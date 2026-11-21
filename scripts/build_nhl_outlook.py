#!/usr/bin/env python3
"""Publish all-game reading views from an existing frozen daily forecast bundle."""
import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.fantasy.game_outlook import game_outlooks
from src.fantasy.per_game import require
from scripts.validate_daily_bundle import validate


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=Path('docs/games'))
    parser.add_argument('--model-review',type=Path,
        help='Optional hash-checked November review directory to summarize on the game page')
    parser.add_argument('--kalshi-benchmark',type=Path,
        help='Optional hash-checked, exact-fixture Kalshi winner quote benchmark; never used as a model input')
    args=parser.parse_args();validate(args.bundle)
    manifest=json.loads((args.bundle/'manifest.json').read_text())
    current_config=json.loads((ROOT/'config/daily_forecast_trial.json').read_text())
    # Selection belongs to the frozen issue, not whichever config is current
    # when a historical reading page is rebuilt.
    trial_config=manifest.get('config') or current_config
    primary_sog_model=trial_config.get('primary_sog_model','default')
    primary_toi_model=(trial_config.get('primary_toi_model','default')
        if manifest['date'] >= trial_config.get('primary_toi_effective_from','9999-12-31') else 'default')
    if primary_sog_model not in manifest['config']['models']:
        raise ValueError(f'Primary SOG model {primary_sog_model!r} is not in the frozen bundle')
    if primary_toi_model not in manifest['config']['models']:
        raise ValueError(f'Primary TOI model {primary_toi_model!r} is not in the frozen bundle')
    schedule_path=Path(manifest['raw_context'])/'schedule.json'
    schedule_source=next(r for r in manifest['sources'] if r['file']=='schedule.json')
    if digest(schedule_path)!=schedule_source['sha256']:raise ValueError('Schedule source hash mismatch')
    week=json.loads(schedule_path.read_text())['gameWeek']
    games=[g for d in week if d['date']==manifest['date'] for g in d['games'] if g['season']==20262027 and g['gameType']==2]
    team=pd.read_csv(args.bundle/'team_projections.csv')
    distributions=pd.read_csv(args.bundle/'team_projected_vs_actual.csv')
    for category in ['goals','shots']:
        part=distributions[distributions.category.eq(category)][['game_id','team','model','simulation_p10','simulation_p90']]
        part=part.rename(columns={f'simulation_p{p}':f'{category}_p{p}' for p in [10,90]})
        team=team.merge(part,on=['game_id','team','model'],validate='one_to_one')
    outlook=game_outlooks(json.loads(team.to_json(orient='records')),games)
    goalie=pd.read_csv(args.bundle/'goalie_projections.csv')
    fields=['game_id','team','player_name','model','injury_status','excluded_from_start_scenario',
        'start_share_provisional','starter_status','saves_if_full_start','goals_against_if_full_start','save_percentage_projection','issue_timing']
    fields += [column for column in ['reported_lineup_status','reported_lineup_source'] if column in goalie]
    goalie=goalie[fields]
    players=pd.read_csv(args.bundle/'player_projections.csv')
    players=players[players.selected_for_trial.eq(True)]
    player_fields=['game_id','team','player_name','model','injury_status','expected_goals_if_plays','expected_shots_if_plays','expected_assists_if_plays']
    # Show just the shot leaders in each saved lineup scenario, not a second ranking model.
    leaders=players.sort_values('expected_shots_if_plays',ascending=False).groupby(['game_id','team','model']).head(3)[player_fields]
    created=datetime.now(timezone.utc)
    for row in outlook:
        row['start_local']=pd.Timestamp(row['start_time_utc']).tz_convert('America/New_York').strftime('%-I:%M %p ET')
    pregame=len({r['game_id'] for r in outlook if r['issue_timing']=='pregame'})
    model_order=[primary_sog_model]+[m for m in manifest['config']['models'] if m!=primary_sog_model]
    payload=dict(date=manifest['date'],forecast_issued_utc=manifest['created_at_utc'],
        forecast_issued_local=pd.Timestamp(manifest['created_at_utc']).tz_convert('America/New_York').strftime('%b %-d, %-I:%M %p ET'),
        view_created_utc=created.isoformat(),pregame_games=pregame,total_games=len(games),
        primary_sog_model=primary_sog_model,primary_toi_model=primary_toi_model,
        models=model_order,games=outlook,
        goalies=json.loads(goalie.to_json(orient='records')),leaders=json.loads(leaders.to_json(orient='records')),
        limitations=[
            'Projected goals are sums of player scoring means in an unconfirmed lineup scenario, not MoneyPuck shot-quality xG.',
            'The scoring lean is the side with the higher mean. It is not a calibrated winner prediction, betting edge or win probability.',
            'Goal totals do not yet have a fitted opponent, home/rest or opposing-goalie adjustment. Shot challengers apply experimental context; selecting a new model may change shots without changing goals.',
            f'{primary_sog_model} is selected for NHL-wide player shots and {primary_toi_model} for conditional ATOI; fantasy category policies remain separate.',
            'Goalie numbers are separate full-60-minute scenarios, not confirmed starters. They are not reconciled with the skater team-goal forecasts.',
            'p10–p90 simulation ranges are provisional Poisson count ranges, not calibrated 80% confidence intervals. Outcomes can fall outside them.',
            'This is a saved forecast, not live scores or an update after puck drop. Late-issued games are excluded by default and must not be scored as prospective predictions.'
        ])
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'outlook.json').write_text(json.dumps(payload,separators=(',',':'),allow_nan=False)+'\n')
    pd.DataFrame(outlook).to_csv(args.out/'game_predictions.csv',index=False)
    team.to_csv(args.out/'team_predictions.csv',index=False)
    goalie.to_csv(args.out/'goalie_scenarios.csv',index=False)
    template=(ROOT/'templates/nhl_outlook.html').read_text()
    evidence_html=''
    review_hash=None
    review_summary=None
    if args.model_review:
        review_manifest=json.loads((args.model_review/'manifest.json').read_text())
        for name, expected in review_manifest.get('files', {}).items():
            if digest(args.model_review/name) != expected:
                raise ValueError(f'Model-review hash mismatch: {name}')
        review_summary=json.loads((args.model_review/'summary.json').read_text())
        if review_summary['through'] >= manifest['date']:
            raise ValueError('Model review includes outcomes on or after today’s forecast date')
        review_hash=digest(args.model_review/'manifest.json')
        b=review_summary['selected_shots_paired_game_bootstrap']
        url='../history/'+args.model_review.name+'/index.html'
        evidence_html=(
            '<section class="guide"><h2>Model evidence for today’s release</h2>'
            f'<p>Across {review_summary["prospective_games"]} saved November games and '
            f'{review_summary["player_games"]:,} matched player-games, calibrated-opponent shots had '
            f'{review_summary["selected_shots_mae"]:.3f} MAE versus '
            f'{review_summary["default_shots_mae"]:.3f} for default '
            f'({review_summary["selected_shots_relative_improvement_pct"]:.1f}% lower; '
            f'{b["games_lower_mae"]}/{b["games"]} games lower; game-cluster 95% interval '
            f'[{b["lower_95"]:+.3f}, {b["upper_95"]:+.3f}]). It remains selected for NHL-wide SOG. '
            'Fantasy shots keep their separate default policy.</p>'
            f'<p>The isolated usage-only ATOI model reduced conditional ice-time MAE from '
            f'{review_summary["default_toi_mae"]:.3f} to {review_summary["isolated_usage_toi_mae"]:.3f} minutes '
            f'across {review_summary["isolated_usage_toi_games"]} prospective games '
            f'({review_summary["isolated_usage_toi_paired_game_bootstrap"]["games_lower_mae"]}/'
            f'{review_summary["isolated_usage_toi_paired_game_bootstrap"]["games"]} games lower; paired '
            f'95% interval [{review_summary["isolated_usage_toi_paired_game_bootstrap"]["lower_95"]:+.3f}, '
            f'{review_summary["isolated_usage_toi_paired_game_bootstrap"]["upper_95"]:+.3f}]). '
            f'{"It is selected for future conditional ATOI projections." if primary_toi_model == "usage_toi_only_trial" else "It supports promoting usage-only ATOI for future releases."} '
            'Assist and team-probability results do not support another policy change.</p>'
            f'<p><a href="{escape(url, quote=True)}">Full November model review and scored files</a></p></section>')
    kalshi_html=''
    kalshi_hash=None
    kalshi_meta=None
    if args.kalshi_benchmark:
        km=json.loads((args.kalshi_benchmark/'manifest.json').read_text())
        for name,expected in km.get('files',{}).items():
            if digest(args.kalshi_benchmark/name)!=expected:
                raise ValueError(f'Kalshi benchmark hash mismatch: {name}')
        require(km.get('market_status')=='read_only_benchmark_not_model_input',
                'Kalshi benchmark must be labeled read-only and not a model input')
        snapshot=Path(km['snapshot']); snapshot_manifest=snapshot/'manifest.json'
        require(digest(snapshot_manifest)==km['snapshot_sha256'],'Kalshi snapshot manifest hash mismatch')
        probability_dir=Path(km['probabilities'])
        probability_manifest=probability_dir/'manifest.json'
        require(digest(probability_manifest)==km['probabilities_sha256'],
                'Kalshi benchmark probability release hash mismatch')
        issue_manifest=json.loads(probability_manifest.read_text())
        if 'team_win_probabilities.csv' in issue_manifest.get('files',{}):
            require(digest(probability_dir/'team_win_probabilities.csv')==
                    issue_manifest['files']['team_win_probabilities.csv'],
                    'Changed direct-team probability source')
        quotes=pd.read_csv(args.kalshi_benchmark/'winner_benchmark.csv')
        require(set(quotes.game_id)=={g['id'] for g in games},
                'Kalshi benchmark game coverage differs from today’s official slate')
        require(not quotes.duplicated(['game_id','team']).any(),
                'Duplicate Kalshi game/team quote')
        require(quotes.groupby('game_id').team.nunique().eq(2).all() and
                quotes.groupby('game_id').size().eq(2).all(),
                'Kalshi benchmark must have one contract for both teams in every game')
        require(quotes.two_sided_quote.eq(True).all(), 'Kalshi benchmark contains a one-sided quote')
        quote_at=pd.to_datetime(quotes.sampled_at_utc,utc=True)
        starts=pd.to_datetime(quotes.start_time_utc,utc=True)
        issued=pd.to_datetime(quotes.model_issued_at_utc,utc=True)
        require((quote_at<starts).all(), 'Kalshi quote was sampled after puck drop')
        require(quotes.model_probability.between(0,1).all() and
                quotes.quoted_midpoint.between(0,1).all(), 'Invalid Kalshi/model probability')
        direct=pd.read_csv(probability_dir/'team_win_probabilities.csv')
        direct_map={(int(r.game_id),r.home):r.home_win_probability for r in direct.itertuples()}
        direct_map.update({(int(r.game_id),r.away):r.away_win_probability for r in direct.itertuples()})
        for r in quotes.itertuples():
            require((int(r.game_id),r.team) in direct_map and
                    abs(float(r.model_probability)-float(direct_map[(int(r.game_id),r.team)]))<1e-10,
                    'Kalshi benchmark probabilities do not match their frozen direct-team release')
        delay=(quote_at-issued).dt.total_seconds()/60
        lead=(starts-quote_at).dt.total_seconds()/60
        view=quotes[['game_id','team','ticker','sampled_at_utc','model_probability',
                     'yes_bid','yes_ask','quoted_midpoint','market_minus_model_pp','spread']].copy()
        view['model_probability']=view.model_probability.map(lambda x:f'{x:.1%}')
        for column in ['yes_bid','yes_ask','quoted_midpoint','spread']:
            view[column]=view[column].map(lambda x:f'{x:.3f}')
        view['market_minus_model_pp']=view.market_minus_model_pp.map(lambda x:f'{x:+.1f} pp')
        table=view.to_html(index=False,border=0,classes='data',escape=True)
        url='../history/'+args.kalshi_benchmark.name+'/index.html'
        kalshi_html=(
            '<section class="guide"><h2>Kalshi winner market comparison</h2>'
            f'<p>Mapped {len(quotes)} two-sided team quotes across {quotes.game_id.nunique()} games. '
            f'The quotes were sampled a median of {delay.median():.1f} minutes after the direct-team forecast '
            f'was issued and at least {lead.min():.1f} minutes before puck drop. '
            'Market-minus-model is the YES midpoint less the raw direct-team probability, in percentage points. '
            'Prices are shown as quoted: they are not de-vigged, calibrated probabilities, executable prices, '
            'or forecast inputs. This comparison does not blend or change the selected model.</p>'
            f'<div class="scroll">{table}</div>'
            f'<p><a href="{escape(url, quote=True)}">Full Kalshi benchmark, contract rules, source times and hashes</a></p></section>')
        kalshi_hash=digest(args.kalshi_benchmark/'manifest.json')
        kalshi_meta=dict(games=int(quotes.game_id.nunique()),contracts=len(quotes),
            median_minutes_after_model_issue=float(delay.median()),
            minimum_minutes_before_game=float(lead.min()),median_spread=float(quotes.spread.median()),
            market_status='read_only_benchmark_not_model_input')
    template=template.replace('__MODEL_EVIDENCE__',evidence_html)
    template=template.replace('__KALSHI_BENCHMARK__',kalshi_html)
    (args.out/'index.html').write_text(template.replace('__OUTLOOK_DATA__',json.dumps(payload,separators=(',',':'),allow_nan=False).replace('</','<\\/')))
    (args.out/'README.md').write_text(f'''# NHL game outlook — {manifest['date']}

[Interactive matchups](index.html) · [Game predictions CSV](game_predictions.csv)

There are {len(games)} games: {pregame} pregame forecasts and {len(games)-pregame} late-issued.
The goal numbers are projected means, not exact final scores. The side with the
higher goal mean is the model scoring lean; no calibrated win odds are supplied.
Simulation ranges and goalie start shares remain provisional. All saved
models can be compared without changing the frozen forecasts. Selected models
are {primary_sog_model} for all-player SOG and {primary_toi_model} for
conditional ATOI; fantasy category selection remains separate.
{'This page also summarizes the November model review and links the scored evidence.' if review_summary else ''}
{'Kalshi winner prices are shown as a separate read-only benchmark; they were sampled after the direct-team forecast was issued and were not model inputs. See the [mapped market report](../history/'+args.kalshi_benchmark.name+'/README.md).' if kalshi_meta else ''}

Start by comparing each matchup's goal means and shot volume. Expand a card for
assumed shot leaders and goalie full-start scenarios. Use the table to scan all
teams. Any late-issued games are excluded by default.

The page is a saved snapshot and does not update live. Selected models are {primary_sog_model} for all-player SOG and {primary_toi_model} for conditional ATOI; the frozen forecast itself is not changed by this reading view. See the page's assumptions
and manifest for limitations and source hashes.
''')
    (args.out/'manifest.json').write_text(json.dumps(dict(date=manifest['date'],view_created_utc=created.isoformat(),
        forecast_issued_utc=manifest['created_at_utc'],frozen_bundle_manifest_sha256=digest(args.bundle/'manifest.json'),
        source_schedule_sha256=digest(schedule_path),model_status='frozen_all_player_sog_and_conditional_toi_selections',
        primary_sog_model=primary_sog_model,primary_toi_model=primary_toi_model,
        model_review_manifest_sha256=review_hash,
        kalshi_benchmark_manifest_sha256=kalshi_hash,kalshi_benchmark=kalshi_meta,
        code_sha256={str(p.resolve().relative_to(ROOT)):digest(p) for p in [Path(__file__),
            ROOT/'src/fantasy/game_outlook.py',ROOT/'src/fantasy/model_policy.py',
            ROOT/'scripts/validate_daily_bundle.py',ROOT/'templates/nhl_outlook.html',
            ROOT/'config/daily_forecast_trial.json',ROOT/'config/team_goal_model_active.json']+
            ([ROOT/'scripts/map_kalshi_winner_benchmark.py'] if args.kalshi_benchmark else [])},
        files={p.name:digest(p) for p in args.out.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    print('NHL outlook:',args.out/'index.html')
    print('Official games:',len(games),'Pregame:',pregame,'Late:',len(games)-pregame)


if __name__=='__main__':main()
