"""Interpretable Poisson team-goal model with strictly lagged hockey context."""
import numpy as np
import pandas as pd
import json
import hashlib
from pathlib import Path
from scipy.optimize import minimize


RATE_COLUMNS=['goalsFor','goalsAgainst','xGoalsFor','xGoalsAgainst']


def load_history(moneypuck, boxscores, through):
    """Validate published history and reconcile current-season official targets."""
    moneypuck,boxscores=Path(moneypuck),Path(boxscores)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    mp=moneypuck/'all_teams.csv';mm=json.loads((moneypuck/'metadata.json').read_text())
    if sha(mp)!=mm['sha256']:raise ValueError('Changed MoneyPuck source')
    columns=['season','gameId','gameDate','team','opposingTeam','home_or_away','situation','playoffGame',*RATE_COLUMNS,'shotsOnGoalFor','shotsOnGoalAgainst']
    frame=pd.read_csv(mp,usecols=columns)
    frame=frame[frame.season.between(2022,2026)&frame.situation.eq('all')&frame.playoffGame.eq(0)].copy()
    frame['date']=pd.to_datetime(frame.gameDate.astype(str),format='%Y%m%d').dt.strftime('%Y-%m-%d')
    frame=frame[frame.date.le(through)].rename(columns={'gameId':'game_id','opposingTeam':'opponent'})
    for c in ['team','opponent']:frame[c]=frame[c].replace({'T.B':'TBL','L.A':'LAK','S.J':'SJS','N.J':'NJD'})
    if frame.duplicated(['game_id','team']).any() or not frame.groupby('game_id').size().eq(2).all():raise ValueError('Invalid team pairs')
    if not frame.home_or_away.isin(['HOME','AWAY']).all():raise ValueError('Unknown home/away label')
    frame['is_home']=frame.home_or_away.eq('HOME').astype(int)
    if not np.isfinite(frame[RATE_COLUMNS]).all().all() or not frame[RATE_COLUMNS].ge(0).all().all():raise ValueError('Invalid counts/xG')
    bm=json.loads((boxscores/'metadata.json').read_text());rows=[];boxes={}
    if bm['through_eastern_date']!=through or bm['unfinished_games']:raise ValueError('Incomplete official cutoff')
    for source in bm['sources']:
        if not source['file'].startswith('boxscore_'):continue
        path=boxscores/source['file']
        if sha(path)!=source['sha256']:raise ValueError('Changed official source')
        b=json.loads(path.read_text())
        if b['gameState'] not in ['OFF','FINAL'] or b['season']!=20262027 or b['gameType']!=2:raise ValueError('Invalid official game')
        boxes[b['id']]=b
        goals={side:sum(p['goals'] for group in ['forwards','defense'] for p in b['playerByGameStats'][side][group]) for side in ['homeTeam','awayTeam']}
        for side,other in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            rows.append(dict(game_id=b['id'],date=b['gameDate'],season=2026,team=b[side]['abbrev'],opponent=b[other]['abbrev'],
                is_home=int(side=='homeTeam'),official_goals=goals[side],official_against=goals[other],official_sog=b[side]['sog'],official_sa=b[other]['sog']))
    official=pd.DataFrame(rows)
    current=official.merge(frame[frame.season.eq(2026)][['game_id','team',*RATE_COLUMNS,'shotsOnGoalFor','shotsOnGoalAgainst']],on=['game_id','team'],how='left',validate='one_to_one')
    current['source_matches']=current.goalsFor.eq(current.official_goals)&current.goalsAgainst.eq(current.official_against)&current.shotsOnGoalFor.eq(current.official_sog)&current.shotsOnGoalAgainst.eq(current.official_sa)
    bad=set(current.loc[~current.source_matches,'game_id'])
    audit=current.copy();current.loc[current.game_id.isin(bad),['xGoalsFor','xGoalsAgainst']]=np.nan
    current['goalsFor']=current.official_goals;current['goalsAgainst']=current.official_against
    current['shotsOnGoalFor']=current.official_sog;current['shotsOnGoalAgainst']=current.official_sa
    frame=pd.concat([frame[frame.season.lt(2026)],current],ignore_index=True)
    frame['actual']=frame.goalsFor
    return frame, audit, boxes


