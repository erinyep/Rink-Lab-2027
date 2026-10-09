"""Interpretable, provisional goalie rates with visible count-exception exclusions."""
import numpy as np
from .per_game import require
from .availability import excluded_by_status


def start_shares(starts,statuses):
    weights={pid:0 if excluded_by_status(statuses[pid]) else count+1 for pid,count in starts.items()}
    total=sum(weights.values())
    return {pid:weight/total if total else np.nan for pid,weight in weights.items()}


def goalie_rates(history, player_id, prior_shots=200, prior_minutes=600):
    valid=history[history.eligible_for_valuation & (history.shots_against==history.saves+history.goals_against)].copy()
    prior=valid[valid.season_id<20262027]
    require(not prior.empty,'No valid completed-season goalie prior')
    prior_sv=float((prior.saves*prior.weight).sum()/(prior.shots_against*prior.weight).sum())
    prior_sa60=float((prior.shots_against*prior.weight).sum()*3600/(prior.time_on_ice*prior.weight).sum())
    obs=valid[valid.player_id==player_id]
    sa=float((obs.shots_against*obs.weight).sum()); saves=float((obs.saves*obs.weight).sum())
    seconds=float((obs.time_on_ice*obs.weight).sum())
    sv=(saves+prior_shots*prior_sv)/(sa+prior_shots)
    sa60=(sa+prior_minutes*prior_sa60/60)/(seconds/60+prior_minutes)*60
    require(0<=sv<=1 and np.isfinite(sa60),'Invalid goalie rate')
    return dict(save_probability=sv,shots_against_per_60=sa60,weighted_shots=sa,
        observed_save_weight=sa/(sa+prior_shots),weighted_minutes=seconds/60,
        fallback='past_league_prior' if obs.empty else 'weighted_history_with_shrinkage')


def simulate_goalie(shots_mean,save_probability,goals_for_mean,draws=10000,seed=20261009):
    require(shots_mean>=0 and 0<=save_probability<=1 and goals_for_mean>=0,'Invalid simulation inputs')
    rng=np.random.default_rng(seed)
    sa=rng.poisson(shots_mean,draws); saves=rng.binomial(sa,save_probability); ga=sa-saves
    gf=rng.poisson(goals_for_mean,draws)
    win_proxy=float((gf>ga).mean()+.5*(gf==ga).mean())
    return dict(shots_against=sa,saves=saves,goals_against=ga),win_proxy
