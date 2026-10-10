"""Cutoff-safe player inputs and provisional recent-usage shot estimates."""
import numpy as np
import pandas as pd
from .per_game import EVENTS, TARGETS, require


def coherent_count_means(means):
    """Retain goals, cap PPP at points, and expose feasibility corrections.

    Calibration of assists alone can make a sparse player's PPP exceed G+A.
    These are probability-support constraints, not fitted performance gains.
    """
    out=means.copy()
    flags=dict(goal_shot_constraint_applied=out['shots']<out['goals'],
               pp_point_constraint_applied=out['pp_points']>out['goals']+out['assists'])
    out['shots']=max(out['shots'],out['goals'])
    out['points']=out['goals']+out['assists']
    out['pp_points']=min(out['pp_points'],out['points'])
    return out,flags


def current_from_games(games, target_date, season_id):
    require(not games.duplicated(['game_id','player_id']).any(), 'Duplicate player/game')
    past = games[(games.game_date < target_date)&(games.toi_seconds > 0)].copy()
    require(not past.empty, 'No completed pre-date player history')
    totals = past.groupby('player_id')[TARGETS].sum()
    totals['games_played'] = past.groupby('player_id').size()
    latest = past.sort_values(['game_date','game_id']).drop_duplicates('player_id',keep='last').set_index('player_id')
    totals['skater_full_name'] = latest['name']
    totals['position_code'] = latest.position
    totals['position_group'] = np.where(totals.position_code == 'D','D','F')
    totals['team_abbrevs'] = latest.team
    totals['season_id'] = season_id
    totals['source_snapshot'] = 'cutoff_game_history'
    require(np.isfinite(totals[TARGETS]).all().all(), 'Invalid game aggregates')
    return totals.reset_index()


def recent_shot_usage(history, player_id, target_date, prior_shots, prior_toi,
                      window=5, toi_prior_games=10, rate_prior_minutes=200):
    """Fixed shrinkage assumptions; priors must exclude the current season.

    Keep rate and exposure distinct. Recent games are neither independent
    evidence of changed talent nor enough to validate the selected weights.
    """
    require(prior_toi > 0 and prior_shots >= 0, 'Invalid usage prior')
    h=history[(history.player_id==player_id)&(history.game_date<target_date)&(history.toi_seconds>0)]
    h=h.sort_values(['game_date','game_id']).tail(window)
    rate=(h.shots.sum()+rate_prior_minutes*prior_shots/prior_toi)/(h.toi_minutes.sum()+rate_prior_minutes)
    toi=(h.toi_minutes.sum()+toi_prior_games*prior_toi)/(len(h)+toi_prior_games)
    return dict(recent_games=len(h), recent_shots=float(h.shots.sum()),
        recent_toi_minutes=float(h.toi_minutes.sum()),usage_toi_minutes=float(toi),
        usage_shots_per_minute=float(rate),usage_shots_before_context=float(toi*rate))
