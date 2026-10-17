#!/usr/bin/env python3
"""Publish all-game reading views from an existing frozen daily forecast bundle."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.fantasy.game_outlook import game_outlooks
from scripts.validate_daily_bundle import validate


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=Path('docs/games'))
    args=parser.parse_args();validate(args.bundle)
    manifest=json.loads((args.bundle/'manifest.json').read_text())
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
    payload=dict(date=manifest['date'],forecast_issued_utc=manifest['created_at_utc'],
        forecast_issued_local=pd.Timestamp(manifest['created_at_utc']).tz_convert('America/New_York').strftime('%b %-d, %-I:%M %p ET'),
        view_created_utc=created.isoformat(),pregame_games=pregame,total_games=len(games),
        models=manifest['config']['models'],games=outlook,
        goalies=json.loads(goalie.to_json(orient='records')),leaders=json.loads(leaders.to_json(orient='records')),
        limitations=[
            'Projected goals are sums of player scoring means in an unconfirmed lineup scenario, not MoneyPuck shot-quality xG.',
            'The scoring lean is the side with the higher mean. It is not a calibrated winner prediction, betting edge or win probability.',
            'Goal totals do not yet have a fitted opponent, home/rest or opposing-goalie adjustment. Shot challengers apply experimental context; selecting a new model may change shots without changing goals.',
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
    (args.out/'index.html').write_text(template.replace('__OUTLOOK_DATA__',json.dumps(payload,separators=(',',':'),allow_nan=False).replace('</','<\\/')))
    (args.out/'manifest.json').write_text(json.dumps(dict(date=manifest['date'],view_created_utc=created.isoformat(),
        forecast_issued_utc=manifest['created_at_utc'],frozen_bundle_manifest_sha256=digest(args.bundle/'manifest.json'),
        source_schedule_sha256=digest(schedule_path),model_status='existing_frozen_models_no_refit_or_promotion',
        code_sha256={p.name:digest(p) for p in [Path(__file__),ROOT/'src/fantasy/game_outlook.py',ROOT/'templates/nhl_outlook.html']},
        files={p.name:digest(p) for p in args.out.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    (args.out/'README.md').write_text(f'''# NHL game outlook — {manifest['date']}

[Interactive matchups](index.html) · [Game predictions CSV](game_predictions.csv)

There are {len(games)} games: {pregame} pregame forecasts and {len(games)-pregame} late-issued.
The goal numbers are projected means, not exact final scores. The side with the
higher goal mean is the model scoring lean; no calibrated win odds are supplied.
Simulation ranges and goalie start shares remain provisional. All five saved
models can be compared without changing the frozen forecasts.

Start by comparing each matchup's goal means and shot volume. Expand a card for
assumed shot leaders and goalie full-start scenarios. Use the table to scan all
teams. NJD–WSH is excluded by default because its forecasts were issued late.

The page is a saved snapshot and does not update live. See the page's assumptions
and manifest for limitations and source hashes.
''')
    print('NHL outlook:',args.out/'index.html')
    print('Official games:',len(games),'Pregame:',pregame,'Late:',len(games)-pregame)


if __name__=='__main__':main()
