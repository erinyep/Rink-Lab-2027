"""Re-score canonical saved slates and test fixed past-only lineup rules."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import evaluate, verify_manifest_files, digest, summarize_errors
from scripts.write_october_13_review import clustered_difference
from scripts.evaluate_october_9 import table
from src.fantasy.participation_screen import rank_recent_lineup


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ['previous_review','additional_bundle','actuals','boxscores','out']:
        ap.add_argument('--'+key,type=Path,required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise ValueError('Preserve earlier screens')
    prev = verify_manifest_files(a.previous_review,[])
    bundles = [Path(json.loads((Path(e)/'manifest.json').read_text())['frozen_bundle']) for e in prev['evaluations']]+[a.additional_bundle]
    if len(set(bundles)) != len(bundles):
        raise ValueError('Duplicate bundles')
    actual = pd.read_csv(a.actuals/'skater_game_stats.csv').query('toi_seconds > 0')
    players, lineups, team_errors, evaluation_paths = [], [], [], []
    used = set()
    for bundle in bundles:
        m = verify_manifest_files(bundle,[])
        ev = evaluate(bundle,a.actuals,a.boxscores,Path('data/processed/forecasts'))
        evaluation_paths.append(str(ev))
        p = pd.read_csv(ev/'simulation_summary.csv')
        p = p[p.issue_timing.eq('pregame') & p.actual.notna() & p.category.eq('shots')].copy()
        ids = set(p.game_id)
        if ids & used:
            raise ValueError('Overlapping games')
        used |= ids
        players.append(p.assign(date=m['date']))
        history = pd.read_csv(Path(m['game_history'])/'skater_game_stats.csv')
        candidates = pd.read_csv(ev/'player_projections.csv').query("model == 'default' and issue_timing == 'pregame'")
        # Position was frozen in the original simulation, never inferred from today's roster.
        all_sim = pd.read_csv(bundle/'simulation_summary.csv')
        pos = all_sim[['game_id','player_id','position_group']].drop_duplicates()
        candidates = candidates.merge(pos,on=['game_id','player_id'],validate='one_to_one')
        totals = pd.read_csv(ev/'team_projections.csv').query("model == 'default'").set_index(['game_id','team'])
        for (gid,team), z in candidates.groupby(['game_id','team']):
            obs = actual[actual.game_id.eq(gid) & actual.team.eq(team)]
            actual_ids = set(obs.player_id)
            baseline = z.selected_for_trial.astype(bool)
            for variant in ['saved_lineup','recent_five','last_then_recent_five']:
                ranked = rank_recent_lineup(z,history,m['date'],last_game_first=variant=='last_then_recent_five')
                selected = baseline if variant == 'saved_lineup' else ranked.selected_recent
                hit = ranked.player_id.isin(actual_ids)
                audit = ranked.assign(date=m['date'],variant=variant,selected=selected,actual_played=hit)
                lineups.append(audit)
                row = dict(date=m['date'],game_id=gid,team=team,variant=variant,
                    selected=int(selected.sum()),nonparticipants=int((selected & ~hit).sum()),
                    missed_actual=int((~selected & hit).sum()),unmodeled_actual=len(actual_ids-set(z.player_id)),
                    swaps=int((selected!=baseline).sum()),missing_slots=18-int(selected.sum()))
                for cat in ['goals','shots']:
                    col='expected_'+cat+'_if_plays'
                    # Retain original unidentified-replacement contribution. Same injury
                    # exclusions and capacities guarantee unchanged number of open slots.
                    if selected.sum()!=baseline.sum():
                        raise ValueError('Changed lineup capacity requires explicit replacement model')
                    pred = totals.loc[(gid,team),'expected_'+cat] + z.loc[selected,col].sum()-z.loc[baseline,col].sum()
                    target = obs[cat].sum()
                    row.update({cat+'_prediction':pred,cat+'_actual':target,cat+'_error':abs(pred-target),cat+'_bias':pred-target})
                team_errors.append(row)
        print('Scored',m['date'],len(ids),'games',flush=True)
    p = pd.concat(players,ignore_index=True)
    metrics, intervals, sensitivity, dates, date_ci = [], [], [], [], []
    for label,z in [('all_players',p),('fantasy',p[p.fantasy_team_name.fillna('').str.strip().ne('')])]:
        metrics.append(summarize_errors(z,'model_projection_if_plays').assign(population=label))
        intervals.append(clustered_difference(z,label))
        for day,g in z.groupby('date'):
            dates.append(summarize_errors(g,'model_projection_if_plays').assign(population=label,date=day))
            sensitivity.append(summarize_errors(z[z.date.ne(day)],'model_projection_if_plays').assign(population=label,excluded_date=day))
        wide=z.pivot(index=['date','game_id','player_id'],columns='model',values='absolute_error')
        if wide.isna().any().any(): raise ValueError('Unequal model populations')
        d=wide.subtract(wide['default'],axis=0)
        sums=d.groupby(level='date').sum(); counts=d.groupby(level='date').size().to_numpy()
        rng=np.random.default_rng(20261028); draw=rng.integers(0,len(sums),(20000,len(sums)))
        boot=sums.to_numpy()[draw].sum(axis=1)/counts[draw].sum(axis=1)[:,None]
        date_ci.append(pd.DataFrame(dict(population=label,model=sums.columns,delta=d.mean().values,
            lower_95=np.quantile(boot,.025,axis=0),upper_95=np.quantile(boot,.975,axis=0))))
    t=pd.DataFrame(team_errors)
    grouped=t.groupby('variant').agg(team_games=('team','size'),nonparticipants=('nonparticipants','sum'),
        missed_actual=('missed_actual','sum'),unmodeled_actual=('unmodeled_actual','sum'),swaps=('swaps','sum'),
        goals_mae=('goals_error','mean'),goals_bias=('goals_bias','mean'),shots_mae=('shots_error','mean')).reset_index()
    bydate=t.groupby(['date','variant']).agg(nonparticipants=('nonparticipants','sum'),goals_mae=('goals_error','mean'),shots_mae=('shots_error','mean')).reset_index()
    pci=[]
    for cat in ['nonparticipants','goals_error','shots_error']:
        w=t.pivot(index=['game_id','team'],columns='variant',values=cat)
        d=w.subtract(w.saved_lineup,axis=0); sums=d.groupby(level='game_id').sum()
        rng=np.random.default_rng(20261028); draw=rng.integers(0,len(sums),(20000,len(sums)))
        boot=sums.to_numpy()[draw].mean(axis=1)/2
        pci.append(pd.DataFrame(dict(metric=cat,variant=sums.columns,delta_per_team=d.mean().values,
            lower_95=np.quantile(boot,.025,axis=0),upper_95=np.quantile(boot,.975,axis=0))))
    a.out.mkdir(parents=True)
    outputs=dict(shots_metrics=pd.concat(metrics),shots_game_uncertainty=pd.concat(intervals),shots_date_uncertainty=pd.concat(date_ci),
        shots_by_date=pd.concat(dates),shots_leave_one_date_out=pd.concat(sensitivity),participation_metrics=grouped,
        participation_by_date=bydate,participation_game_uncertainty=pd.concat(pci),participation_team_games=t,
        participation_player_audit=pd.concat(lineups,ignore_index=True))
    for name,frame in outputs.items(): frame.to_csv(a.out/(name+'.csv'),index=False)
    report=f'''# Shots and participation screen through October 27

{p.game_id.nunique()} disjoint games across {p.date.nunique()} saved dates; {len(p[p.model.eq('default')])} observed skater appearances.
All canonical bundles re-scored against one actuals vintage; no missing-date forecasts reconstructed.

## Shots

{table(outputs['shots_metrics'][['population','model','rows_scored','mae','bias']])}

{table(outputs['shots_game_uncertainty'])}

Date-cluster sensitivity (only six dates, exploratory):

{table(outputs['shots_date_uncertainty'])}

## Participation screen

{table(grouped)}

{table(bydate)}

{table(outputs['participation_game_uncertainty'])}

Two fixed last-five-team-game ranking rules, neither fitted nor tuned on outcomes. Preserve 12F/6D, saved injury exclusions,
candidate populations, baseline player means and unidentified replacement contributions. Use each issuance's saved history,
strictly before target date. Missing history retains the candidate. Injury labels are snapshots, not confirmed scratches.
These new rankings are retrospective development screens, not previously issued predictions or calibrated participation probabilities.
Actual positive-TOI appearances define participation. No unseen roster players added after outcomes. Unmodeled actuals stay visible.
Team errors assess lineup swaps only; player forecasts remain conditional on playing. Shot targets here sum skater SOG (goalie shots excluded).
Do not claim production improvement from this screen without a future frozen trial.

[Leave-one-date-out](shots_leave_one_date_out.csv) · [Every team](participation_team_games.csv) · [Every candidate](participation_player_audit.csv)
'''
    (a.out/'README.md').write_text(report)
    (a.out/'manifest.json').write_text(json.dumps(dict(actuals=str(a.actuals),actuals_sha256=digest(a.actuals/'manifest.json'),
        boxscores=str(a.boxscores),evaluations=evaluation_paths,bundles=[str(b) for b in bundles],
        source_manifest_hashes={str(b/'manifest.json'):digest(b/'manifest.json') for b in bundles},
        code_hashes={p:digest(p) for p in ['scripts/screen_shots_and_participation.py','src/fantasy/participation_screen.py']},
        files={p.name:digest(p) for p in a.out.iterdir()}),indent=2)+'\n')
    print(report)


if __name__=='__main__': main()
