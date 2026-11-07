"""Fail-closed checks for complete, fresh pregame releases."""
from datetime import timedelta
import numpy as np
import pandas as pd
from .per_game import require


def validate_release(manifest, games, players, teams, goalies, context, now,
                     max_age_hours=6, lead_minutes=10, allow_context_lag=False):
    now=pd.Timestamp(now)
    require(now.tzinfo is not None, 'Release time must be timezone-aware')
    require(max_age_hours>0 and lead_minutes>=0, 'Invalid freshness/lead settings')
    require(not manifest.get('finalized_at_utc'), 'Bundle already finalized')
    expected={g['id'] for g in games}
    require(expected, 'No official scheduled games')
    game_by_id={g['id']:g for g in games}
    public_only=manifest.get('availability_status')=='disabled_public_data_only'
    if public_only:
        require(players.injury_status.eq('UNKNOWN').all() and goalies.injury_status.eq('UNKNOWN').all(),
                'Public mode must expose unknown injuries')
    else:
        age=(now-pd.Timestamp(manifest['injuries_as_of_utc'])).total_seconds()/3600
        require(0<=age<=max_age_hours, 'Stale or future injury snapshot')
    require(pd.Timestamp(manifest['created_at_utc'])<=now, 'Future bundle timestamp')
    team_keys={(g['id'],g[k]['abbrev']) for g in games for k in ['homeTeam','awayTeam']}
    models=set(manifest['config']['models'])
    timing_by_game={}
    for label,f in [('players',players),('teams',teams),('goalies',goalies)]:
        require(set(f.game_id)==expected, 'Incomplete '+label+' game coverage')
        require(set(zip(f.game_id,f.team))==team_keys, 'Incomplete '+label+' team coverage')
        require(f.issue_timing.isin(['pregame','late_not_pregame']).all(), 'Invalid issue timing in '+label)
        timing=f.groupby('game_id').issue_timing.agg(lambda x:set(x))
        require(timing.map(len).eq(1).all(), 'Conflicting issue timing within '+label+' game')
        observed={game_id:next(iter(values)) for game_id,values in timing.items()}
        if timing_by_game:
            require(observed==timing_by_game, 'Issue timing differs across forecast populations')
        timing_by_game=observed
        if 'issued_at_utc' in f:
            issued=pd.to_datetime(f.issued_at_utc,utc=True)
        else:
            issued=pd.Series(pd.Timestamp(manifest['created_at_utc']),index=f.index)
        for game_id,part in f.assign(_issued_at=issued).groupby('game_id'):
            game=game_by_id[game_id]
            start=pd.Timestamp(game['startTimeUTC'])
            issue_time=part._issued_at.max()
            if observed[game_id]=='pregame':
                require(game['gameState'] in {'FUT','PRE'}, 'Pregame label on started game in '+label)
                require(start>issue_time+timedelta(minutes=lead_minutes), 'Insufficient lead time in '+label)
            else:
                require(game['gameState'] not in {'FUT','PRE'} or start<=issue_time,
                        'Late label before puck drop in '+label)
    for f,keys in [(players,['game_id','player_id','category']), (teams,['game_id','team','category'])]:
        require(not f.duplicated(keys+['model']).any(), 'Duplicate forecast')
        require(f.groupby(keys).model.agg(set).map(lambda x:x==models).all(), 'Incomplete model comparison')
    player_categories={'goals','assists','shots','hits','points','pp_points','penalty_minutes','plus_minus','toi_minutes'}
    team_categories={'goals','assists','shots','hits','points','pp_points'}
    require(players.groupby(['game_id','player_id','model']).category.agg(set).map(lambda x:x==player_categories).all(), 'Incomplete player categories')
    require(teams.groupby(['game_id','team','model']).category.agg(set).map(lambda x:x==team_categories).all(), 'Incomplete team categories')
    require(not goalies.duplicated(['game_id','player_id','model']).any(), 'Duplicate goalie forecast')
    require(np.isfinite(players.model_projection_if_plays).all(), 'Missing player means')
    require(np.isfinite(teams.projection_mean).all(), 'Missing team means')
    cols=['shots_against_if_full_start','saves_if_full_start','goals_against_if_full_start']
    require(np.isfinite(goalies[cols]).all().all(), 'Missing goalie means')
    require(np.allclose(goalies[cols[0]],goalies[cols[1]]+goalies[cols[2]]), 'Goalie shot identity')
    require(goalies.groupby(['game_id','team']).model.nunique().eq(2).all(), 'Both goalie models required')
    require(players.actual.isna().all() and teams.actual.isna().all(), 'Outcomes populated before release')
    require(allow_context_lag or context.moneypuck_missing_nhl_games.eq(0).all(), 'MoneyPuck coverage lags NHL; explicit exception required')
    pregame_games=sum(value=='pregame' for value in timing_by_game.values())
    return dict(validated_at_utc=now.isoformat(), games=len(expected),pregame_games=pregame_games,
        late_games=len(expected)-pregame_games,teams=len(team_keys),
        injury_max_age_hours=max_age_hours,minimum_lead_minutes=lead_minutes,
        context_lag_explicitly_accepted=allow_context_lag)
