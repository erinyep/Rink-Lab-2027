"""Conservative calibration of frozen team probabilities on strictly earlier dates."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit
from .per_game import require


def fit_probability_calibration(rows, target_date, *, ridge=20., min_games=30,
                                min_dates=4, min_class=5):
    require(ridge > 0 and min_games > 0 and min_dates > 0 and min_class > 0, 'Invalid calibration settings')
    train = rows[rows.date < target_date].copy()
    require(not train.game_id.duplicated().any(), 'Duplicate calibration game')
    p = train.probability.to_numpy(dtype=float)
    y = train.actual_home_win.to_numpy(dtype=float)
    require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), 'Invalid raw probability')
    require(np.isin(y,[0,1]).all(), 'Nonbinary winner')
    result = dict(version='ridge_logistic_probability_challenger_v1', target_date=target_date,
        training_through=str(train.date.max()) if len(train) else None, games=len(train),
        dates=int(train.date.nunique()), training_game_ids=sorted(map(int,train.game_id)),
        intercept=0., slope=1., ridge=ridge, status='identity_insufficient_history')
    if len(train)<min_games or train.date.nunique()<min_dates or min(y.sum(),len(y)-y.sum())<min_class:
        return result
    x = logit(np.clip(p,1e-6,1-1e-6))
    def objective(beta):
        eta = beta[0] + beta[1]*x
        return np.logaddexp(0,eta).sum()-y@eta + .5*ridge*(beta[0]**2+(beta[1]-1)**2)
    def gradient(beta):
        error = expit(beta[0]+beta[1]*x)-y
        return np.array([error.sum()+ridge*beta[0],error@x+ridge*(beta[1]-1)])
    # A nonnegative slope preserves rankings; regularization anchors identity.
    fitted = minimize(objective,[0.,1.],jac=gradient,bounds=[(-2.,2.),(0.,3.)],method='L-BFGS-B')
    require(fitted.success and np.isfinite(fitted.x).all(), 'Calibration optimization failed')
    result.update(intercept=float(fitted.x[0]),slope=float(fitted.x[1]),status='fitted_experimental')
    return result


def calibrated_probability(probabilities, fitted, target_date):
    require(fitted['training_through'] is None or fitted['training_through'] < target_date,
            'Calibration contains target-date outcomes')
    require(fitted['target_date'] <= target_date, 'Calibration release is from a later date')
    p = np.asarray(probabilities,dtype=float)
    require(np.isfinite(p).all() and ((p>=0)&(p<=1)).all(), 'Invalid probability')
    require(np.isfinite([fitted['intercept'],fitted['slope']]).all() and fitted['slope']>=0,
            'Invalid calibration coefficients')
    if fitted['status']=='identity_insufficient_history':
        return p.copy()
    return expit(fitted['intercept']+fitted['slope']*logit(np.clip(p,1e-6,1-1e-6)))


def reliability_table(rows, bins=5):
    """Fixed bins; retain sample sizes and empty bins instead of overstating calibration."""
    require(bins>0,'Invalid reliability bins')
    frame=rows.copy()
    frame['bin']=pd.cut(frame.probability,np.linspace(0,1,bins+1),include_lowest=True)
    return frame.groupby('bin',observed=False).agg(games=('game_id','size'),
        mean_probability=('probability','mean'),observed_home_win_rate=('actual_home_win','mean')).reset_index()
