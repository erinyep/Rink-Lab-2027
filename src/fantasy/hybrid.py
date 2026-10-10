"""Experimental shot calibration plus opponent context, with explicit fallbacks."""
import numpy as np
from .per_game import require


def hybrid_shots(baseline, multiplier, context_factor, fallback=None):
    """Missing rates use supplied pregame priors; missing context is neutral.

    Observed zero rates remain zero. A caller must explicitly decide whether
    sparse-history shrinkage should replace them. No outcome-derived filling.
    """
    require(np.isfinite(multiplier) and multiplier > 0, 'Invalid calibration')
    rate_status = 'observed_baseline'
    if not np.isfinite(baseline):
        require(fallback is not None and np.isfinite(fallback) and fallback >= 0,
                'Missing shot mean requires a documented pregame fallback')
        baseline = fallback
        rate_status = 'pregame_position_prior'
    require(baseline >= 0, 'Negative shot mean')
    context_status = 'available'
    if not np.isfinite(context_factor):
        context_factor = 1.0
        context_status = 'missing_neutral_factor'
    require(context_factor > 0, 'Invalid opponent factor')
    return baseline * multiplier * context_factor, rate_status, context_status
