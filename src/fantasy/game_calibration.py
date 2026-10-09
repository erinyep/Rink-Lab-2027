"""Experimental pooled event calibration; distinct from player skill estimation."""
import numpy as np
from .per_game import require


def fit_calibration(rows, prior_expected_events=200.0):
    """Shrink observed/expected ratios toward 1 with explicit pseudo-event mass.

The fixed prior is a conservative initial assumption, not a tuned parameter.
Use only completed calibration dates; assess subsequent games separately.
    """
    require(prior_expected_events > 0, 'Calibration prior must be positive')
    valid = rows[(rows.appeared == True) & rows.shots_if_plays.notna()].copy()
    require(not valid.empty, 'No calibration appearances')
    require(not valid.duplicated(['game_id', 'player_id']).any(), 'Duplicate calibration appearance')
    factors = {}
    for event in ['shots', 'assists']:
        subset = valid.dropna(subset=[event, f'{event}_if_plays'])
        expected = float(subset[f'{event}_if_plays'].sum())
        actual = float(subset[event].sum())
        require(expected > 0 and actual >= 0, 'Invalid event exposure')
        factors[event] = dict(multiplier=(actual + prior_expected_events) / (expected + prior_expected_events),
            predicted_events=expected, observed_events=actual, player_games=len(subset),
            prior_expected_events=prior_expected_events)
    return factors


def apply_calibration(rows, factors):
    """Preserve original conditional means, participation unknowns, and missingness."""
    result = rows.copy()
    for event in ['shots', 'assists']:
        multiplier = factors[event]['multiplier']
        require(np.isfinite(multiplier) and multiplier > 0, 'Invalid calibration factor')
        result[f'baseline_{event}_if_plays'] = result[f'{event}_if_plays']
        result[f'{event}_if_plays'] *= multiplier
    result['baseline_points_if_plays'] = result.points_if_plays
    result['points_if_plays'] = result.goals_if_plays + result.assists_if_plays
    result['model_version'] = 'pooled_calibration_v1_experimental'
    result['model_status'] = 'unvalidated_on_subsequent_games'
    # Operational review labels do not estimate an appearance probability.
    result['lineup_review_required'] = result.injury_status.fillna('UNKNOWN') != 'ACTIVE'
    return result


def shot_error_components(rows):
    valid = rows[(rows.appeared == True) & rows.shots_if_plays.notna() & (rows.toi_minutes_if_plays > 0)].copy()
    rate = valid.shots_if_plays / valid.toi_minutes_if_plays
    valid['shot_error_toi_component'] = rate * (valid.toi_minutes_if_plays - valid.toi_minutes)
    valid['shot_error_rate_residual'] = rate * valid.toi_minutes - valid.shots
    # Actual TOI is used only to explain errors, never as a prediction feature.
    return valid
