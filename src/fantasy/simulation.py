"""Provisional conditional count draws, not calibrated predictive intervals."""
import hashlib
import math
import numpy as np
from .per_game import require


def simulate_counts(means, *, draws=10000, seed=20261009, key=''):
    require(draws > 0, 'Draw count must be positive')
    for event in ['shots','goals','assists','hits','pp_points']:
        require(np.isfinite(means[event]) and means[event] >= 0, f'Invalid {event} mean')
    require(means['goals'] <= means['shots'], 'Goal mean exceeds shot mean')
    points_mean=means['goals']+means['assists']
    require(means['pp_points'] <= points_mean, 'PPP mean exceeds point mean')
    # Stable row keys avoid changing draws when roster ordering changes.
    entropy=int.from_bytes(hashlib.sha256(f'{seed}:{key}'.encode()).digest()[:8], 'little')
    rng=np.random.default_rng(entropy)
    shots=rng.poisson(means['shots'],draws)
    conversion=means['goals']/means['shots'] if means['shots'] else 0
    goals=rng.binomial(shots,conversion)
    assists=rng.poisson(means['assists'],draws)
    points=goals+assists
    pp_fraction=means['pp_points']/points_mean if points_mean else 0
    return dict(shots=shots,goals=goals,assists=assists,points=points,
                hits=rng.poisson(means['hits'],draws),pp_points=rng.binomial(points,pp_fraction))


def poisson_diagnostics(actual, means):
    """Score fixed marginal assumptions without tuning dispersion on the holdout."""
    actual=np.asarray(actual); means=np.asarray(means)
    require(np.isfinite(means).all() and (means >= 0).all(), 'Invalid Poisson means')
    require((actual >= 0).all() and (actual == np.floor(actual)).all(), 'Invalid count outcomes')
    p=1-np.exp(-means)
    positive=means>0
    nll=np.zeros(len(actual),dtype=float)
    nll[positive]=means[positive]-actual[positive]*np.log(means[positive])+np.array([math.lgamma(float(y)+1) for y in actual[positive]])
    impossible=(~positive)&(actual>0)
    nll[impossible]=np.inf
    return dict(appearances=len(actual),mean_nll=float(nll.mean()),
                zero_mean_positive_actual=int(impossible.sum()),
                positive_mean_nll=float(nll[positive].mean()) if positive.any() else None,
                at_least_one_brier=float(((p-(actual>0))**2).mean()),
                positive_mean_pearson_second_moment=float((((actual[positive]-means[positive])**2)/means[positive]).mean()) if positive.any() else None)
