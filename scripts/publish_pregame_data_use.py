#!/usr/bin/env python3
"""Explain a frozen daily release and export its source/participation audits."""
import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import digest, verify_manifest_files
from scripts.validate_daily_bundle import validate
from scripts.publish_results_update import page
from src.fantasy.availability import excluded_by_status


def table(frame):
    f = frame.fillna('—').astype(str)
    return '\n'.join(['| ' + ' | '.join(f.columns) + ' |',
                       '| ' + ' | '.join(['---'] * len(f.columns)) + ' |'] +
                      ['| ' + ' | '.join(row) + ' |' for row in f.to_numpy()])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ['bundle', 'team-model', 'original-probabilities', 'benchmark', 'liquidity', 'features', 'fantasy', 'out']:
        ap.add_argument('--' + key, type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise ValueError('Preserve previous reports')
    checks = validate(a.bundle)
    manifests = {key: verify_manifest_files(getattr(a, key), []) for key in
                 ['bundle', 'team_model', 'original_probabilities', 'benchmark', 'liquidity', 'features', 'fantasy']}
    m = manifests['bundle']
    target = m['date']
    direct = pd.read_csv(a.team_model/'team_win_probabilities.csv')
    original = pd.read_csv(a.original_probabilities/'team_win_probabilities.csv')
    quotes = pd.read_csv(a.benchmark/'winner_benchmark.csv')
    liquidity = pd.read_csv(a.liquidity/'winner_liquidity.csv')
    if set(direct.game_id) != set(original.game_id) or set(direct.game_id) != set(quotes.game_id):
        raise ValueError('Comparison game population differs')
    home_quotes = quotes.merge(direct[['game_id', 'home']], on='game_id', validate='many_to_one')
    home_quotes = home_quotes[home_quotes.team.eq(home_quotes.home)]
    comparison = direct[['game_id', 'start_time_utc', 'away', 'home', 'away_goal_mean', 'home_goal_mean', 'home_win_probability']].merge(
        original[['game_id', 'home_win_probability']].rename(columns={'home_win_probability': 'original_home_probability'}),
        on='game_id', validate='one_to_one').merge(
        home_quotes[['game_id', 'ticker', 'yes_bid', 'yes_ask', 'quoted_midpoint', 'sampled_at_utc']],
        on='game_id', validate='one_to_one')
    comparison['start_ET'] = pd.to_datetime(comparison.start_time_utc, utc=True).dt.tz_convert('America/New_York').dt.strftime('%-I:%M %p')
    comparison['model_minus_market_pp'] = 100*(comparison.home_win_probability-comparison.quoted_midpoint)
    players = pd.read_csv(a.bundle/'player_projections.csv')
    players = players[players.model.eq('default')]
    audit = pd.read_csv(a.bundle/'inputs/lineup_audit.csv')
    context = pd.read_csv(a.bundle/'team_context.csv')
    mp = Path(m['moneypuck_snapshot'])
    mpmeta = json.loads((mp/'metadata.json').read_text())
    quality = json.loads((Path(m['moneypuck_shots_source'])/'manifest.json').read_text())
    quality_rows = pd.read_csv(Path(m['moneypuck_shots_source'])/'defense_shot_quality_team_games.csv')
    usable_quality_games = quality_rows.loc[~quality_rows.source_quarantined, 'game_id'].nunique()
    pbp = json.loads((Path(m['defense_pbp_source'])/'manifest.json').read_text())
    pbpmeta = json.loads((Path(pbp['raw_snapshot'])/'metadata.json').read_text())
    toi_path = Path(next(p for p in m['additional_sources'] if 'player_game_toi' in p))
    toimeta = json.loads((toi_path.parent/'manifest.json').read_text())
    reconciled = pd.read_csv(a.team_model/'input_reconciliation.csv')
    xg_bad = reconciled.loc[~reconciled.source_matches, 'game_id'].nunique()
    shot_bad = len({v for ids in context.moneypuck_excluded_current_game_ids.dropna() for v in str(ids).split(';') if v})
    fantasy = json.loads((a.fantasy/'report.json').read_text())
    boxes = json.loads((Path(m['boxscore_history'])/'metadata.json').read_text())
    inputs = json.loads((a.bundle/'inputs/manifest.json').read_text())
    espn = Path(inputs['espn']['snapshot'])
    rows = []
    for (game_id, team), group in audit.groupby(['game_id', 'team']):
        selected = group[group.selected_for_trial.eq(True)]
        rows.append(dict(game_id=game_id, team=team, candidates=len(group), selected=len(selected),
                         injury_excluded=int(group.injury_status.map(excluded_by_status).sum()),
                         selected_not_in_previous_game=int((~selected.played_last_team_game).sum()),
                         selected_nonactive=int(selected.injury_status.ne('ACTIVE').sum()),
                         lineup_confirmed=False))
    participation = pd.DataFrame(rows)
    a.out.mkdir(parents=True)
    comparison.to_csv(a.out/'game_comparison.csv', index=False)
    participation.to_csv(a.out/'participation_summary.csv', index=False)
    # Keep every candidate; exclusions are forecast selection, not data removal.
    audit.to_csv(a.out/'participation_candidates.csv', index=False)
    review_candidates = audit[audit.selected_for_trial.eq(True) & audit.injury_status.ne('ACTIVE')]
    review_candidates.to_csv(a.out/'selected_status_review.csv', index=False)
    context.to_csv(a.out/'moneypuck_team_context.csv', index=False)
    sources = [
        dict(source='Official NHL finals', path=m['boxscore_history'], timestamp=boxes['created_at_utc'],
             use='Observed goals, SOG, participation and schedule history through the preceding day; outcome validation reference.'),
        dict(source='Official NHL TOI', path=str(toi_path),
             timestamp=toimeta['retrieval_completed_at_utc'], use='Recent EV/PP and total TOI history; only validated total-TOI policy is promoted.'),
        dict(source='Official NHL schedule and rosters', path=m['raw_context'],
             timestamp=json.loads((Path(m['raw_context'])/'metadata.json').read_text())['retrieved_at_utc'],
             use='Today game identities/times, roster candidates and prior-game union; not confirmation of dressing.'),
        dict(source='ESPN', path=str(espn), timestamp=m['injuries_as_of_utc'],
             use='Timestamped injuries, ownership, active/bench slots and saved matchup categories; ACTIVE is not confirmation.'),
        dict(source='MoneyPuck team games', path=str(mp), timestamp=mpmeta['retrieved_at_utc'],
             use='Previous-season SOG priors and reconciled lagged 5v5 xOnGoal in usage-shot challenger; lagged xG/xGA in separate direct team model.'),
        dict(source='MoneyPuck unblocked shots', path=m['moneypuck_shots_source'], timestamp=quality['retrieved_at_utc'],
             use='Lagged D xG/rebound/attempt features in separate frozen feature experiment; no change to main player or fantasy means.'),
        dict(source='NHL play-by-play', path=m['defense_pbp_source'], timestamp=pbpmeta.get('retrieved_at_utc', pbpmeta.get('created_at_utc')),
             use='Lagged defense involvement in separate feature trial; quarantined disagreements remain excluded.'),
        dict(source='Kalshi winner quotes', path=str(a.benchmark), timestamp=quotes.sampled_at_utc.min(),
             use='Matched pregame external benchmark for original and fitted team probabilities; no model input or blending.'),
        dict(source='Kalshi depth/trades', path=str(a.liquidity), timestamp=manifests['liquidity']['completed_at_utc'],
             use='Quote quality and recency audit from a later sequential observation; original quote benchmark preserved.')]
    pd.DataFrame(sources).to_csv(a.out/'source_usage.csv', index=False)
    snapshot = Path(manifests['benchmark']['snapshot'])
    markets = pd.read_csv(snapshot/'markets.csv')
    date_token = pd.Timestamp(target).strftime('%y%b%d').upper()
    today_markets = markets[markets.event_ticker.str.contains('-'+date_token, regex=False)]
    requested = json.loads((snapshot/'manifest.json').read_text())['requested_series']
    series = today_markets.groupby('series').agg(contracts=('ticker','size'), two_sided=('two_sided_quote','sum'),
                                              median_volume=('volume','median'), median_spread=('spread','median')).reindex(requested)
    series[['contracts','two_sided']] = series[['contracts','two_sided']].fillna(0).astype(int)
    series.reset_index().to_csv(a.out/'kalshi_today_series.csv', index=False)
    def link(path):
        return os.path.relpath(path, a.out)
    displayed = comparison[['away','home','start_ET','away_goal_mean','home_goal_mean','home_win_probability','original_home_probability','quoted_midpoint','model_minus_market_pp']].copy()
    for c in ['home_win_probability','original_home_probability','quoted_midpoint']:
        displayed[c] = 100*displayed[c]
    displayed = displayed.rename(columns={'home_win_probability':'team_model_home_%', 'original_home_probability':'original_home_%', 'quoted_midpoint':'Kalshi_home_%'})
    displayed = displayed.round(2)
    issued = pd.Timestamp(m['finalized_at_utc']).tz_convert('America/New_York').strftime('%-I:%M %p ET')
    body = f'''# Pregame preparation and data use — {target}

Research question: do the current ice-time, shots and direct team-model policies improve on their frozen baselines on new games, and how do their winner probabilities compare with independently observed pregame market quotes?

## Release

{checks['games']} games issued at {issued}; {len(players)} candidate skaters across five models and {checks['goalie_rows']//2} goalie candidates across two models. All games passed strict pregame, freshness, coverage, finite-value, source-hash and count-identity checks. Official history covers {boxes['final_games']} final games through {boxes['through_eastern_date']}. No missing historical forecast dates are reconstructed.

[Game outlook](../../../docs/games/index.html) · [Fantasy report]({link(a.fantasy/'index.html')}) · [Direct team model]({link(a.team_model/'README.md')}) · [Frozen feature trial]({link(a.features/'README.md')})

## How today's data is used

- **MoneyPuck team games:** {mpmeta['current_games']} current-season games downloaded. Previous-season SOG supplies team priors; lagged 5v5 xOnGoal supplies the usage-shot context challenger. The original opponent-shot factor remains based on NHL SOG. Today's main-context audit excludes {shot_bad} distinct games involving today's teams from MoneyPuck chance features because of source discrepancies. Previous-season priors are not reconciled game by game against current-season NHL snapshots.
- **Separate direct team model:** uses lagged MoneyPuck xG/xGA alongside official goals, home ice and rest. {boxes['final_games']-xg_bad}/{boxes['final_games']} current games pass its goals/SOG reconciliation; {xg_bad} games are excluded from xG updates while their official goals and schedule remain. Coefficients stay frozen through {direct.training_through.iloc[0]}; fresh features end before today. Team goals are not redistributed into player forecasts.
- **MoneyPuck shot file:** {quality['rows']:,} raw events, {quality['eligible_games']} official games represented, {len(quality['quarantined_games'])} games quarantined and {usable_quality_games} usable. Missing official games: {len(quality['missing_official_games'])}. Lagged defense shot quality and expected rebounds enter the separate four-variant feature trial using the October 20 coefficients. These do not change the five main player models.
- **Fantasy:** the adopted policy uses usage-based TOI only; shots and other categories keep the default. Neither new MoneyPuck xG nor Kalshi prices change fantasy goal/shot means. Saved active/bench labels and category scores come from refreshed ESPN data.
- **Kalshi:** {len(quotes)} winner contracts mapped to all {quotes.game_id.nunique()} games by exact date, team aliases and fixture identity, with rules and pregame timestamps retained. Median bid/ask spread is ${quotes.spread.median():.2f}. Quotes benchmark both probability models; they do not train or adjust either model. Player props/totals are preserved for coverage inspection only and have not been mapped or validated as forecasting features.

Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Whole target-date outcomes are excluded from every forecasting feature. Downloaded xG may contain retrospective source corrections; it is not an archived historical as-of score.

## Today's games and market comparison

Goal means belong to the separate fitted team model. All probability columns refer to the home team; differences are percentage points, not betting edges. Quoted midpoints are not calibrated or guaranteed executable probabilities. Model and market observation times differ.

{table(displayed)}

[Full comparison and timestamps](game_comparison.csv) · [Contract rules and original bid/ask quotes]({link(a.benchmark/'winner_benchmark.csv')}) · [Depth and trade recency]({link(a.liquidity/'winner_liquidity.csv')})

Depth was available for {liquidity.depth_status.eq('available').sum()}/{len(liquidity)} contracts. Trade pagination completed for {liquidity.trade_pagination_complete.sum()}/{len(liquidity)}. Median age of most recent available live-API trade at the later observation: {liquidity.last_trade_age_minutes.median():.1f} minutes. Depth, trades and original quotes are separate sequential observations. A recent trade does not establish sufficient liquidity for an arbitrary order size.

### Today's broader Kalshi coverage

Date-filtered contract counts below are discovery counts; only winner contracts have verified NHL mappings and rules for today's benchmark. Zero-volume or absent markets are not imputed.

{table(series.reset_index().round(3))}

## Participation and fantasy status

Preserved official roster candidates, last-game participation and timestamped ESPN injury labels for every candidate. No lineup-selection replacement or fitted participation probability was promoted. Conditional player means assume dressing; goalie means assume a full start. No starter is certified by these inputs.

[Every candidate and selection reason](participation_candidates.csv) · [Team participation audit](participation_summary.csv) · [MoneyPuck coverage by team](moneypuck_team_context.csv)

{len(review_candidates)} selected candidates have a non-ACTIVE label: {review_candidates.injury_status.value_counts().to_dict()}. [Review names and statuses](selected_status_review.csv). These labels require follow-up; ACTIVE itself also does not confirm dressing. Official roster and ESPN snapshots are morning observations, not evening lineup confirmations.

{chr(10).join('- '+action for action in fantasy['actions'])}

## Next prospective checks

Preserve this morning release. Before evening puck drop, acquire a new timestamped roster/injury/starter and market observation; any new forecast must be issued separately before the ten-minute cutoff. After finals, score the frozen player, fantasy TOI, goalie, direct-team and feature releases separately, and compare each probability model with the same home-side Kalshi benchmark on matched completed games. Exclude void/cancelled/fair-price contract resolutions from ordinary winner scoring. No model promotion, coefficient tuning, lineup transactions or market trades occurred in this preparation.

[Source paths, timestamps and usage](source_usage.csv) · [Report manifest](manifest.json)
'''
    (a.out/'README.md').write_text(body)
    html = (f'<p><a href="{link(Path("docs/games/index.html"))}">Game outlook</a> · '
            f'<a href="{link(a.fantasy/"index.html")}">Fantasy</a> · '
            f'<a href="{link(a.team_model/"index.html")}">Team model</a></p>')
    html += '<p>All '+str(checks['games'])+' games frozen pregame. MoneyPuck supplies lagged experimental context; Kalshi is an independent benchmark.</p>'
    html += '<p><a href="README.md">Full source-use report, limitations and next checks</a> · <a href="game_comparison.csv">Download comparison</a></p>'
    html += '<main>'+displayed.to_html(index=False)+'</main><h2>Saved fantasy actions</h2><ul>'+''.join('<li>'+escape(action)+'</li>' for action in fantasy['actions'])+'</ul>'
    (a.out/'index.html').write_text(page('Pregame data use — '+target, html))
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), date=target,
                    source_manifests={str(getattr(a,key)/'manifest.json'): digest(getattr(a,key)/'manifest.json') for key in manifests},
                    validation=checks, files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()})
    (a.out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('Pregame data-use report:', a.out)
    print(displayed.to_string(index=False))
    print('Fantasy actions:', json.dumps(fantasy['actions']))


if __name__ == '__main__':
    main()
