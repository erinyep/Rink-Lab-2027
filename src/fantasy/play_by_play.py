"""Auditable NHL event-derived defense opportunity measures, not causal credit."""
import math
import pandas as pd
from .per_game import require

ATTEMPTS = {'shot-on-goal', 'missed-shot', 'blocked-shot', 'goal'}
STOPS = {'stoppage', 'faceoff', 'period-end', 'period-start', 'game-end', 'penalty', 'delayed-penalty'}


def parse_game(game):
    require(game['gameType'] == 2 and game['gameState'] in {'OFF', 'FINAL'}, 'Not final regular season')
    roster = {p['playerId']: p for p in game['rosterSpots']}
    require(len(roster) == len(game['rosterSpots']), 'Duplicate roster ID')
    teams = {game[k]['id']: game[k]['abbrev'] for k in ['homeTeam', 'awayTeam']}
    plays = sorted(game['plays'], key=lambda p: p['sortOrder'])
    require(len({p['eventId'] for p in plays}) == len(plays), 'Duplicate event ID')
    rows = []; anchor = None
    for p in plays:
        if p['periodDescriptor']['periodType'] == 'SO':
            continue
        period = p['periodDescriptor']['number']; kind = p['typeDescKey']; d = p.get('details', {})
        minutes, seconds = map(int, p['timeInPeriod'].split(':')); elapsed = 60*minutes+seconds
        if anchor and (anchor['period'] != period or elapsed-anchor['time'] > 10):
            anchor = None
        if kind in STOPS:
            anchor = None
        if kind not in ATTEMPTS:
            # Conservative reset on opponent recorded puck actions, not hits.
            if anchor and kind in {'takeaway', 'giveaway'} and d.get('eventOwnerTeamId') != anchor['team_id']:
                anchor = None
            continue
        pid = d.get('scoringPlayerId') if kind == 'goal' else d.get('shootingPlayerId')
        player = roster.get(pid, {})
        # Blocked-shot owner can be the blocker; roster shooter team is primary.
        tid = player.get('teamId')
        if tid is None and kind != 'blocked-shot':
            tid = d.get('eventOwnerTeamId')
        require(tid in teams, 'Unresolved shooting team')
        position = player.get('positionCode')
        assists = [d[k] for k in ['assist1PlayerId', 'assist2PlayerId'] if d.get(k)]
        d_assists = sum(roster.get(x, {}).get('positionCode') == 'D' for x in assists)
        code = str(p.get('situationCode', ''))
        five = code == '1551'
        distance = None
        if d.get('xCoord') is not None and d.get('yCoord') is not None and p.get('homeTeamDefendingSide') in {'left','right'}:
            # Home defending left attacks +x; away attacks the opposite net.
            sign = 1 if p['homeTeamDefendingSide'] == 'left' else -1
            if tid != game['homeTeam']['id']:
                sign *= -1
            distance = math.hypot(89-sign*d['xCoord'], d['yCoord'])
        continuation = bool(anchor and anchor['team_id'] == tid and pid != anchor['player_id']
                            and elapsed >= anchor['time'])
        rows.append(dict(game_id=game['id'], game_date=game['gameDate'], event_id=p['eventId'],
            period=period, seconds_in_period=elapsed, team=teams[tid], player_id=pid,
            position=position, event=kind, situation_code=code, five_on_five=five,
            defense_attempt=position=='D', on_goal=kind in {'goal','shot-on-goal'},
            unblocked=kind!='blocked-shot', distance_to_attacking_net=distance,
            near_net_attempt=distance<=25 if distance is not None else None,
            defense_assist_credits=d_assists, goal_with_defense_involvement=kind=='goal' and (position=='D' or d_assists>0),
            follows_defense_attempt_within10s=continuation,
            defense_anchor_event_id=anchor['event_id'] if continuation else None))
        # Most recent D attempt anchors at most one credit per following event.
        # Goal ends the chain; opponent attempts break it. This is not possession.
        if kind == 'goal':
            anchor = None
        elif position == 'D':
            anchor = dict(period=period, time=elapsed, team_id=tid, player_id=pid, event_id=p['eventId'])
        elif anchor and tid != anchor['team_id']:
            anchor = None
    return pd.DataFrame(rows)


def team_measures(events):
    rows = []
    for (gid, team), all_events in events.groupby(['game_id', 'team']):
        for strength in ['all', '5v5']:
            e = all_events if strength == 'all' else all_events[all_events.five_on_five]
            defense = e[e.defense_attempt]
            rows.append(dict(game_id=gid, game_date=all_events.game_date.iloc[0], team=team, strength=strength,
                team_attempts=len(e), defense_attempts=len(defense),
                defense_unblocked_attempts=int(defense.unblocked.sum()), defense_sog=int(defense.on_goal.sum()),
                defense_near_net_attempts=int(defense.near_net_attempt.fillna(False).sum()),
                defense_assist_credits=int(e.defense_assist_credits.sum()),
                goals_with_defense_involvement=int(e.goal_with_defense_involvement.sum()),
                followup_attempts_after_defense=int(e.follows_defense_attempt_within10s.sum()),
                unknown_shooter_position=int(e.position.isna().sum()),
                missing_coordinates=int(e.distance_to_attacking_net.isna().sum())))
    return pd.DataFrame(rows)


def lagged_defense_context(team_games, audit, before):
    """Exclude target dates and quarantine BOTH teams of discrepant games."""
    bad=set(audit.loc[~audit.sog_match,'game_id'])
    past=team_games[team_games.game_date.lt(before)].copy()
    rows=[]
    for team,t in past.groupby('team'):
        for strength in ['all','5v5']:
            g=t[t.strength.eq(strength) & ~t.game_id.isin(bad)]
            n=len(g)
            row=dict(team=team,strength=strength,before_date=before,games_used=n,
                     quarantined_games=t[t.strength.eq(strength) & t.game_id.isin(bad)].game_id.nunique(),
                     latest_game_date=g.game_date.max() if n else None)
            for c in ['defense_attempts','defense_unblocked_attempts','defense_sog','defense_near_net_attempts',
                      'defense_assist_credits','goals_with_defense_involvement','followup_attempts_after_defense']:
                row[c+'_per_game']=g[c].sum()/n if n else float('nan')
            row['defense_attempt_share']=g.defense_attempts.sum()/g.team_attempts.sum() if g.team_attempts.sum() else float('nan')
            rows.append(row)
    return pd.DataFrame(rows)


def lagged_shot_quality(team_games, before):
    require(not team_games.duplicated(['game_id','team','strength']).any(), 'Duplicate shot quality team-game')
    past=team_games[team_games.game_date.lt(before)]
    rows=[]
    for (team,strength),all_games in past.groupby(['team','strength']):
        g=all_games[~all_games.source_quarantined]
        row=dict(team=team,strength=strength,before_date=before,games_used=len(g),
                 quarantined_games=int(all_games.source_quarantined.sum()))
        for c in ['defense_xg','defense_expected_rebounds','defense_unblocked_attempts','team_xg']:
            row[c+'_per_game']=g[c].sum()/len(g) if len(g) else float('nan')
        rows.append(row)
    return pd.DataFrame(rows)
