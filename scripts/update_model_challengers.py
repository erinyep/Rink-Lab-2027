"""Validate isolated TOI/PP challengers and past-only team calibration.

New player means are retrospective challengers, never recovered pregame issues.
Existing frozen forecasts and model-selection policies are not overwritten.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import digest, verify_manifest_files
from scripts.evaluate_october_9 import table
from src.fantasy.daily import validate_exposure_population
from src.fantasy.opportunity import historical_pp_prior, power_play_opportunity
from src.fantasy.probability_calibration import fit_probability_calibration, calibrated_probability, reliability_table
from src.fantasy.simulation import poisson_diagnostics
from src.fantasy.per_game import require


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['actuals','exposure','panel','out']:
        ap.add_argument('--'+key,type=Path,required=True)
    ap.add_argument('--target-date',required=True)
    a=ap.parse_args();require(not a.out.exists(),'Preserve previous reviews')
    am=verify_manifest_files(a.actuals,[])
    for source in am['sources']:
        for k in ['boxscore','landing']:
            require(digest(source[k])==source[k+'_sha256'],'Changed official source')
    em=json.loads((a.exposure.parent/'manifest.json').read_text())
    require(digest(a.exposure)==em['output_sha256'],'Changed exposure')
    panel=pd.read_csv(a.panel)
    sk=pd.read_csv(a.actuals/'skater_game_stats.csv');ex=pd.read_csv(a.exposure)
    require(not sk.duplicated(['game_id','player_id']).any(),'Duplicate actuals')
    validate_exposure_population(sk,ex)
    require(np.allclose(ex.ev_toi_seconds+ex.pp_toi_seconds+ex.sh_toi_seconds,ex.toi_seconds),'Exposure component mismatch')
    root=Path('outputs/per_game_forecast');cfg=json.loads(Path('config/daily_forecast_trial.json').read_text())
    sources={str(a.actuals/'manifest.json'):digest(a.actuals/'manifest.json'),
             str(a.exposure.parent/'manifest.json'):digest(a.exposure.parent/'manifest.json'),str(a.panel):digest(a.panel)}
    forecasts=[]
    for folder in sorted((root/'frozen').glob('daily_*')):
        manifest=verify_manifest_files(folder,[])
        if manifest['date']>=a.target_date:continue
        sources[str(folder/'manifest.json')]=digest(folder/'manifest.json')
        p=pd.read_csv(folder/'player_projections.csv')
        p=p[p.issue_timing.eq('pregame')]
        calibrated=p[p.model.eq('calibrated_opponent_sog_trial')]
        usage=p[p.model.eq('usage_shot_context_trial')][['game_id','player_id','expected_toi_minutes_if_plays']]
        base=calibrated.merge(usage,on=['game_id','player_id'],suffixes=('','_usage'),validate='one_to_one')
        base=base.merge(sk.loc[sk.toi_seconds.gt(0),['game_id','player_id','game_date','position','pp_points','toi_minutes']],on=['game_id','player_id'],validate='one_to_one')
        base=base.merge(ex[['game_id','player_id','pp_toi_seconds']],on=['game_id','player_id'],validate='one_to_one')
        require(base.game_date.eq(manifest['date']).all(),'Actual date differs')
        for r in base.itertuples():
            prior=historical_pp_prior(panel,r.player_id,'D' if r.position=='D' else 'F',20262027)
            pp=power_play_opportunity(sk,ex,r.player_id,r.game_date,prior['prior_pp_minutes'],
                prior['prior_pp_rate'],r.expected_toi_minutes_if_plays_usage,window=cfg['recent_window_games'],
                exposure_prior_games=cfg['pp_exposure_prior_games'],rate_prior_minutes=cfg['pp_rate_prior_minutes'])
            forecasts.append(dict(game_id=r.game_id,player_id=r.player_id,player_name=r.player_name,date=r.game_date,
                position=r.position,baseline_toi=r.expected_toi_minutes_if_plays,usage_toi=r.expected_toi_minutes_if_plays_usage,
                actual_toi=r.toi_minutes,baseline_pp_points=r.expected_pp_points_if_plays,
                opportunity_pp_points=min(pp['opportunity_pp_points'],r.expected_goals_if_plays+r.expected_assists_if_plays),
                actual_pp_points=r.pp_points,actual_pp_minutes=r.pp_toi_seconds/60,
                **prior,**{k:v for k,v in pp.items() if k!='opportunity_pp_points'}))
    f=pd.DataFrame(forecasts);require(not f.duplicated(['game_id','player_id']).any(),'Duplicate replay player')
    summaries=[]
    for label,z in [('all',f)]+list(f.groupby('date')):
        for category,actual,models in [('toi','actual_toi',['baseline_toi','usage_toi']),
            ('pp_points','actual_pp_points',['baseline_pp_points','opportunity_pp_points']),
            ('pp_minutes','actual_pp_minutes',['prior_pp_minutes','expected_pp_minutes'])]:
            for model in models:
                err=z[model]-z[actual]
                row=dict(date=label,category=category,model=model,rows=len(z),games=z.game_id.nunique(),
                    mae=err.abs().mean(),bias=err.mean(),predicted=z[model].sum(),actual=z[actual].sum())
                if category=='pp_points':row.update(poisson_diagnostics(z[actual].to_numpy(),z[model].to_numpy()))
                summaries.append(row)
    metrics=pd.DataFrame(summaries)
    # Only independently issued direct-team probabilities train this calibrator.
    probabilities=[]
    for folder in sorted(root.glob('team_context_daily_*')):
        manifest=json.loads((folder/'manifest.json').read_text());date=manifest['date']
        if date>=a.target_date:continue
        p=verify_manifest_files(folder,[])
        sources[str(folder/'manifest.json')]=digest(folder/'manifest.json')
        pred=pd.read_csv(folder/'team_win_probabilities.csv')
        for r in pred.itertuples():
            if r.game_id not in set(sk.game_id):continue
            source=next(s for s in am['sources'] if s['game_id']==r.game_id)
            box=json.loads(Path(source['boxscore']).read_text())
            require(box['gameDate']==date and box['homeTeam']['abbrev']==r.home and box['awayTeam']['abbrev']==r.away,'Fixture mismatch')
            require(pd.Timestamp(r.start_time_utc)-pd.Timestamp(r.issued_at_utc)>=pd.Timedelta(minutes=10),'Late probability')
            require(box['startTimeUTC']==r.start_time_utc,'Changed game start')
            require(r.training_through<date,'Team-model training leakage')
            probabilities.append(dict(game_id=r.game_id,date=date,probability=r.home_win_probability,
                actual_home_win=int(box['homeTeam']['score']>box['awayTeam']['score']),
                model_release_sha256=p['model_release_sha256']))
    probs=pd.DataFrame(probabilities);require(not probs.game_id.duplicated().any(),'Duplicate probability issuance')
    require(probs.model_release_sha256.nunique()==1,'Do not pool different raw-model versions')
    folds=[];scores=[]
    for date,z in probs.groupby('date',sort=True):
        fit=fit_probability_calibration(probs,date);folds.append(fit)
        calibrated=calibrated_probability(z.probability,fit,date)
        prior=probs[probs.date<date]
        home_rate=(prior.actual_home_win.sum()+1)/(len(prior)+2)
        for (index,r),cp in zip(z.iterrows(),calibrated):
            for model,p in [('raw',r.probability),('calibration_trial',cp),('past_home_rate',home_rate),('coin_flip',.5)]:
                scores.append(dict(game_id=r.game_id,date=date,model=model,probability=p,actual_home_win=r.actual_home_win,
                    brier=(p-r.actual_home_win)**2,log_loss=-np.log(np.clip(p if r.actual_home_win else 1-p,1e-12,1)),
                    training_games=fit['games'],calibration_status=fit['status']))
    scores=pd.DataFrame(scores)
    pm=scores.groupby('model').agg(games=('game_id','size'),brier=('brier','mean'),log_loss=('log_loss','mean')).reset_index()
    eligible=scores[scores.calibration_status.eq('fitted_experimental')]
    held=eligible.groupby('model').agg(games=('game_id','size'),brier=('brier','mean'),log_loss=('log_loss','mean')).reset_index()
    release=fit_probability_calibration(probs,a.target_date)
    release['raw_model_release_sha256']=str(probs.model_release_sha256.iloc[0])
    release['status_note']='Experimental challenger; raw probabilities remain the selected output. Rolling validation is retrospective.'
    a.out.mkdir(parents=True)
    for name,frame in [('player_challenger_rows',f),('player_metrics',metrics),('probability_training_rows',probs),
                       ('probability_walk_forward_scores',scores),('probability_metrics',pm),('probability_fitted_holdout_metrics',held)]:
        frame.to_csv(a.out/(name+'.csv'),index=False)
    reliability=[]
    for model,z in scores.groupby('model'):
        bins=reliability_table(z);bins['model']=model;reliability.append(bins)
    pd.concat(reliability,ignore_index=True).to_csv(a.out/'probability_reliability.csv',index=False)
    (a.out/'probability_calibration.json').write_text(json.dumps(release,indent=2)+'\n')
    (a.out/'probability_folds.json').write_text(json.dumps(folds,indent=2)+'\n')
    report=f'''# Model challengers — {a.target_date}

These changes implement isolated usage-aware TOI, power-play opportunity and team probability calibration. Existing five-model means, primary calibrated SOG and fantasy policies remain unchanged. Automatic refresh and participation modeling are deferred.

## Player workload and PP opportunity

Retrospective challenger reconstruction on {len(f)} matched positive-TOI player-games / {f.game_id.nunique()} games across {f.date.nunique()} saved release dates. Only dates before each target enter historical features; same-day outcomes cannot change their prediction. Priors use completed 2023-24 through 2025-26 seasons with fixed half-life weights. Recent PP minutes are shrunk with ten prior games; PP event rates with 120 prior minutes. No parameter was selected by minimizing these evaluation errors. The original usage TOI model and calibrated SOG are retained and exposed together as `usage_toi_only_trial`; `pp_opportunity_trial` additionally replaces PPP with expected PP minutes × shrunk PPP/minute, capped at expected G+A. Shots, goals and assists are not scaled by TOI. Replacements without identity retain position priors.

{table(metrics[metrics.date.eq('all')][['category','model','rows','mae','bias','predicted','actual']])}

PPP count negative log likelihood and probability-of-at-least-one Brier are in player_metrics.csv, along with zero-mean positive outcomes. Sparse categories require these proper scores in addition to MAE. Any zero-minute or missing exposure conflicts stop the run; nonparticipants are not assigned zero conditional production. This audit measures projected player PP minutes, not a fitted team power-play opportunity or opponent-penalty model. There are no confirmed PP-unit assignments.

## Probability calibration

Only frozen direct-team probabilities from the same fitted model release are used, with official final winner labels and verified issuance/start times. No player-sum probabilities or market prices train calibration. A ridge-logistic intercept/slope is shrunk toward identity (intercept 0, slope 1), with nonnegative slope. Until at least 30 games, four dates and five of each outcome exist on earlier dates, calibration is identity.

Full rolling comparison, including identity fallback folds:

{table(pm)}

Only games for which an earlier-date fitted calibrator was available:

{table(held)}

The next-date artifact uses {release['games']} earlier games / {release['dates']} dates through {release['training_through']}; intercept {release['intercept']:.5f}, slope {release['slope']:.5f}. Reliability bins retain their sample sizes and empty bins. The limited fitted holdout cannot justify a promotion. Raw probabilities remain selected; upcoming releases can save calibrated challenger probabilities separately. No retrospective output is called an issued pregame forecast, and no profitability is inferred.

## Files and validation

[Player rows](player_challenger_rows.csv) · [Player metrics by date](player_metrics.csv) · [Rolling probability scores](probability_walk_forward_scores.csv) · [Fitted-fold metrics](probability_fitted_holdout_metrics.csv) · [Reliability](probability_reliability.csv) · [Next-date calibration](probability_calibration.json).

All {sk.game_id.nunique()} official final games / {int(sk.toi_seconds.gt(0).sum())} positive-TOI skater rows reconcile with the refreshed exposure source. Official boxscore/scoring-summary G/A/PPP identities and source hashes were validated. Historical releases are untouched; reconstructed challengers use today's corrected actuals vintage and remain retrospective. This is a small recent player-model evaluation, not a whole-season or fantasy-roster validation.
'''
    (a.out/'README.md').write_text(report)
    (a.out/'manifest.json').write_text(json.dumps(dict(target_date=a.target_date,source_hashes=sources,
        config_sha256=digest('config/daily_forecast_trial.json'),code_sha256={str(p):digest(p) for p in [Path(__file__),
        Path('src/fantasy/opportunity.py'),Path('src/fantasy/probability_calibration.py')]},
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print(metrics[metrics.date.eq('all')].to_string(index=False))
    print(held.to_string(index=False));print('Challenger release:',a.out)


if __name__=='__main__':main()
