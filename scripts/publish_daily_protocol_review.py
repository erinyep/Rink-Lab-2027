#!/usr/bin/env python3
"""Publish the October 20 no-refit review of frozen main and experimental forecasts."""
import argparse
from datetime import datetime,timezone
from html import escape
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest
from scripts.evaluate_october_9 import table
from scripts.publish_feature_evidence import accounting
from scripts.write_october_13_review import clustered_difference
from src.fantasy.feature_screen import paired_delta
from src.fantasy.per_game import require


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['evaluation','feature-evaluation','evidence','out']:ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args();require(not (a.out/'manifest.json').exists(),'Preserve completed review')
    em=verify_manifest_files(a.evaluation,[]);fm=verify_manifest_files(a.feature_evaluation,[]);evm=verify_manifest_files(a.evidence,[])
    require(fm['evidence_manifest_sha256']==digest(a.evidence/'manifest.json'),'Different frozen feature release')
    require(fm['actuals_manifest_sha256']==em['actuals_manifest_sha256'],'Different actual vintages')
    require(em['date']=='2026-10-20','This readout is specific to the first October 20 prospective slate')
    require(fm['target_date']==em['date'] and fm['unscored_games']==0,'Incomplete or mismatched experimental slate')
    bundle=Path(em['frozen_bundle']);require(digest(bundle/'manifest.json')==em['frozen_bundle_manifest_sha256'],'Changed main forecasts')
    pm=pd.read_csv(a.evaluation/'player_metrics.csv');tm=pd.read_csv(a.evaluation/'team_metrics.csv');fantasy=pd.read_csv(a.evaluation/'fantasy_player_metrics.csv')
    gm=pd.read_csv(a.evaluation/'goalie_metrics.csv');starts=pd.read_csv(a.evaluation/'goalie_starter_scores.csv')
    coverage=pd.read_csv(a.evaluation/'game_team_coverage.csv');source=pd.read_csv(a.evaluation/'source_hash_audit.csv')
    require(source.status.eq('verified').all(),'Source provenance exceptions need review')
    require(coverage.game_id.nunique()==em['games'],'Incomplete main slate')
    main=pd.read_csv(a.evaluation/'simulation_summary.csv');main=main[main.issue_timing.eq('pregame') & main.actual.notna()]
    shot=main[main.category.eq('shots')]
    uncertainty=pd.concat([clustered_difference(shot,'all_players'),clustered_difference(shot[shot.fantasy_team_name.notna()],'saved_fantasy_roster')],ignore_index=True)
    team=pd.read_csv(a.evaluation/'team_projected_vs_actual.csv');team=team[team.issue_timing.eq('pregame') & team.category.eq('shots')].copy()
    td=paired_delta(team,baseline='default')
    experimental=pd.read_csv(a.feature_evaluation/'scored_predictions.csv')
    check=experimental.merge(team[team.model.eq('default')][['game_id','team','actual']],on=['game_id','team'],validate='many_to_one')
    require(np.allclose(check.actual_shots,check.actual),'Experimental skater-sum SOG differs from official team SOG')
    require(set(zip(experimental.game_id,experimental.team))==set(zip(team.game_id,team.team)),'Different team populations')
    # Exact old-input sequential decomposition, evaluated on the common actual population.
    c,effects=accounting(bundle)
    c=c.merge(shot[shot.model.eq('default')][['game_id','player_id','actual']],on=['game_id','player_id'],validate='one_to_one')
    rows=[];previous=c.baseline_shots.copy()
    for effect in effects:
        current=previous+c[effect]
        c[effect+'_absolute_error_delta']=(current-c.actual).abs()-(previous-c.actual).abs()
        for scope,mask in [('all',pd.Series(True,index=c.index)),('D',c.position_group.eq('D')),('F',c.position_group.eq('F')),('fantasy',c.fantasy_team_name.notna())]:
            z=c[mask];delta=z[effect+'_absolute_error_delta'];counts=z.groupby('game_id').size();sums=z.assign(delta=delta).groupby('game_id').delta.sum()
            rng=np.random.default_rng(20261020);draws=rng.integers(0,len(sums),(20000,len(sums)));boot=sums.to_numpy()[draws].sum(axis=1)/counts.to_numpy()[draws].sum(axis=1)
            rows.append(dict(component=effect,scope=scope,rows=len(z),games=z.game_id.nunique(),mean_absolute_movement=z[effect].abs().mean(),mae_delta=delta.mean(),lower_95=np.quantile(boot,.025),upper_95=np.quantile(boot,.975)))
        previous=current
    components=pd.DataFrame(rows)
    goalie=pd.read_csv(a.evaluation/'goalie_projections.csv');goalie=goalie[goalie.issue_timing.eq('pregame') & goalie.actual_starter.eq(1) & goalie.eligible_for_conditional_count_scoring.eq(True)]
    gd=[]
    for cat in ['shots_against','saves','goals_against']:
        part=goalie[['game_id','team','model',cat+'_absolute_error']].rename(columns={cat+'_absolute_error':'absolute_error'})
        z=paired_delta(part,baseline='goalie_history_baseline');z['category']=cat;gd.append(z)
    gd=pd.concat(gd,ignore_index=True)
    playerwide=pd.read_csv(a.evaluation/'player_projections.csv');scored=playerwide[playerwide.actual_shots.notna()]
    owner=[]
    for (name,model),g in scored[scored.fantasy_team_name.notna()].groupby(['fantasy_team_name','model']):
        owner.append(dict(fantasy_team_name=name,model=model,players=len(g),games=g.game_id.nunique(),sog_mae=g.shots_absolute_error.mean(),sog_bias=(g.expected_shots_if_plays-g.actual_shots).mean()))
    starts_summary=starts.groupby('model').agg(team_games=('game_id','size'),brier=('brier_score','mean'),uniform_brier=('uniform_candidate_brier_score','mean'),starter_coverage=('actual_starter_in_candidates','mean')).reset_index()
    # Expose count calibration by saved expected-SOG bin, without fitting new probabilities.
    shot['forecast_bin']=pd.cut(shot.model_projection_if_plays,[0,1,2,3,np.inf],right=False).astype(str)
    calibration=shot.groupby(['model','forecast_bin']).agg(rows=('actual','size'),forecast_mean=('model_projection_if_plays','mean'),observed_mean=('actual','mean'),mae=('absolute_error','mean')).reset_index()
    a.out.mkdir(parents=True,exist_ok=True)
    files={'player_metrics':pm,'team_metrics':tm,'fantasy_metrics':fantasy,'goalie_metrics':gm,'player_paired_uncertainty':uncertainty,'team_paired_uncertainty':td,
           'goalie_paired_uncertainty':gd,'component_performance':components,'coverage':coverage,'fantasy_team_metrics':pd.DataFrame(owner),
           'goalie_starter_metrics':starts_summary,'sog_calibration_bins':calibration,
           'player_results':scored[['game_id','player_id','player_name','team','fantasy_team_name','model','selected_for_trial','expected_shots_if_plays','actual_shots','shots_absolute_error']],
           'team_results':team[['game_id','team','opponent','model','projection_mean','actual','signed_error','absolute_error']],
           'player_component_results':c[['game_id','player_id','player_name','team','fantasy_team_name','baseline_shots','actual']+effects+[e+'_absolute_error_delta' for e in effects]],
           'source_hash_audit':source}
    for name,frame in files.items():frame.to_csv(a.out/(name+'.csv'),index=False)
    short=['model','rows_scored','mae','bias','interval_p10_p90_coverage']
    pshots=pm[pm.category.eq('shots')];tshots=tm[tm.category.eq('shots')];fshots=fantasy[fantasy.category.eq('shots')]
    gs=gm[gm.population.eq('actual_starters')]
    feature_metrics=pd.read_csv(a.feature_evaluation/'metrics.csv');feature_ci=pd.read_csv(a.feature_evaluation/'paired_uncertainty.csv')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(15,5))
    for ax,title,data,metric in [(axes[0],'Individual SOG: 396 appearances',pshots,'mae'),(axes[1],'Main team SOG: 22 observations',tshots,'mae'),(axes[2],'New team trials: 22 observations',feature_metrics,'mae')]:
        z=data.sort_values(metric);ax.barh(z.model.str.replace('_',' '),z[metric],color='#087e83');ax.invert_yaxis();ax.set_title(title,fontsize=11);ax.set_xlabel('MAE (lower is better)')
    fig.tight_layout();fig.savefig(a.out/'model_results.png',dpi=150);plt.close(fig)
    brief=f'''# October 20 model results — first prospective feature test

All {em['games']} games final; 396 positive-TOI skater appearances, 83 saved fantasy-roster appearances and 22 actual goalie starts. Main and experimental forecasts were frozen before puck drop. Evaluation uses the same official actuals, identical available observations per model, unchanged coefficients and no outcome-based selection. All {len(source)} source checks verify; no provenance exceptions.

![Last night's results](model_results.png)

## What the new protocol found

The new defense trial improves its own control (team SOG MAE 5.792→5.344, about 7.7%); defense plus quality reaches 5.342. All paired 95% feature intervals still include zero. This first unseen slate reverses the earlier retrospective screen, rather than confirming a stable effect. The main opponent-shots model is better on this slate (4.775), so the new trials are not an upgrade over our existing team forecasts. The baselines differ; incremental feature gains are measured against the frozen research control, not assigned to the main player-based models.

Calibrated opponent context leads all-player SOG (1.037 vs default 1.051); the game-bootstrap difference is -0.014, 95% interval [-0.025,-0.005]. It improves 9/11 games. This small effect does not transfer to fantasy players: opponent-only leads that subset (1.388 vs default 1.395), while candidate and calibrated candidate are worse than default. Fantasy difference intervals all include zero. Multiple correlated comparisons and one slate are exploratory; no automatic promotion.

Goalie opponent context improves saves MAE 6.440→6.152 and GA MAE 0.913→0.890, but paired intervals include zero. Full-start forecasts are scored against actual starters with variable durations; 55–65-minute and relief populations remain separate in the download. Saves p10–p90 coverage is only 59.1% for both variants, showing the provisional intervals need work.

## Main individual and fantasy SOG

{table(pshots[short])}

Saved fantasy roster subset (ownership is frozen at issuance, not today's roster):

{table(fshots[short])}

[All nine player categories](player_metrics.csv) · [Paired player/fantasy differences](player_paired_uncertainty.csv) · [Results by fantasy team](fantasy_team_metrics.csv) · [Player outcomes](player_results.csv).

## Main team SOG

{table(tshots[short])}

[All six team categories](team_metrics.csv) · [Team paired differences](team_paired_uncertainty.csv) · [Each team's outcome](team_results.csv).

## New feature experiment — prospective October 20 only

{table(feature_metrics)}

Negative paired MAE delta versus the research bias control helps:

{table(feature_ci)}

All 22 experimental team actuals equal official NHL team SOG. No refitting took place in evaluation. The historical corrected-data screen and this genuinely future slate are kept separate; do not pool them as equivalent prospective observations. Source-vintage limitations from the original screen still apply to training, while tonight's frozen inputs and predictions are available for inspection.

[Scored experimental predictions](feature_trials/scored_predictions.csv) · [Frozen October 20 evidence](../feature_evidence_2026-10-20/README.md).

## Which existing components helped?

These are exact sequential reconstructions from saved pregame inputs: baseline → TOI → rate → calibration → matchup → count constraints. They are diagnostic accounting, not separately issued ablation models, causal importance, or stable player-specific importance. Negative error delta helps; intervals resample whole games with appearance weights. Order and interactions matter.

{table(components[components.scope.eq('all')])}

[Position and fantasy component results](component_performance.csv) · [Per-player contribution/outcome audit](player_component_results.csv). The rate update hurt aggregate SOG accuracy at this stage; calibration and matchup recovered some error. One game's outcome cannot establish whether an individual player's variable is predictive.

## Goalies and uncertainty

{table(gs[['model','category','rows_scored','mae','bias','interval_p10_p90_coverage']])}

[Paired goalie differences](goalie_paired_uncertainty.csv) · [Duration and relief subsets](goalie_metrics.csv).

{table(starts_summary)}

Starter Brier is summed multiclass squared error per team-game; lower is better. Uniform uses the same saved candidates. Both models share provisional starter probabilities, so this is one participation model, not two independent wins. All observed starters were represented.

## Coverage and decision

Every one of the 396 skaters who played had a forecast. Of 395 identified selected-lineup players, 369 played and 26 did not; 27 actual skaters were outside the identified selected lineup. Colorado also had one unidentified replacement slot. All 102 modeled nonparticipants remain unscored for conditional stat means, rather than becoming invented zero outcomes. Team totals retain the issued lineup scenario, not the postgame participant roster.

[Coverage by game/team](coverage.csv) · [SOG calibration bins](sog_calibration_bins.csv) · [Source audit](source_hash_audit.csv).

Retain defaults and challengers for now. Continue the same frozen feature definitions and control on future slates, improve near-puck-drop lineup and starter confirmation, and assess interval calibration. Evaluate SOG, other categories and goalie duration separately. Do not tune tonight's coefficients to this result and call the improvement prospective. No lineup, roster or market transactions were performed.
'''
    (a.out/'README.md').write_text(brief)
    # Standalone results page with searchable player/team audit tables.
    sections=[('Main player SOG',pshots[short]),('Saved fantasy-player SOG',fshots[short]),('Main team SOG',tshots[short]),('New feature trials',feature_metrics),('Feature uncertainty',feature_ci),('Main-model uncertainty',uncertainty),('Component performance',components),('Goalies',gs[['model','category','rows_scored','mae','bias']]),('Lineup coverage',coverage),('Player outcomes',files['player_results']),('Team outcomes',files['team_results'])]
    body=''.join('<h2>'+escape(name)+'</h2>'+frame.round(4).to_html(index=False,border=0) for name,frame in sections)
    links=' · '.join(f'<a href="{name}.csv">{escape(name.replace("_"," "))}</a>' for name in files)
    (a.out/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>October 20 model results</title><style>body{font:15px system-ui;margin:24px;color:#172c38}h1,h2{color:#087e83}p{max-width:1050px;line-height:1.6}main{overflow:auto}table{border-collapse:collapse;font-size:12px}td,th{padding:8px;border-bottom:1px solid #ddd;white-space:nowrap}img{max-width:100%}</style></head><body><h1>October 20 results · 11 final games</h1><p><a href="../evidence/">Frozen pregame evidence</a> · <a href="../games/">Saved matchups</a> · <a href="README.md">Full interpretation and methods</a></p><p><strong>New defense trials beat their own control, but not our best existing team model.</strong> D-only MAE 5.344 vs control 5.792; main opponent-shots MAE 4.775. New-feature intervals include no gain. Calibrated opponent context leads individual SOG, opponent-only leads the fantasy subset. No model promotion from one slate.</p><p>396 player appearances and 22 team observations scored on identical outcomes per model; no postgame refitting. All skaters who played and all starting goalies had forecast coverage, but 26 selected lineup players did not play. Main conditional means do not score nonparticipants as zero. Historical corrected-data tests remain separate.</p><p>'+links+'</p><img src="model_results.png" alt="Individual, main-team and experimental-team shot errors"><p><label>Find a player, team or model <input id="search" type="search"></label></p><main>'+body+'</main><script>document.getElementById("search").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script></body></html>')
    sources=[a.evaluation/'manifest.json',a.feature_evaluation/'manifest.json',a.evidence/'manifest.json',bundle/'manifest.json']
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),date=em['date'],games=em['games'],status='prospective_evaluation_no_refit_no_promotion',
        source_manifests={str(p):digest(p) for p in sources},code_sha256={str(Path(__file__).relative_to(ROOT)):digest(Path(__file__))},
        files={str(p.relative_to(a.out)):digest(p) for p in a.out.rglob('*') if p.is_file()}),indent=2)+'\n')
    print('Review:',a.out/'README.md')


if __name__=='__main__':main()
