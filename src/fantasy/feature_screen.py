"""Small chronological screening models; distinct from issued player forecasts."""
import numpy as np
import pandas as pd
from .per_game import require


def fit_residual(train, features, penalty=20):
    require(len(train)>0 and train.residual.notna().all(), 'No valid training targets')
    x=train[features].astype(float)
    center=x.mean().fillna(0)
    scale=x.std(ddof=0).replace(0,1).fillna(1)
    z=(x.fillna(center)-center)/scale
    y=train.residual.to_numpy(float)
    # Intercept is not penalized; only training moments enter imputation/scaling.
    beta=np.linalg.solve(z.T@z+penalty*np.eye(len(features)), z.T@(y-y.mean())) if features else np.array([])
    return dict(features=features,center=center.to_dict(),scale=scale.to_dict(),
                coefficients=dict(zip(features,beta)),intercept=float(y.mean()))


def apply_residual(frame, model):
    effects=pd.DataFrame(index=frame.index)
    for c in model['features']:
        effects[c]=(frame[c].fillna(model['center'][c])-model['center'][c])/model['scale'][c]*model['coefficients'][c]
    result=frame.baseline+model['intercept']+effects.sum(axis=1)
    return result.clip(lower=0),effects


def lagged_team_rows(team_games, target_fixtures, pbp, pbp_audit, quality, prior_games=20):
    """All historical features exclude the entire target date, including doubleheaders."""
    from .play_by_play import lagged_defense_context,lagged_shot_quality
    rows=[]
    for date, fixtures in target_fixtures.groupby('game_date'):
        past=team_games[team_games.game_date.lt(date)]
        league=float(past.shots.mean()) if len(past) else 30.
        d=lagged_defense_context(pbp,pbp_audit,date)
        q=lagged_shot_quality(quality,date)
        d=d[d.strength.eq('all')].set_index('team') if len(d) else pd.DataFrame()
        q=q[q.strength.eq('all')].set_index('team') if len(q) else pd.DataFrame()
        for f in fixtures.itertuples():
            own=past[past.team.eq(f.team)];opp=past[past.team.eq(f.opponent)]
            offense=(own.shots.sum()+prior_games*league)/(len(own)+prior_games)
            against=(opp.shots_against.sum()+prior_games*league)/(len(opp)+prior_games)
            row=dict(game_id=f.game_id,game_date=date,team=f.team,opponent=f.opponent,
                     baseline=(offense+against)/2,own_games=len(own),opponent_games=len(opp),
                     latest_input_date=past.game_date.max() if len(past) else None)
            for prefix,team in [('own',f.team),('opponent',f.opponent)]:
                for source,cols in [(d,['defense_attempt_share','followup_attempts_after_defense_per_game']),
                                    (q,['defense_xg_per_game','defense_expected_rebounds_per_game','team_xg_per_game'])]:
                    for c in cols: row[prefix+'_'+c]=float(source.loc[team,c]) if team in source.index else np.nan
                row[prefix+'_pbp_games']=int(d.loc[team,'games_used']) if team in d.index else 0
                row[prefix+'_quality_games']=int(q.loc[team,'games_used']) if team in q.index else 0
            rows.append(row)
    out=pd.DataFrame(rows)
    require(not out.duplicated(['game_id','team']).any(),'Duplicate feature row')
    return out


def paired_delta(frame, baseline='bias_control', draws=2000,seed=20261020):
    pivot=frame.pivot(index=['game_id','team'],columns='model',values='absolute_error')
    require(pivot.notna().all().all(),'Unequal screening populations')
    rng=np.random.default_rng(seed);rows=[]
    for model in pivot.columns:
        if model==baseline:continue
        delta=(pivot[model]-pivot[baseline]).groupby('game_id').mean()
        values=delta.to_numpy(); boots=rng.choice(values,size=(draws,len(values)),replace=True).mean(axis=1)
        rows.append(dict(model=model,comparison=baseline,games=len(values),mae_delta=values.mean(),
                         ci_low=np.quantile(boots,.025),ci_high=np.quantile(boots,.975)))
    return pd.DataFrame(rows)
