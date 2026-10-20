#!/usr/bin/env python3
"""Build a local, category-aware decision report from immutable input snapshots."""
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
from src.fantasy.decisions import active_slots, category_rules, fit_lineup, dominates, acquisition_window_open, category_comparison
from src.fantasy.availability import excluded_by_status
from src.fantasy.schedule import normalize_team, LEGACY_TEAM_ALIASES
from scripts.validate_daily_bundle import validate


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def records(frame):
    return json.loads(frame.to_json(orient='records'))


def read_verified(snapshot, filename):
    metadata=json.loads((snapshot/'metadata.json').read_text())
    expected=metadata['files'][filename]
    if isinstance(expected,dict):expected=expected['sha256']
    if sha(snapshot/filename)!=expected:raise ValueError(f'Input hash mismatch: {filename}')
    return pd.read_csv(snapshot/filename)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--rules',required=True,type=Path)
    parser.add_argument('--future-roster',type=Path)
    parser.add_argument('--team-id',type=int,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    validate(args.bundle)
    m=json.loads((args.bundle/'manifest.json').read_text())
    fm=json.loads((args.bundle/'inputs/manifest.json').read_text())
    if fm['espn'].get('status')=='disabled_public_data_only':raise ValueError('League-aware inputs required')
    snapshot=Path(fm['espn']['snapshot'])
    rules_path=args.rules/'rules.json'
    rm=json.loads((args.rules/'metadata.json').read_text())
    if sha(rules_path)!=rm['files']['rules.json']:raise ValueError('Rules hash mismatch')
    rules=json.loads(rules_path.read_text());cats=category_rules(rules);caps=active_slots(rules)
    if rules['rosterSettings']['lineupLocktimeType']!='INDIVIDUAL_GAME':raise ValueError('Unsupported lineup lock rule')
    if rules['league_id']!=json.loads((snapshot/'metadata.json').read_text())['league_id']:raise ValueError('League mismatch')
    now=datetime.now(timezone.utc)
    if now.astimezone(ZoneInfo('America/New_York')).date().isoformat()!=m['date']:
        raise ValueError('Today report requires a bundle for the current Eastern date')
    age=(now-datetime.fromisoformat(m['injuries_as_of_utc'])).total_seconds()/3600
    if not 0<=age<=6:raise ValueError('Refresh ownership/injuries before building today report')
    roster=read_verified(snapshot,'rosters.csv');available=read_verified(snapshot,'available_players.csv')
    matches=read_verified(snapshot,'matchup_categories.csv');teams=read_verified(snapshot,'teams.csv')
    team=teams[teams.team_id.eq(args.team_id)]
    if len(team)!=1:raise ValueError('Unknown team')
    name=team.team_name.iloc[0]
    crosswalk_path=Path('data/processed/espn')/snapshot.name/'espn_nhl_crosswalk.csv'
    meta=json.loads((snapshot/'metadata.json').read_text());key=str(crosswalk_path)
    if sha(crosswalk_path)!=meta['files'][key]['sha256']:raise ValueError('Crosswalk hash mismatch')
    cw=pd.read_csv(crosswalk_path)
    cw=cw[cw.match_status.eq('matched')][['espn_player_id','nhl_player_id']]
    if cw.espn_player_id.duplicated().any():raise ValueError('Duplicate crosswalk')
    projections=pd.read_csv(args.bundle/'player_projections.csv');projections=projections[projections.model.eq('default')]
    projections=projections.drop(columns=['player_name','fantasy_team_name','injury_status'])
    history_path=args.bundle/'inputs/current_per_game_forecast.csv'
    if sha(history_path)!=fm['files']['current_per_game_forecast.csv']:raise ValueError('Player history hash mismatch')
    exposure=pd.read_csv(history_path)[['player_id','historical_gp']]
    projections=projections.merge(exposure,on='player_id',how='left',validate='one_to_one')
    own=roster[roster.fantasy_team_id.eq(args.team_id)].merge(cw,on='espn_player_id',how='left',validate='one_to_one')
    own=own.merge(projections,left_on='nhl_player_id',right_on='player_id',how='left',validate='one_to_one')
    raw_schedule=Path(m['raw_context'])/'schedule.json'
    schedule_source=next(s for s in m['sources'] if s['file']=='schedule.json')
    if sha(raw_schedule)!=schedule_source['sha256']:raise ValueError('Schedule hash mismatch')
    week=json.loads(raw_schedule.read_text())['gameWeek']
    aliases={};fixtures={};calendar=[]
    for day in week:
        for g in day['games']:
            if g['season']!=20262027 or g['gameType']!=2:continue
            for side,other in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
                t=g[side];abbr=t['abbrev'];long=t.get('placeName',{}).get('default','')+' '+t.get('commonName',{}).get('default','')
                aliases[normalize_team(long)]=abbr;aliases[normalize_team(abbr)]=abbr
                calendar.append(dict(date=day['date'],team=abbr,opponent=g[other]['abbrev']))
                if day['date']==m['date']:fixtures[abbr]=g
    aliases.update({k:v for k,v in LEGACY_TEAM_ALIASES.items() if v in aliases.values()})
    own['schedule_team']=own.nhl_team.map(lambda x:aliases.get(normalize_team(x)))
    own['eligible']=own.eligible_slots.fillna('').str.split('|')
    own['is_goalie']=own.primary_position.eq('Goalie')
    own['blocked']=own.injury_status.map(excluded_by_status)
    own['has_game']=own.schedule_team.isin(fixtures)
    own['is_current_active']=own.lineup_slot.isin(caps)
    own['locked']=own.schedule_team.map(lambda t: t in fixtures and (pd.Timestamp(fixtures[t]['startTimeUTC'])<=now or fixtures[t]['gameState'] not in ['FUT','PRE']))
    own['decision_state']='no game today'
    own.loc[own.schedule_team.isna(),'decision_state']='unresolved team mapping'
    own.loc[own.has_game,'decision_state']='upcoming'
    own.loc[own.has_game & own.blocked,'decision_state']='injury exclusion'
    own.loc[own.has_game & own.is_goalie,'decision_state']='starter unconfirmed'
    own.loc[own.locked,'decision_state']='game locked'
    own.loc[own.has_game & ~own.is_goalie & own.player_id.isna(),'decision_state']='forecast missing'
    own['start_local']=own.start_time_utc.map(lambda t:pd.Timestamp(t).tz_convert('America/New_York').strftime('%-I:%M %p') if pd.notna(t) else '')
    # Locked active players consume their actual saved slot. Off-day or blocked,
    # unlocked players can be benched; this is a lineup scenario, not a transaction.
    baseline=[]
    for row in own.to_dict('records'):
        if row['is_goalie'] or not row['is_current_active'] or not row['has_game']:continue
        if row['blocked'] and not row['locked']:continue
        baseline.append(dict(id=row['espn_player_id'],eligible=row['eligible'],
                             fixed_slot=row['lineup_slot'] if row['locked'] else None))
    skater_caps={k:v for k,v in caps.items() if k!='Goalie'}
    if fit_lineup(baseline,skater_caps) is None:raise ValueError('Saved active scenario does not fit league slots')
    actions=[];comparisons=[]
    bench=own[~own.is_goalie & own.lineup_slot.eq('Bench') & own.has_game & ~own.blocked & ~own.locked & own.player_id.notna()]
    for candidate in bench.to_dict('records'):
        item=dict(id=candidate['espn_player_id'],eligible=candidate['eligible'])
        assignment=fit_lineup(baseline+[item],skater_caps)
        if assignment:
            actions.append(f"START {candidate['player_name']} in {assignment[item['id']]}: an active slot is usable after benching off-day/injury-excluded players. Confirm dressing in ESPN.")
        else:
            for incumbent in own[~own.is_goalie & own.is_current_active & own.has_game & ~own.blocked & ~own.locked & own.player_id.notna()].to_dict('records'):
                test=[p for p in baseline if p['id']!=incumbent['espn_player_id']]+[item]
                if fit_lineup(test,skater_caps) is not None:
                    comparisons.append(dict(bench_player=candidate['player_name'],active_player=incumbent['player_name'],
                        category_dominant=dominates(candidate,incumbent,cats),
                        **{c['name']:candidate['expected_'+c['model_event']+'_if_plays']-incumbent['expected_'+c['model_event']+'_if_plays'] for c in cats if c['model_event']}))
    if bench.empty:actions.append('No unlocked benched skater has a game today in the saved roster; no additional rostered start is available.')
    for row in own[own.has_game & own.blocked & own.is_current_active].itertuples():
        actions.append(f"CHECK {row.player_name}: {row.injury_status} in an active {row.lineup_slot} slot; {row.roster_entry_status}. An OUT row is not expected to play.")
    ownmatch=matches[matches.team_id.eq(args.team_id)]
    if ownmatch.matchup_number.nunique()!=1:raise ValueError('Ambiguous current matchup')
    other=matches[(matches.matchup_number.eq(ownmatch.matchup_number.iloc[0])) & ~matches.team_id.eq(args.team_id)]
    gaps=[]
    for c in cats:
        a=ownmatch[ownmatch.category.eq(c['name'])];b=other[other.category.eq(c['name'])]
        if len(a)!=1 or len(b)!=1:raise ValueError('Missing scored matchup category')
        gaps.append(category_comparison(c['name'], a.score.iloc[0], b.score.iloc[0], c['lower_is_better']))
    gs=ownmatch[ownmatch.category.eq('GS')]
    minimum=rules['scoringSettings'].get('statQualificationMinimum',{}).get('limitValue')
    goalie_note=f"Saved goalie starts: {gs.score.iloc[0]:g}; minimum {minimum:g}." if len(gs)==1 and minimum is not None else 'Goalie qualification unavailable.'
    goalie_note+=' Goalie starts are unconfirmed. Additional starts can help W while changing GAA and SV%; no automatic start/sit call from the full-start means.'
    actions.append(goalie_note)
    future_rows=[];future_note='Next-period transaction roster was not supplied.'
    if args.future_roster:
        future=read_verified(args.future_roster,'rosters.csv');future=future[future.fantasy_team_id.eq(args.team_id)]
        new=future[~future.espn_player_id.isin(own.espn_player_id)]
        removed=own[~own.espn_player_id.isin(future.espn_player_id)]
        fmeta=json.loads((args.future_roster/'metadata.json').read_text())
        future_note=(f"Next scoring period {fmeta['requested_scoring_period']}: added "+(', '.join(new.player_name) or 'none')+
                     '; removed '+(', '.join(removed.player_name) or 'none')+'. Today retains the current-period roster until ESPN makes the change effective.')
        future_rows=records(future[['player_name','lineup_slot','roster_entry_status']])
        actions.insert(0,future_note)
    watch=available.merge(cw,on='espn_player_id',how='left',validate='one_to_one')
    watch=watch[watch.availability_status.eq('FREEAGENT') & watch.injury_status.eq('ACTIVE') & ~watch.espn_player_id.isin(roster.espn_player_id)]
    if args.future_roster:
        watch=watch[~watch.espn_player_id.isin(future.espn_player_id)]
    watch=watch[watch.nhl_player_id.notna()]
    if watch.nhl_player_id.duplicated().any():raise ValueError('Ambiguous available-player NHL identity')
    watch=watch.merge(projections,left_on='nhl_player_id',right_on='player_id',how='inner',validate='one_to_one')
    watch=watch[watch.issue_timing.eq('pregame') & watch.selected_for_trial.eq(True) & pd.to_datetime(watch.start_time_utc,utc=True).gt(now)]
    watch['start_local']=pd.to_datetime(watch.start_time_utc,utc=True).dt.tz_convert('America/New_York').dt.strftime('%-I:%M %p')
    watch['eligible']=watch.eligible_slots.fillna('').str.split('|')
    watch['open_slot_fit']=watch.apply(lambda r:fit_lineup(baseline+[dict(id=r.espn_player_id,eligible=r.eligible)],skater_caps) is not None,axis=1)
    add_window=acquisition_window_open([pd.Timestamp(g['startTimeUTC']) for g in fixtures.values()],now)
    watch['usable_starts_today']=watch.open_slot_fit.astype(int) if add_window else 0
    watch['action_status']='watchlist_only_transaction_timing_and_remaining_daily_allowance_unverified'
    watch=watch.sort_values(['open_slot_fit','expected_pp_points_if_plays','expected_assists_if_plays'],ascending=False)
    goalie=pd.read_csv(args.bundle/'goalie_projections.csv')
    goalie=goalie[goalie.model.eq('goalie_history_baseline') & goalie.player_id.isin(own.nhl_player_id)]
    goalie=goalie.merge(own[['nhl_player_id','lineup_slot']],left_on='player_id',right_on='nhl_player_id',validate='one_to_one')
    acq=rules['acquisitionSettings']
    transaction_note=('This is a category league: there is no single fantasy-points total. '
        'Lineup changes lock at each NHL game. Check the next-period roster above before treating an acquisition as available today. '
        'The captured acquisition limit is one per scoring period, but the available counters cover whole matchups; '
        'remaining daily allowance is unverified. Streamers are a watchlist, not an ADD instruction.')
    if not add_window:
        transaction_note="Today's add/drop window closed at the first scheduled NHL game. New acquisitions cannot contribute today; streamer rows are future planning only. Individual lineup swaps remain possible until each player's game."
    calendar_frame=pd.DataFrame(calendar).drop_duplicates()
    own_calendar=own[['espn_player_id','player_name','schedule_team','lineup_slot','injury_status']].merge(calendar_frame,left_on='schedule_team',right_on='team',how='left')
    if args.future_roster:
        current_calendar=own_calendar[own_calendar.date.eq(m['date'])]
        future_calendar=future[['espn_player_id','player_name','nhl_team','lineup_slot','injury_status']].copy()
        future_calendar['schedule_team']=future_calendar.nhl_team.map(lambda x:aliases.get(normalize_team(x)))
        future_calendar=future_calendar.drop(columns='nhl_team').merge(calendar_frame[calendar_frame.date.gt(m['date'])],left_on='schedule_team',right_on='team',how='left')
        own_calendar=pd.concat([current_calendar,future_calendar],ignore_index=True)
    payload=dict(team=name,date=m['date'],future_roster_supplied=bool(args.future_roster),created_at=now.astimezone(ZoneInfo('America/New_York')).strftime('%b %-d, %-I:%M %p ET'),
        acquisition_open_today=add_window,injuries_as_of=m['injuries_as_of_utc'],opponent=other.team_name.iloc[0],categories=cats,slots=caps,
        actions=actions,roster=records(own.drop(columns='eligible')),matchup=gaps,streamers=records(watch.drop(columns='eligible')),
        goalies=records(goalie),comparisons=comparisons,transaction_note=transaction_note,future_note=future_note,
        schedule=records(own_calendar),future_roster=future_rows,
        limitations=['Conditional means assume the player dresses; ACTIVE and lineup selection do not confirm participation.',
                     'Matchup scores are the saved ESPN snapshot, not live scores or final projected results.',
                     'ATOI is average ice time; adding a player below the team average can reduce it. GAA and SV% require exposure-weighted aggregation.',
                     'No calibrated category win probabilities or joint matchup simulation. Future calendar games are schedule opportunities, not predicted appearances.'])
    args.out.mkdir(parents=True,exist_ok=False)
    own.drop(columns='eligible').to_csv(args.out/'roster.csv',index=False)
    watch.drop(columns='eligible').to_csv(args.out/'streamer_watchlist.csv',index=False)
    pd.DataFrame(gaps).to_csv(args.out/'category_gaps.csv',index=False)
    pd.DataFrame(comparisons).to_csv(args.out/'start_sit_comparisons.csv',index=False)
    goalie.to_csv(args.out/'goalies.csv',index=False)
    own_calendar.to_csv(args.out/'roster_schedule.csv',index=False)
    (args.out/'report.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    template=(ROOT/'templates/fantasy_today.html').read_text()
    (args.out/'index.html').write_text(template.replace('__REPORT_DATA__',json.dumps(payload,allow_nan=False).replace('</','<\\/')))
    lines=[f"# {name} — {m['date']}",'', '[Interactive report and charts](index.html)','']
    lines += ['- '+a for a in actions]
    lines += ['',transaction_note,'','Charts: category gaps, sortable roster/streamer projections, and roster schedule calendar.','',
              'Model: default skaters, goalie history baseline. All goalie starts provisional.','']
    (args.out/'README.md').write_text('\n'.join(lines))
    sources=[args.bundle/'manifest.json',rules_path,snapshot/'metadata.json',crosswalk_path,raw_schedule,history_path]
    if args.future_roster:sources.append(args.future_roster/'metadata.json')
    manifest=dict(created_at_utc=now.isoformat(),date=m['date'],team_id=args.team_id,team_name=name,
        model='default',bundle=str(args.bundle),espn_snapshot=str(snapshot),rules_snapshot=str(args.rules),
        sources={str(p):sha(p) for p in sources},code_sha256={str(p):sha(p) for p in [Path(__file__),ROOT/'src/fantasy/decisions.py',ROOT/'templates/fantasy_today.html']},
        files={p.name:sha(p) for p in args.out.iterdir() if p.is_file()})
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Today report:',args.out/'index.html')
    print('\n'.join(actions));print('Streamer watchlist rows:',len(watch))


if __name__=='__main__':main()
