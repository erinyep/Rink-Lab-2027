#!/usr/bin/env python3
"""Publish the first through-October-20 multi-date audit with explicit evidence tiers."""
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
from scripts.write_october_13_review import clustered_difference
from scripts.review_forecast_week import summarize
from src.fantasy.feature_screen import paired_delta
from src.fantasy.per_game import require


def aggregate_metrics(frame,keys):
    """Weighted aggregation of absolute errors; never average date-level MAEs equally."""
    rows=[]
    for key,z in frame.groupby(keys):
        if not isinstance(key,tuple):key=(key,)
        rows.append(dict(zip(keys,key),rows=int(z.rows.sum()),games=int(z.games.sum()),
            mae=np.average(z.mae,weights=z.rows),bias=np.average(z.bias,weights=z.rows)))
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--review',type=Path,required=True);a=ap.parse_args()
    m=verify_manifest_files(a.review,[]);require(m['through']=='2026-10-20','This interpretation is specific to the first through-October-20 multi-date audit');require(not (a.review/'multi_date.md').exists(),'Preserve completed extensions')
    dates=[];players=[];teams=[];goalies=[];provenance=[]
    for directory in m['evaluations']:
        root=Path(directory);em=verify_manifest_files(root,[])
        require(em['actuals_manifest_sha256']==m['actuals_sha256'],'Mixed actual vintages')
        require(digest(Path(em['frozen_bundle'])/'manifest.json')==em['frozen_bundle_manifest_sha256'],'Changed issued forecast')
        provenance.append(dict(date=em['date'],bundle=em['frozen_bundle'],manifest_sha256=em['frozen_bundle_manifest_sha256'],evaluation=directory))
        for name,level in [('player_metrics','player'),('fantasy_player_metrics','saved_fantasy_player'),('team_metrics','team'),('goalie_metrics','goalie')]:
            z=pd.read_csv(root/(name+'.csv'));z=z[z.issue_timing.eq('pregame')]
            if level=='goalie':z=z[z.population.eq('actual_starters')]
            z=z.rename(columns={'rows_scored':'rows','games_scored':'games'});z['date']=em['date'];z['level']=level;dates.append(z)
        p=pd.read_csv(root/'simulation_summary.csv');p=p[p.issue_timing.eq('pregame') & p.actual.notna()];players.append(p)
        t=pd.read_csv(root/'team_projected_vs_actual.csv');teams.append(t[t.issue_timing.eq('pregame') & t.actual.notna()])
        g=pd.read_csv(root/'goalie_projections.csv');goalies.append(g[g.issue_timing.eq('pregame') & g.actual_starter.eq(1) & g.eligible_for_conditional_count_scoring.eq(True)])
    p=pd.concat(players,ignore_index=True);t=pd.concat(teams,ignore_index=True);g=pd.concat(goalies,ignore_index=True);bydate=pd.concat(dates,ignore_index=True)
    require(not p.duplicated(['game_id','player_id','model','category']).any(),'Overlapping saved cohorts')
    shot=p[p.category.eq('shots')];fantasy=shot[shot.fantasy_team_name.fillna('').str.strip().ne('')]
    ci=[]
    for label,z in [('all_players',shot),('saved_fantasy_roster',fantasy)]:
        ci.append(clustered_difference(z,label).assign(scope='all_saved_dates'))
        for date,part in z.groupby('date'):ci.append(clustered_difference(part,label).assign(scope=date))
    intervals=pd.concat(ci,ignore_index=True)
    sensitivity=[]
    for excluded in sorted(shot.date.unique()):
        for level,z in [('player',shot),('saved_fantasy_player',fantasy)]:
            part=z[z.date.ne(excluded)];stats=summarize(part,['model'],'model_projection_if_plays','actual');stats['excluded_date']=excluded;stats['level']=level;sensitivity.append(stats)
    sensitivity=pd.concat(sensitivity,ignore_index=True)
    teamci=paired_delta(t[t.category.eq('shots')],baseline='default')
    goalieci=[]
    for cat in ['shots_against','saves','goals_against']:
        z=paired_delta(g[['game_id','team','model',cat+'_absolute_error']].rename(columns={cat+'_absolute_error':'absolute_error'}),baseline='goalie_history_baseline');z['category']=cat;goalieci.append(z)
    goalieci=pd.concat(goalieci,ignore_index=True)
    # October 17 export is a different evidence tier: team and goalie means only.
    published=pd.read_csv(a.review/'published_october_17_metrics.csv');published=published[published.scope.eq('publication_safe')].copy()
    published['cohort']='published_export_oct17'
    full=pd.read_csv(a.review/'model_metrics.csv');fullteam=full[full.level.eq('team')].copy();fullteam['cohort']='full_bundles_oct10_12_20'
    combined=aggregate_metrics(pd.concat([fullteam,published],ignore_index=True),['model','category'])
    pg=pd.read_csv(a.review/'published_october_17_goalie_metrics.csv');pg=pg[pg.scope.eq('publication_safe')]
    combined_goalies=aggregate_metrics(pd.concat([full[full.level.eq('goalie') & full.category.isin(['saves','goals_against'])],pg],ignore_index=True),['model','category'])
    coverage=pd.read_csv(a.review/'game_coverage.csv')
    # The saved exported IDs demonstrate 12 additional, disjoint games; no full player rows are invented.
    view=Path(m['published_outlook_source']['path']);vm=json.loads((view/'manifest.json').read_text());export=pd.read_csv(view/'team_predictions.csv')
    export=export[export.issue_timing.eq('pregame') & (pd.to_datetime(export.start_time_utc,utc=True)>pd.Timestamp(vm['view_created_utc']))]
    exportids=set(export.game_id);require(not exportids.intersection(set(t.game_id)),'Export overlaps restored daily games')
    coverage['published_export_team_goalie_only']=coverage.game_id.isin(exportids)
    daycoverage=coverage.groupby('date').agg(final_games=('game_id','nunique'),actual_appearances=('appearances','sum'),baseline_covered_appearances=('covered','sum'),full_daily_games=('daily_trial','sum'),published_team_goalie_games=('published_export_team_goalie_only','sum')).reset_index()
    outputs={'model_metrics_by_date':bydate,'paired_player_sog_by_date':intervals,'leave_one_date_out_sog':sensitivity,'pooled_team_sog_uncertainty':teamci,'pooled_goalie_uncertainty':goalieci,'combined_team_export_metrics':combined,'combined_goalie_export_metrics':combined_goalies,'coverage_by_date':daycoverage,'forecast_cohorts':pd.DataFrame(provenance),'game_coverage':coverage}
    for name,frame in outputs.items():frame.to_csv(a.review/(name+'.csv'),index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,level,title in [(axes[0],'player','All modeled player appearances'),(axes[1],'saved_fantasy_player','Saved fantasy-roster appearances')]:
        z=bydate[bydate.level.eq(level)&bydate.category.eq('shots')].pivot(index='date',columns='model',values='mae')
        for model in z:ax.plot(range(len(z)),z[model],marker='o',label=model.replace('_sog_trial','').replace('_shot_context_trial','').replace('_',' '))
        ax.set_xticks(range(len(z)),z.index,rotation=20);ax.set_ylabel('SOG mean absolute error');ax.set_title(title);ax.legend(fontsize=8)
    fig.suptitle('Three saved prospective slates — missing dates are not reconstructed');fig.tight_layout();fig.savefig(a.review/'multi_date_performance.png',dpi=150);plt.close(fig)
    headline=full[full.category.eq('shots')][['level','model','rows','games','mae','bias']]
    datehead=bydate[bydate.category.eq('shots')][['date','level','model','rows','games','mae','bias']]
    text=f'''# More than yesterday: saved-model performance through {m['through']}

The audit covers **151 official finals and 5,435 positive-TOI appearances**. Actual data availability does not imply forecast availability. We do not reconstruct forecasts on missing dates or select versions after seeing errors.

| Evidence tier | Coverage | What we can compare |
| --- | --- | --- |
| Saved season-rate baseline policy | 69 games, 2,422 appearances | All nine skater categories; latest saved pregame whole-game snapshot |
| Complete five-model daily forecasts | 24 games, 864 appearances on October 10, 12 and 20 | Same players per model; team totals, 179 saved fantasy appearances and 48 goalie starts |
| October 17 published export | 12 additional publication-safe games | Team and goalie means only; original full player bundle absent locally |
| Older October 9 issued trial | 4 games, 143 player appearances | Older default/candidate simulation and independent opponent trial, reported separately |
| New defense/shot-quality experiment | October 20 only, 11 games | First prospective test; no earlier frozen feature forecasts exist |

The baseline overlaps the comparative cohorts; do not add those game counts. Complete daily team evidence plus October 17 exports spans 36 distinct games. The new feature test is a subset of October 20, not additional games. Missing dates remain visible in [date coverage](coverage_by_date.csv) and [every game](game_coverage.csv). The October 17 raw bundle is required to expand the full-player sample further.

## Pooled complete daily models — 24 games

![Performance across saved dates](multi_date_performance.png)

{table(headline)}

Across 864 appearances, calibrated opponent SOG MAE is 1.042 versus default 1.058: paired change -0.0167, exploratory 95% interval [-0.0241,-0.0093], with lower total player absolute error in 20/24 games. Candidate is almost tied at 1.043 and improves 19/24 games. This is a small, repeatable improvement within the available all-player sample, not proof of a large fantasy benefit.

The fantasy subset reverses that conclusion: opponent-only 1.348, default 1.350, calibrated opponent 1.361, candidate 1.364. Main team SOG favors candidate (4.227 vs default 4.448) when pooled across all 24 games, unlike yesterday's opponent-only winner. Evaluate the intended population, rather than selecting yesterday's best model.

Goalie saves favor opponent context (4.959 vs 5.221 over 48 starts), while GA is essentially unchanged/slightly worse (1.093 vs 1.085). [Pooled goalie uncertainty](pooled_goalie_uncertainty.csv) keeps those targets separate.

These are three saved dates, not 24 independent daily replications. Players are clustered within games; bootstrap resamples games with appearance weights, and date-wide dependence can make these exploratory intervals optimistic. Model definitions/inputs evolve with issuance history, so the pooled table evaluates the saved forecasting policy, not one fixed fitted parameter vector. No promotion is automatic.

[All categories](model_metrics.csv) · [By date, all categories and interval coverage](model_metrics_by_date.csv) · [Paired all-player/fantasy differences](paired_player_sog_by_date.csv) · [Leave one saved date out](leave_one_date_out_sog.csv) · [Frozen sources](forecast_cohorts.csv).

## Date-by-date SOG

{table(datehead)}

No date is replaced by a postgame reconstruction, and no missing player outcome becomes zero. Same scored appearances per model within date; pooled MAEs weight appearances/observations, not dates equally. Main team errors retain issued lineup assumptions instead of substituting actual participants.

## Extra team-only evidence from October 17

The published view was created after one declared-pregame game had started. We use the more conservative 12-game publication-safe subset. Export hashes verify; full source/issuance provenance cannot be independently recovered from the absent bundle. Exact same-game roster names map goalie IDs; unresolved candidates remain unscored. Keep this tier visible.

Combined **36-game team** summaries (24 complete-bundle games plus 12 export-only games), weighted by team observations:

{table(combined[combined.category.eq('shots')])}

Combined goalie export evidence is separate in [saves/GA metrics](combined_goalie_export_metrics.csv). These broad summaries mix evidence tiers; the 24-game full-bundle table remains the primary comparison. No October 17 player or fantasy projections are invented. [October 17 audit](published_october_17.md).

## Older evidence and the new features

[Baseline metrics across 69 games](baseline_metrics.csv), [baseline errors by date](baseline_by_date.csv), [older October 9 default/candidate simulations](archived_issued_simulation_metrics.csv), [independent opponent trial](archived_opponent_metrics.csv), and [older goalie trial](archived_goalie_metrics.csv) are retained as separate cohorts. Their populations and input conventions differ; do not treat them as a five-model comparison.

The new D/shot-quality variants have **only 11 prospective games**, because they were first frozen on October 20. The [51-game corrected-data retrospective screen](../feature_evidence_2026-10-20/README.md) is additional research evidence, not 51 more prospective forecasts. [October 20 prospective results](../results_2026-10-20/README.md) show D measures beating their research control but trailing the best existing team model; uncertainty includes no gain.

Next: choose the target/category and fantasy population before promotion, continue frozen future comparisons, and improve lineup/starter confirmation. More historical actuals cannot recover forecasts that were never saved. No coefficients are refitted in this review.
'''
    (a.review/'multi_date.md').write_text(text)
    # Put the broader interpretation first while preserving the complete underlying audit.
    readme=a.review/'README.md';s=readme.read_text();s=s.replace('\n\n','\n\n[Start with the multi-date comparison](multi_date.md): 24 full-comparison games, plus 12 additional team/goalie export games. The new feature trial has only 11 prospective games.\n\n',1);readme.write_text(s)
    sections=[('Primary pooled daily models: 24 games',headline),('SOG by date',datehead),('All-player and fantasy paired uncertainty',intervals),('36-game team evidence (mixed tiers)',combined[combined.category.eq('shots')]),('Date coverage',daycoverage),('Leave-one-date-out sensitivity',sensitivity)]
    html=''.join('<h2>'+escape(title)+'</h2>'+frame.round(4).to_html(index=False,border=0) for title,frame in sections)
    (a.review/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Multi-date model performance</title><style>body{font:15px system-ui;margin:24px;color:#172c38}h1,h2{color:#087e83}p{max-width:1050px;line-height:1.6}main{overflow:auto}table{border-collapse:collapse;font-size:12px}td,th{padding:8px;border-bottom:1px solid #ddd;white-space:nowrap}img{max-width:100%}</style></head><body><h1>Model performance beyond one night</h1><p><a href="../results/">October 20 results</a> · <a href="multi_date.md">Full interpretation and methods</a> · <a href="model_metrics.csv">All categories</a> · <a href="model_metrics_by_date.csv">All categories by date</a></p><p>151 finals audited; 24 games have complete five-model player forecasts (October 10, 12 and 20), with 12 more publication-safe October 17 team/goalie exports. Calibrated opponent context improves all-player shots in 20/24 games, but does not improve the saved fantasy subset. New defense features have only 11 prospective games. Missing predictions are not reconstructed; evidence tiers stay separate.</p><img src="multi_date_performance.png" alt="Model errors across three saved dates"><main>'+html+'</main></body></html>')
    m['multi_date_extension']=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),full_dates=sorted(shot.date.unique().tolist()),daily_games=int(shot.game_id.nunique()),player_appearances=int(shot[shot.model.eq('default')].shape[0]),export_only_games=len(exportids),code_sha256=digest(Path(__file__)))
    m['files']={p.name:digest(p) for p in a.review.iterdir() if p.is_file() and p.name!='manifest.json'};(a.review/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print(headline.to_string(index=False));print('36-game team SOG:');print(combined[combined.category.eq('shots')].to_string(index=False));print('Expanded review:',a.review/'multi_date.md')


if __name__=='__main__':main()
