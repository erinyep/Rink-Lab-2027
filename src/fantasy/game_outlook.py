"""Reading views over frozen NHL team forecasts; no refitting or new win model."""
import math


def game_outlooks(team_rows, schedule_games):
    """Pair each saved model's team rows against official home/away identities."""
    schedule={g['id']:g for g in schedule_games}
    if len(schedule)!=len(schedule_games):
        raise ValueError('Duplicate scheduled game')
    by_game={}
    identities=set()
    required=['expected_goals','expected_shots','goals_p10','goals_p90','shots_p10','shots_p90']
    for row in team_rows:
        key=(row['game_id'],row['model'],row['team'])
        if key in identities:raise ValueError('Duplicate team/model forecast')
        identities.add(key)
        if row['game_id'] not in schedule:raise ValueError('Forecast game absent from schedule')
        if not all(math.isfinite(float(row[c])) and float(row[c])>=0 for c in required):
            raise ValueError('Missing/nonfinite/negative forecast')
        if not (row['goals_p10']<=row['goals_p90'] and row['shots_p10']<=row['shots_p90']):
            raise ValueError('Reversed simulation range')
        by_game.setdefault((row['game_id'],row['model']),[]).append(row)
    output=[]
    for (gid,model),rows in by_game.items():
        g=schedule[gid];home=g['homeTeam']['abbrev'];away=g['awayTeam']['abbrev']
        if len(rows)!=2 or {r['team'] for r in rows}!={home,away}:raise ValueError('Missing or incorrect game teams')
        indexed={r['team']:r for r in rows};h=indexed[home];a=indexed[away]
        if h['opponent']!=away or a['opponent']!=home:raise ValueError('Opponent identity differs from schedule')
        if h['issue_timing']!=a['issue_timing']:raise ValueError('Conflicting issue timing')
        if h['start_time_utc']!=g['startTimeUTC'] or a['start_time_utc']!=g['startTimeUTC']:
            raise ValueError('Game start differs from saved schedule')
        edge=h['expected_goals']-a['expected_goals']
        output.append(dict(game_id=gid,model=model,home=home,away=away,
            home_name=team_name(g['homeTeam']),away_name=team_name(g['awayTeam']),
            start_time_utc=g['startTimeUTC'],issue_timing=h['issue_timing'],
            higher_scoring_mean=home if edge>0 else away if edge<0 else 'even',
            home_goal_edge=edge,total_expected_goals=h['expected_goals']+a['expected_goals'],
            **{'home_'+k:h[k] for k in required+['identified_skaters','unidentified_replacement_skaters']},
            **{'away_'+k:a[k] for k in required+['identified_skaters','unidentified_replacement_skaters']}))
    models={r['model'] for r in output}
    for model in models:
        if {r['game_id'] for r in output if r['model']==model}!=set(schedule):
            raise ValueError('Model does not cover every scheduled game')
    return sorted(output,key=lambda r:(r['start_time_utc'],r['game_id'],r['model']))


def team_name(team):
    return (team.get('placeName',{}).get('default','')+' '+team.get('commonName',{}).get('default',team['abbrev'])).strip()
