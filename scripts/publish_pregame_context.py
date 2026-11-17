#!/usr/bin/env python3
"""Publish lineup changes and public NHL context for the last saved fantasy roster."""
import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.snapshot_nhl_lineups import normalized_name
from scripts.evaluate_daily_forecasts import verify_manifest_files
from scripts.publish_results_update import page
from scripts.validate_daily_bundle import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['bundle', 'lineups', 'team-probabilities', 'benchmark', 'fantasy-report', 'out']:
        parser.add_argument('--' + key, required=True, type=Path)
    args = parser.parse_args()
    validate(args.bundle)
    bundle = json.loads((args.bundle/'manifest.json').read_text())
    for folder in [args.lineups, args.team_probabilities, args.benchmark]:
        verify_manifest_files(folder, [])
    lineup = pd.read_csv(args.lineups/'projected_lineups.csv')
    coverage = pd.read_csv(args.lineups/'coverage.csv')
    audit = pd.read_csv(args.bundle/'inputs/lineup_audit.csv')
    changes = audit[audit.selected_for_trial.ne(audit.heuristic_selected_for_trial)].copy()
    changes['change'] = changes.selected_for_trial.map({True:'added to scenario', False:'removed from scenario'})
    coverage = coverage.merge(audit.groupby(['game_id','team']).published_lineup_applied.all().reset_index(),
                              on=['game_id','team'], how='left', validate='one_to_one')
    teams = pd.read_csv(args.team_probabilities/'team_win_probabilities.csv')
    quotes = pd.read_csv(args.benchmark/'winner_benchmark.csv')
    home_quotes = quotes.merge(teams[['game_id','home']], on='game_id').query('team == home')
    comparison = teams[['game_id','away','home','away_goal_mean','home_goal_mean','home_win_probability']].merge(
        home_quotes[['game_id','quoted_midpoint','spread','sampled_at_utc']], on='game_id', validate='one_to_one')
    comparison['model_minus_market_percentage_points'] = 100*(comparison.home_win_probability-comparison.quoted_midpoint)

    # Ownership and slots retain their original date. Today's NHL facts are joined by official identity.
    fantasy_manifest = json.loads((args.fantasy_report/'manifest.json').read_text())
    roster_path = args.fantasy_report/'roster.csv'
    if hashlib.sha256(roster_path.read_bytes()).hexdigest() != fantasy_manifest['files']['roster.csv']:
        raise ValueError('Changed saved fantasy roster')
    roster = pd.read_csv(roster_path)
    identities = {}
    raw = Path(bundle['raw_context'])
    for path in raw.glob('roster_*.json'):
        team = path.stem.removeprefix('roster_')
        for group in json.loads(path.read_text()).values():
            if not isinstance(group, list):
                continue
            for player in group:
                name = player['firstName']['default']+' '+player['lastName']['default']
                identities.setdefault(normalized_name(name), []).append((player['id'],team))
    predictions = pd.read_csv(args.bundle/'player_projections.csv')
    policy = json.loads(Path('config/fantasy_category_policy.json').read_text())
    fantasy_rows = []
    for row in roster.itertuples():
        matches = identities.get(normalized_name(row.player_name), [])
        record = dict(player_name=row.player_name, saved_lineup_slot=row.lineup_slot,
                      fantasy_roster_date=fantasy_manifest['date'], fantasy_roster_status='current_ownership_and_slots_unverified',
                      team=None, player_id=None, tonight_status='not_matched_to_tonights_official_rosters', start_time_utc=None)
        if len(matches) == 1:
            player_id, team = matches[0]
            fixture = teams[teams.home.eq(team) | teams.away.eq(team)].iloc[0]
            reported = lineup[lineup.player_id.eq(player_id) & lineup.team.eq(team)]
            record.update(player_id=player_id,team=team,start_time_utc=fixture.start_time_utc,
                          tonight_status=reported.iloc[0].projected_status if len(reported)==1 else 'official_roster_participation_unconfirmed')
            for category in ['goals','assists','shots','pp_points','toi_minutes','hits','penalty_minutes','plus_minus']:
                model = policy['category_models'].get(category, policy['baseline'])
                selected = predictions[predictions.player_id.eq(player_id) & predictions.model.eq(model)]
                record['expected_'+category+'_if_plays'] = selected.iloc[0]['expected_'+category+'_if_plays'] if len(selected)==1 else None
        fantasy_rows.append(record)
    fantasy = pd.DataFrame(fantasy_rows)
    args.out.mkdir(parents=True, exist_ok=True)
    files = {'lineup_coverage.csv': coverage, 'projected_lineups.csv':lineup,
             'lineup_selection_changes.csv': changes[['game_id','team','player_id','player_name','change','selection_reason']],
             'model_market_comparison.csv': comparison, 'fantasy_roster_context.csv':fantasy}
    for name, frame in files.items():
        frame.to_csv(args.out/name,index=False)
    count = int(coverage.published_lineup_applied.fillna(False).sum())
    text = (f"# Pregame update — {bundle['date']}\n\n"
            f"All {len(teams)} games have frozen pregame team, skater and goalie projections. Official statistics cover through November 16. "
            f"MoneyPuck team data also cover through November 16. Kalshi quotes map to {len(quotes)} team contracts.\n\n"
            f"Published NHL projected lineups were applied for {count} of {len(coverage)} teams, changing {len(changes)} player selections. "
            "Incomplete or unresolved lists retain the prior-game lineup heuristic and are identified in lineup_coverage.csv. "
            "Projected lineup changes affect player-sum team scenarios. The direct team win model continues to use team history, home/rest and lagged xG. "
            "Goalie rows carry published projected status where available. Their start shares remain uncalibrated historical scenarios.\n\n"
            f"Fantasy ownership and lineup slots come from the saved {fantasy_manifest['date']} roster. "
            "ESPN requires authenticated access, which is unavailable in this workspace. Today's public NHL context and category projections are shown for those saved players. "
            "Current fantasy ownership, active slots, locks and matchup totals remain unverified.\n\n"
            "The existing NHL calibrated-opponent shots and isolated usage-only TOI selections remain supported by the November review. "
            "On November 16's two games, direct-team Brier was 0.3619 versus 0.3172 for the goal-history baseline. "
            "The two-game comparison provides insufficient evidence for a refit. New lineup selection is an operational scenario update whose prospective accuracy still needs evaluation.\n\n"
            "[Team forecasts](../../team-model/) · [Player and goalie outlook](../../games/) · "
            "[Fantasy roster context](fantasy_roster_context.csv) · [Lineup changes](lineup_selection_changes.csv) · "
            "[Model and market comparison](model_market_comparison.csv)\n")
    (args.out/'README.md').write_text(text)
    body = ''.join('<p>'+escape(paragraph)+'</p>' for paragraph in text.split('\n\n')[1:-1])
    body += '<p><a href="../../team-model/">Team probabilities</a> · <a href="../../games/">Player and goalie outlook</a></p>'
    for title, frame in [('Team model and Kalshi', comparison.drop(columns=['game_id'])),
                         ('Lineup coverage', coverage[['team','status','published_lineup_applied']]),
                         ('Lineup changes', files['lineup_selection_changes.csv'][['team','player_name','change']]),
                         ('Last saved fantasy roster with tonight’s NHL context',fantasy[['player_name','saved_lineup_slot','team','tonight_status','expected_shots_if_plays','expected_toi_minutes_if_plays']])]:
        body += '<h2>'+escape(title)+'</h2>'+frame.round(3).fillna('—').to_html(index=False,escape=True)
    body += '<p>Projected-lineup sources</p><ul>'+''.join('<li><a href="'+escape(url,quote=True)+'">'+escape(url.rsplit('/',1)[-1])+'</a></li>' for url in sorted(set(lineup.source_url)))+'</ul>'
    (args.out/'index.html').write_text(page('Pregame update — '+bundle['date'],body))
    manifest = dict(date=bundle['date'],created_at_utc=datetime.now(timezone.utc).isoformat(),fantasy_roster_date=fantasy_manifest['date'],
                    published_lineups_applied=count,lineup_selection_changes=len(changes),
                    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.iterdir() if p.is_file() and p.name!='manifest.json'})
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Published context:',args.out,'Applied teams:',count,'Changed selections:',len(changes))


if __name__ == '__main__':
    main()