def build_features(history, fixtures, recent_games=20, prior_games=20):
    """Entire target date is excluded; current-season windows are per team.

    Fixtures require game_id, date, season, team, opponent, is_home. Historical
    xG quarantines preserve goal and schedule observations but not invalid xG.
    """
    if history.duplicated(['game_id','team']).any() or fixtures.duplicated(['game_id','team']).any():
        raise ValueError('Duplicate team-game identity')
    if recent_games<=0 or prior_games<=0:raise ValueError('Invalid prior/window')
    rows=[]
    for season,season_fixtures in fixtures.groupby('season'):
        previous=history[history.season.eq(season-1)]
        if previous.empty:raise ValueError('Previous-season prior is required')
        league=previous[RATE_COLUMNS].mean()
        priors=previous.groupby('team')[RATE_COLUMNS].mean()
        season_history=history[history.season.eq(season)].sort_values(['date','game_id'])
        for date,day in season_fixtures.groupby('date'):
            past=season_history[season_history.date.lt(date)]
            rates={};rest={};counts={}
            for team in set(day.team)|set(day.opponent):
                all_past=past[past.team.eq(team)];recent=all_past.tail(recent_games)
                prior=priors.loc[team].fillna(league) if team in priors.index else league
                rates[team]=(recent[RATE_COLUMNS].sum()+prior_games*prior)/(recent[RATE_COLUMNS].count()+prior_games)
                counts[team]=len(recent)
                rest[team]=min(7,(pd.Timestamp(date)-pd.Timestamp(all_past.date.max())).days) if len(all_past) else 7
            for f in day.itertuples():
                own,opp=rates[f.team],rates[f.opponent]
                baseline=(own.goalsFor+opp.goalsAgainst)/2
                if not baseline>0 or not np.isfinite([*own,*opp]).all():raise ValueError('Invalid lagged rates')
                rows.append(dict(game_id=f.game_id,date=date,season=season,team=f.team,opponent=f.opponent,is_home=int(f.is_home),
                    baseline=baseline,log_own_goal_rate=np.log(max(own.goalsFor,.01)),
                    log_opponent_goals_against=np.log(max(opp.goalsAgainst,.01)),
                    log_own_xg_rate=np.log(max(own.xGoalsFor,.01)),log_opponent_xg_against=np.log(max(opp.xGoalsAgainst,.01)),
                    own_back_to_back=int(rest[f.team]==1),opponent_back_to_back=int(rest[f.opponent]==1),
                    rest_advantage=(rest[f.team]-rest[f.opponent])/7,
                    own_recent_games=counts[f.team],opponent_recent_games=counts[f.opponent],
                    latest_input_date=past.date.max() if len(past) else previous.date.max()))
    return pd.DataFrame(rows)


def fit_poisson(frame, features, penalty=20):
    x=frame[features].to_numpy(float);y=frame.actual.to_numpy(float)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or (y<0).any():raise ValueError('Invalid training data')
    center=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-10]=1
    design=np.column_stack([np.ones(len(x)),(x-center)/scale])
    def objective(beta):
        eta=design@beta
        mu=np.exp(eta)
        value=np.sum(mu-y*eta)+penalty/2*np.sum(beta[1:]**2)
        gradient=design.T@(mu-y);gradient[1:]+=penalty*beta[1:]
        return value,gradient
    initial=np.zeros(design.shape[1]);initial[0]=np.log(max(y.mean(),.01))
    fit=minimize(objective,initial,jac=True,method='L-BFGS-B',options={'maxiter':1000,'ftol':1e-12})
    if not fit.success:raise ValueError('Poisson fit failed: '+fit.message)
    return dict(features=features,center=center.tolist(),scale=scale.tolist(),coefficients=fit.x.tolist(),
        penalty=penalty,training_rows=len(frame),training_games=int(frame.game_id.nunique()),
        training_through=str(frame.date.max()),converged=True)


def predict_goals(frame, model):
    x=frame[model['features']].to_numpy(float)
    if not np.isfinite(x).all():raise ValueError('Nonfinite prediction inputs')
    design=np.column_stack([np.ones(len(x)),(x-np.array(model['center']))/np.array(model['scale'])])
    means=np.exp(design@np.array(model['coefficients']))
    if not np.isfinite(means).all() or (means<=0).any() or (means>100).any():raise ValueError('Invalid goal prediction')
    return means
