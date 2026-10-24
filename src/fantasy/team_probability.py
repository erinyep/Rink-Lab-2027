"""Uncalibrated scoring-count probability baseline, separate from team means."""
import math
import numpy as np


def scoring_win_probability(home_mean, away_mean):
    """Independent Poisson counts, with tied counts split equally.

    Input means cover the saved game's scoring exposure (not regulation-only).
    This is an approximation, not an OT/shootout or confirmed-goalie model.
    """
    means = [float(home_mean), float(away_mean)]
    if any(not math.isfinite(x) or not 0 <= x <= 100 for x in means):
        raise ValueError('Invalid hockey goal mean')
    pmfs = []
    for mean in means:
        p = [math.exp(-mean)]
        for k in range(1, 300):
            p.append(p[-1] * mean / k)
        p = np.array(p)
        if abs(p.sum() - 1) > 1e-10:
            raise ValueError('Incomplete probability mass')
        pmfs.append(p)
    h, a = pmfs
    return float(h @ (np.cumsum(a) - .5 * a))
