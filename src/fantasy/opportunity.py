"""Past-only PP opportunity challenger, separate from shots and participation."""
import numpy as np
import pandas as pd
from .per_game import require


def historical_pp_prior(panel, player_id, position_group, season_id):
    """Use completed-season minutes and events, with position fallback for rookies."""
    past = panel[(panel.season_id < season_id) & (panel.season_id >= season_id - 30003)].copy()
    require(not past.duplicated(['player_id', 'season_id']).any(), 'Duplicate historical season')
    player = past[past.player_id.eq(player_id)]
    source = 'player_completed_seasons' if len(player) else 'position_completed_seasons'
    h = player if len(player) else past[past.position_group.eq(position_group)]
    cols = ['games_played', 'toi_minutes', 'pp_toi_minutes', 'pp_points']
    require(not h.empty and h[cols].notna().all().all(), 'Missing PP prior exposure')
    require(np.isfinite(h[cols]).all().all() and h[cols].ge(0).all().all(), 'Invalid PP prior')
    require(h.pp_toi_minutes.le(h.toi_minutes + 1e-6).all(), 'PP minutes exceed total minutes')
    weights = .5 ** ((season_id // 10000 - 1) - h.season_id // 10000)
    totals = h[cols].mul(weights, axis=0).sum()
    require(totals.games_played > 0 and totals.toi_minutes > 0, 'No historical exposure')
    # Zero historical PP exposure is a real role, not missing data. A position
    # rate is still needed if a player with that role receives a new assignment.
    group = past[past.position_group.eq(position_group)]
    require(not group.empty and group[cols].notna().all().all(), 'Missing position prior')
    gw = .5 ** ((season_id // 10000 - 1) - group.season_id // 10000)
    gp = group[cols].mul(gw, axis=0).sum()
    group_rate = gp.pp_points / gp.pp_toi_minutes if gp.pp_toi_minutes > 0 else 0.
    # Shrink a player's completed-season event rate toward the position rate.
    rate = (totals.pp_points + 120 * group_rate) / (totals.pp_toi_minutes + 120)
    return dict(prior_pp_minutes=float(totals.pp_toi_minutes / totals.games_played),
                prior_pp_rate=float(rate), pp_prior_source=source)


def power_play_opportunity(history, exposure, player_id, target_date, prior_pp_minutes,
                           prior_pp_rate, expected_toi_minutes, *, window=5,
                           exposure_prior_games=10., rate_prior_minutes=120.):
    """Recent PP deployment times a shrunk event rate, never total-TOI scaling.

    All inputs, including priors, must precede the target. Hyperparameters are
    fixed research assumptions; no fit to a single slate is claimed.
    """
    require(window > 0 and exposure_prior_games > 0 and rate_prior_minutes > 0,
            'Invalid opportunity shrinkage')
    values = [prior_pp_minutes, prior_pp_rate, expected_toi_minutes]
    require(np.isfinite(values).all() and min(values) >= 0, 'Invalid opportunity prior')
    keys = ['game_id', 'player_id']
    h = history[(history.game_date < target_date) & history.player_id.eq(player_id)
                & history.toi_seconds.gt(0)].copy()
    e = exposure[(exposure.game_date < target_date) & exposure.player_id.eq(player_id)
                 & exposure.toi_seconds.gt(0)].copy()
    require(not h.duplicated(keys).any() and not e.duplicated(keys).any(), 'Duplicate PP appearance')
    h = h.sort_values(['game_date','game_id']).tail(window)
    e = e.rename(columns={'toi_seconds':'exposure_toi_seconds', 'game_date':'exposure_game_date'})
    joined = h.merge(e[keys + ['pp_toi_seconds','exposure_toi_seconds','exposure_game_date']],
                     on=keys, how='left', validate='one_to_one')
    require(joined.pp_toi_seconds.notna().all(), 'Missing PP exposure for observed player')
    require(joined.game_date.eq(joined.exposure_game_date).all(), 'PP exposure date differs')
    require(np.allclose(joined.toi_seconds,joined.exposure_toi_seconds), 'PP exposure total differs')
    require(joined.pp_toi_seconds.ge(0).all() and joined.pp_toi_seconds.le(joined.toi_seconds).all(),
            'Invalid PP minutes')
    require(joined.pp_points.notna().all() and joined.pp_points.ge(0).all(), 'Invalid PP points')
    minutes = float(joined.pp_toi_seconds.sum() / 60)
    events = float(joined.pp_points.sum())
    require(not ((joined.pp_toi_seconds.eq(0)) & joined.pp_points.gt(0)).any(), 'PP points without PP exposure')
    expected_minutes = (minutes + exposure_prior_games * prior_pp_minutes) / (len(joined) + exposure_prior_games)
    expected_minutes = min(expected_minutes, expected_toi_minutes)
    rate = (events + rate_prior_minutes * prior_pp_rate) / (minutes + rate_prior_minutes)
    return dict(expected_pp_minutes=expected_minutes, expected_non_pp_minutes=expected_toi_minutes-expected_minutes,
                pp_points_per_minute=rate, opportunity_pp_points=expected_minutes*rate,
                recent_pp_games=len(joined), recent_pp_minutes=minutes, recent_pp_points=events,
                pp_model_status='fixed_past_only_opportunity_challenger')


def apply_opportunity_means(calibrated_means, usage_toi, pp=None):
    """Isolate exposure changes: preserve SOG/G/A means and their selection."""
    means = calibrated_means.copy()
    means['toi_minutes'] = usage_toi
    if pp is not None:
        means['pp_points'] = min(pp['opportunity_pp_points'], means['goals'] + means['assists'])
    return means
