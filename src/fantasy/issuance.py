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
    require(all(g['gameState'] in {'FUT','PRE'} for g in games), 'Game already started or final')
    starts=pd.to_datetime([g['startTimeUTC'] for g in games],utc=True)
    require((starts>now+timedelta(minutes=lead_minutes)).all(), 'Insufficient lead time')
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
    for label,f in [('players',players),('teams',teams),('goalies',goalies)]:
        require(set(f.game_id)==expected, 'Incomplete '+label+' game coverage')
        require(set(zip(f.game_id,f.team))==team_keys, 'Incomplete '+label+' team coverage')
        require(f.issue_timing.eq('pregame').all(), 'Late rows in '+label)
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
    return dict(validated_at_utc=now.isoformat(), games=len(expected),teams=len(team_keys),
        injury_max_age_hours=max_age_hours,minimum_lead_minutes=lead_minutes,
        context_lag_explicitly_accepted=allow_context_lag)
