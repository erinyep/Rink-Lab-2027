#!/usr/bin/env python3
"""Publish pregame attribution and an explicitly retrospective feature screen."""
import argparse
from datetime import datetime,timezone
import hashlib
from html import escape
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.fantasy.feature_screen import fit_residual,apply_residual,lagged_team_rows,paired_delta
from src.fantasy.diagnostics import shot_contributions
from src.fantasy.per_game import require
from scripts.evaluate_daily_forecasts import verify_manifest_files,verify_inputs
from scripts.evaluate_october_9 import table


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def accounting(bundle):
    m=verify_manifest_files(bundle,[])
    context=shot_contributions(pd.read_csv(bundle/'player_context.csv'),m['calibration']['factors']['shots']['multiplier'])
    if (bundle/'player_projections.csv').exists():
        projections=pd.read_csv(bundle/'player_projections.csv')
        usage=projections[projections.model.eq('usage_shot_context_trial')]
    else:
        summary=pd.read_csv(bundle/'simulation_summary.csv')
        usage=summary[summary.model.eq('usage_shot_context_trial') & summary.category.eq('shots')].rename(columns={'model_projection_if_plays':'expected_shots_if_plays'}).copy()
        # Older bundles lack flattened reader views. Selection is unused in historical player scoring.
        usage['selected_for_trial']=np.nan
    context=context.merge(usage[['game_id','player_id','expected_shots_if_plays','selected_for_trial']],on=['game_id','player_id'],validate='one_to_one')
    context['constraint_contribution']=context.expected_shots_if_plays-context.reconstructed_usage_shots
    effects=['toi_contribution','shot_rate_contribution','calibration_contribution','matchup_contribution','constraint_contribution']
    require(np.allclose(context.baseline_shots+context[effects].sum(axis=1),context.expected_shots_if_plays),'Player accounting mismatch')
    context['defense_pbp_contribution']=0.;context['new_shot_quality_contribution']=0.
    return context,effects


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','actuals','pbp','quality','out']:ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--config',type=Path,default=Path('config/pregame_feature_audit.json'))
    a=ap.parse_args();cfg=json.loads(a.config.read_text());require(not a.out.exists(),'Preserve earlier evidence releases; use new output')
    bm=verify_manifest_files(a.bundle,[]);verify_inputs(a.bundle,a.actuals,Path(bm['boxscore_history']))
    for p in [a.actuals,a.pbp,a.quality]:verify_manifest_files(p,[])
    require(bm['date']==cfg['target_date'],'Wrong bundle date')
    now=datetime.now(timezone.utc);player,effects=accounting(a.bundle)
    require(pd.to_datetime(player.start_time_utc,utc=True).min()>pd.Timestamp(now)+pd.Timedelta(minutes=10),'Too late for all-game experimental release')
    actual=pd.read_csv(a.actuals/'skater_game_stats.csv');require(not actual.duplicated(['game_id','player_id']).any(),'Duplicate actuals')
    actual=actual[actual.toi_seconds.gt(0)]
    teams=actual.groupby(['game_id','game_date','team']).shots.sum().reset_index()
    require(teams.groupby('game_id').size().eq(2).all(),'Incomplete actual teams')
    opponent=teams[['game_id','team','shots']].rename(columns={'team':'opponent','shots':'shots_against'})
    teams=teams.merge(opponent,on='game_id');teams=teams[teams.team.ne(teams.opponent)].reset_index(drop=True)
    require(teams.game_date.max()<cfg['target_date'],'Actual cutoff')
    pbp=pd.read_csv(a.pbp/'defense_team_games.csv');audit=pd.read_csv(a.pbp/'source_audit.csv')
    quality=pd.read_csv(a.quality/'defense_shot_quality_team_games.csv')
    fixtures=teams[['game_id','game_date','team','opponent']]
    features=lagged_team_rows(teams,fixtures,pbp,audit,quality,cfg['team_prior_games'])
    features=features.merge(teams[['game_id','team','shots']],on=['game_id','team'],validate='one_to_one')
    features['residual']=features.shots-features.baseline
    train=features[features.game_date.between(cfg['training_start'],cfg['training_end'])]
    test=features[features.game_date.between(cfg['holdout_start'],cfg['holdout_end'])]
    require(len(train)>0 and len(test)>0,'Empty split')
    require(train.game_date.max()<test.game_date.min(),'Split leakage')
    variants={'bias_control':[],'pbp_defense':cfg['pbp_features'],'shot_quality':cfg['quality_features'],
              'defense_and_quality':cfg['pbp_features']+cfg['quality_features']}
    fitted={};evaluations=[]
    for model,cols in {'trailing_baseline':[],**variants}.items():
        prediction=test.baseline.copy()
        if model!='trailing_baseline':
            fitted[model]=fit_residual(train,cols,cfg['ridge_penalty'])
            prediction,_=apply_residual(test,fitted[model])
        z=test[['game_id','game_date','team','opponent','shots']].copy();z['model']=model;z['prediction']=prediction
        z['absolute_error']=(z.prediction-z.shots).abs();z['error']=z.prediction-z.shots;evaluations.append(z)
    evaluated=pd.concat(evaluations,ignore_index=True)
    metrics=evaluated.groupby('model').agg(team_rows=('team','size'),games=('game_id','nunique'),mae=('absolute_error','mean'),bias=('error','mean')).reset_index()
    uncertainty=paired_delta(evaluated,draws=cfg['bootstrap_draws'],seed=cfg['seed'])
    # Freeze all variants for tonight; do not cherry-pick the holdout winner.
    tonight=pd.read_csv(a.bundle/'team_projections.csv');tonight=tonight[tonight.model.eq('default')]
    tf=tonight[['game_id','team','opponent']].copy();tf['game_date']=cfg['target_date']
    future=lagged_team_rows(teams,tf,pbp,audit,quality,cfg['team_prior_games'])
    future=future.merge(tonight[['game_id','team','start_time_utc']],on=['game_id','team'],validate='one_to_one')
    refit_train=features[features.game_date.between(cfg['training_start'],cfg['holdout_end'])]
    issued=[];refits={}
    for model,cols in variants.items():
        refits[model]=fit_residual(refit_train,cols,cfg['ridge_penalty']);pred,fx=apply_residual(future,refits[model])
        z=future.copy();z['model']=model;z['experimental_team_sog']=pred;z['intercept_contribution']=refits[model]['intercept']
        for c in cols:z[c+'_contribution']=fx[c]
        z['issued_at_utc']=now.isoformat();z['status']='separate_research_trial_not_used_by_main_forecasts';issued.append(z)
    trials=pd.concat(issued,ignore_index=True)
    # Existing saved player variants: exact sequential ablations on their issued cohort.
    season=json.loads(Path('outputs/per_game_forecast/season_through_2026-10-19/manifest.json').read_text())
    saved=[]
    for ev in season['evaluations']:
        em=verify_manifest_files(Path(ev),[]);old=Path(em['frozen_bundle'])
        require(sha(a.actuals/'manifest.json')==em['actuals_manifest_sha256'],'Different actual vintage')
        require(sha(old/'manifest.json')==em['frozen_bundle_manifest_sha256'],'Changed saved forecast')
        c,_=accounting(old)
        c=c[c.issue_timing.eq('pregame')].merge(actual[['game_id','player_id','shots']],on=['game_id','player_id'],validate='one_to_one')
        saved.append(c)
    saved=pd.concat(saved,ignore_index=True);require(not saved.duplicated(['game_id','player_id']).any(),'Overlapping saved cohorts')
    changes=[];pred=saved.baseline_shots.copy()
    for effect in effects:
        following=pred+saved[effect]
        saved[effect+'_error_delta']=(following-saved.shots).abs()-(pred-saved.shots).abs()
        for scope,mask in [('all',pd.Series(True,index=saved.index)),('D',saved.position_group.eq('D')),('F',saved.position_group.eq('F')),('fantasy',saved.fantasy_team_name.notna())]:
            z=saved[mask];error=z[effect+'_error_delta'];cluster=z.assign(delta=error).groupby('game_id').delta.mean()
            rng=np.random.default_rng(cfg['seed']);boot=rng.choice(cluster.to_numpy(),size=(cfg['bootstrap_draws'],len(cluster)),replace=True).mean(axis=1)
            changes.append(dict(component=effect,scope=scope,player_rows=len(z),games=z.game_id.nunique(),mean_absolute_movement=z[effect].abs().mean(),mae_delta=error.mean(),game_weighted_delta=cluster.mean(),ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975)))
        pred=following
    contribution_metrics=pd.DataFrame(changes)
    # Team accounting reconciles replacements rather than assigning their effects to named players.
    selected=player[player.selected_for_trial.eq(True)]
    tc=selected.groupby(['game_id','team'])[['baseline_shots']+effects].sum().reset_index()
    usage_team=pd.read_csv(a.bundle/'team_projections.csv');usage_team=usage_team[usage_team.model.eq('usage_shot_context_trial')]
    tc=tc.merge(usage_team[['game_id','team','expected_shots']],on=['game_id','team'],validate='one_to_one')
    tc['unidentified_replacement_mean']=tc.expected_shots-tc.baseline_shots-tc[effects].sum(axis=1)
    require(tc.unidentified_replacement_mean.ge(-1e-8).all(),'Unexplained team reconciliation')
    a.out.mkdir(parents=True)
    cols=['game_id','team','opponent','player_id','player_name','position_group','fantasy_team_name','injury_status','selected_for_trial','baseline_shots','expected_shots_if_plays']+effects+['largest_forecast_movement','defense_pbp_contribution','new_shot_quality_contribution']
    outputs={'player_contributions':player[cols],'team_contributions':tc,'component_performance':contribution_metrics,
             'historical_component_rows':saved[['game_id','date','team','player_id','player_name','shots','baseline_shots']+effects+[c+'_error_delta' for c in effects]],
             'historical_team_features':features,'heldout_predictions':evaluated,'heldout_metrics':metrics,'heldout_uncertainty':uncertainty,
             'tonight_experimental_team_forecasts':trials}
    for name,frame in outputs.items():frame.to_csv(a.out/(name+'.csv'),index=False)
    (a.out/'fitted_models.json').write_text(json.dumps(dict(heldout_training=fitted,tonight_refit=refits),indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    movement=selected[effects].abs().mean().sort_values();axes[0].barh(movement.index.str.replace('_contribution','').str.replace('_',' '),movement.values,color='#087e83');axes[0].set_title('Tonight: absolute player SOG movements');axes[0].set_xlabel('Mean absolute shots; sequential accounting')
    mm=metrics.sort_values('mae');axes[1].barh(mm.model,mm.mae,color='#087e83');axes[1].set_title('Retrospective team SOG holdout');axes[1].set_xlabel('MAE, October 13–19; lower is better')
    fig.tight_layout();fig.savefig(a.out/'feature_evidence.png',dpi=150);plt.close(fig)
    text=f'''# Feature evidence before October 20 games

Created {now.isoformat()}. Existing forecast bundle: {a.bundle.name}. Main forecasts are preserved; new team trials are issued separately before puck drop.

## Decision for tonight

The new features do not beat the bias control in this declared screen: control MAE {metrics.set_index('model').loc['bias_control','mae']:.3f}, D measures {metrics.set_index('model').loc['pbp_defense','mae']:.3f}, shot quality {metrics.set_index('model').loc['shot_quality','mae']:.3f}. All feature-gain intervals cross zero. Retain the current main models; test the new variants prospectively. This does not establish that the sources are useless or that other feature definitions cannot help.

In the 13-game saved player cohort, calibration is the clearest overall improvement among these ordered steps (MAE change -0.018 SOG); its fantasy-subgroup change is +0.022, so the overall benefit cannot be assumed for roster decisions. Recent shot-rate and matchup adjustments do not show a reliable overall gain. These results apply to SOG; goals, assists, fantasy categories and goalies need separate tests.

## What drives tonight's player forecasts?

![Forecast movement and held-out accuracy](feature_evidence.png)

[Per-player accounting](player_contributions.csv) and [per-team accounting](team_contributions.csv) reconcile the existing usage trial exactly. The order is default baseline → TOI → shot rate → calibration → matchup → count constraints. Values are changes in expected SOG relative to the existing baseline, not shares of the entire prediction. A component that moves a prediction most is not necessarily the component that improves accuracy. These interacting contributions depend on order; they are neither causal importance nor independent feature value. Defense PBP and new MoneyPuck shot-quality effects in the main forecasts remain zero. Team replacements are shown separately. Candidate changes shots by a common multiplier; it does not establish player-specific variable importance.

## Do those existing components help?

October 10/12 saved pregame contexts matched to positive-TOI actual appearances; the same rows are used for each stage. Negative MAE delta helps. Calibration was originally fitted on earlier October data, not on these rows. Intervals resample whole games (equal game weight); per-player MAE delta can differ from equal-game delta. These are retrospective component reconstructions from saved inputs, not separately issued ablation forecasts. Population is conditional on appearing and does not validate participation probabilities.

{table(contribution_metrics[contribution_metrics.scope.eq('all')])}

[Position and fantasy subgroups](component_performance.csv). Effects are ordered; change order and attribution can change. This small cohort cannot establish stable per-player predictive importance.

## Do the new data add team predictive value?

Train {cfg['training_start']}–{cfg['training_end']} ({train.game_id.nunique()} games, {len(train)} team rows); hold out {cfg['holdout_start']}–{cfg['holdout_end']} ({test.game_id.nunique()} games, {len(test)} team rows). Design fixed in configuration before this run: 20-game baseline shrinkage, ridge penalty 20, training-only standardization and missing-value imputation. The baseline averages own historical SOG and opponent historical SA, shrunk toward the past-only league average. All target-date events are excluded. The bias control fits only an intercept; feature models must beat it, not merely fix a baseline bias. No tuning/selection on this holdout.

{table(metrics)}

Paired game-bootstrap MAE deltas against bias control (negative helps; 95% exploratory intervals):

{table(uncertainty)}

D features: own D attempt share, own followup attempts per game, opponent D attempt share. Shot-quality features: own D xG, D expected rebounds and team xG per game. PBP/shot quality use quarantines from the source audits; all teams remain, missing values receive training means (zero standardized effect). [Feature rows and source sample sizes](historical_team_features.csv) retain coverage.

This is a retrospective corrected-data screen, not a prospective season backtest: October 20 downloads may contain later revisions, and model/source quarantine choices were made after results were available. There is no archived as-of history for the new inputs. The test is small, early-season and does not validate individual players, goals or goalies. No model promotion or winning-edge claim follows from this test alone.

## Tonight's frozen experiment

[Experimental team SOG forecasts](tonight_experimental_team_forecasts.csv) refit every declared variant on data through October 19. These are separate team-volume research forecasts, not adjustments to individual player forecasts or replacements for the published five models. All four variants are preserved, including controls; no holdout winner is silently selected. Main lineup-based team projections and this trailing-team baseline have different populations/assumptions. [Parameters](fitted_models.json) expose standardized coefficients and centering; coefficients are conditional on correlated inputs.

Tomorrow: score these frozen forecasts against official actuals on the same games, inspect coverage/position/fantasy stability, and accumulate unseen games before promotion. Use `scripts/evaluate_feature_evidence.py --evidence <this-directory> --actuals <refreshed-official-actuals> --out <new-evaluation-directory>` to score all frozen variants on identical completed games without refitting. Archive new PBP/shot-quality snapshots daily for actual as-of testing. Acquire shifts next for defensible D-pair and PP exposure. No passing/possession or causal creation claim is supported by standard PBP alone.
'''
    (a.out/'README.md').write_text(text)
    tables=''.join('<h2>'+escape(title)+'</h2>'+frame.round(4).to_html(index=False,border=0) for title,frame in [('Held-out team models',metrics),('Paired game uncertainty',uncertainty),('Existing component performance',contribution_metrics),('Tonight player accounting',player[cols]),('Tonight team accounting',tc)])
    links=' · '.join(f'<a href="{name}.csv">{escape(name.replace("_"," "))}</a>' for name in outputs)
    (a.out/'index.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>October 20 feature evidence</title><style>body{font:15px system-ui;margin:24px;color:#172c38}h1,h2{color:#087e83}table{border-collapse:collapse;font-size:12px}td,th{padding:8px;border-bottom:1px solid #ddd;white-space:nowrap}main{overflow:auto}img{max-width:100%}p{max-width:1000px;line-height:1.6}</style></head><body><h1>Feature evidence · October 20</h1><p><a href="../games/">Matchups</a> · <a href="../report/">Fantasy report</a> · <a href="README.md">Full methodology and limitations</a></p><p>What changes forecasts versus what improves held-out accuracy. New D/shot-quality trials are separate research forecasts, not changes to the five main models. Historical results use corrected current downloads, not archived issue-time vintages. Negative error deltas help; correlated contributions depend on order. No player-specific predictive importance or causal claim is established. The first screen finds no improvement from the new D/shot-quality inputs; main forecasts remain unchanged. Full results below.</p><label>Find a player, team or model <input id="search" type="search" placeholder="e.g. McKenna, COL, calibration"></label><p>'+links+'</p><img src="feature_evidence.png" alt="Forecast component movements and retrospective holdout accuracy"><main>'+tables+'</main><script>document.getElementById("search").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script></body></html>')
    manifest=dict(created_at_utc=now.isoformat(),target_date=cfg['target_date'],status='experimental_no_promotion',config=cfg,
        training_games=int(train.game_id.nunique()),holdout_games=int(test.game_id.nunique()),
        source_manifests={str(p/'manifest.json'):sha(p/'manifest.json') for p in [a.bundle,a.actuals,a.pbp,a.quality]},
        code_sha256={str(p.relative_to(ROOT) if p.is_absolute() else p):sha(p) for p in [Path(__file__),ROOT/'src/fantasy/feature_screen.py',ROOT/'src/fantasy/diagnostics.py',ROOT/'scripts/evaluate_feature_evidence.py',a.config]},
        files={p.name:sha(p) for p in a.out.iterdir() if p.is_file()})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(metrics.to_string(index=False));print(uncertainty.to_string(index=False));print(contribution_metrics[contribution_metrics.scope.eq('all')].to_string(index=False));print('Evidence:',a.out)


if __name__=='__main__':main()
