#!/usr/bin/env python3
"""Add a retrospective hybrid to the consolidated Oct 9 comparison.

All means/context use saved pregame inputs. Postgame observations score only.
No optimization uses October 9 outcomes. The hybrid was NOT issued pregame.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.fantasy.hybrid import hybrid_shots
from src.fantasy.simulation import simulate_counts
from scripts.evaluate_october_9 import table


def main():
    root = Path('data/processed/forecasts')
    out = root/'october_9_review'
    model = 'calibrated_opponent_sog_trial'
    m = json.loads((out/'manifest.json').read_text())
    for f, h in m['files'].items():
        assert hashlib.sha256((out/f).read_bytes()).hexdigest() == h
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = root/f'october_9_review_before_hybrid_{stamp}'
    shutil.copytree(out, archive)
    source = root/'opponent_sog_trial_2026-10-09_20261009T225456Z'
    for folder in [source,root/'per_game_20262027_20261009T195052Z',root/'simulation_2026-10-09_20261009T195119Z']:
        saved = json.loads((folder/'manifest.json').read_text())
        for f,h in saved['files'].items():
            assert hashlib.sha256((folder/f).read_bytes()).hexdigest() == h, f'Frozen source changed: {f}'
    ctx = pd.read_csv(source/'player_sog_forecasts.csv').set_index(['game_id','player_id'])
    factors = json.loads(Path('config/game_calibration_candidate.json').read_text())['factors']
    source_files = [source/'player_sog_forecasts.csv',Path('config/game_calibration_candidate.json')]
    players = pd.read_csv(out/'simulation_summary.csv')
    players = players[players.model != model].copy()
    hybrid = players[players.model == 'candidate'].copy()
    hybrid['model'] = model
    hybrid['forecast_issue_status'] = 'retrospective_new_model_not_issued_pregame'
    hybrid['source_model_issued_at_utc'] = np.nan
    hybrid['shot_rate_source'] = 'frozen_candidate'
    hybrid['context_input_status'] = 'not_applicable_to_category'
    for (gid, pid), g in hybrid.groupby(['game_id','player_id']):
        idx = g[g.category == 'shots'].index[0]
        c = ctx.loc[(gid,pid)] if (gid,pid) in ctx.index else None
        base = c.baseline_shots_if_plays if c is not None else np.nan
        factor = c.combined_factor if c is not None else np.nan
        # Candidate has a rate when the context join is missing: undo only its
        # fixed calibration and retain neutral context, rather than drop player.
        fallback = hybrid.at[idx,'model_projection_if_plays']/factors['shots']['multiplier']
        mean, status, context = hybrid_shots(base,factors['shots']['multiplier'],factor,fallback)
        hybrid.at[idx,'model_projection_if_plays'] = mean
        hybrid.at[idx,'shot_rate_source'] = status
        hybrid.at[idx,'context_input_status'] = context
        means = g.set_index('category').model_projection_if_plays.to_dict()
        means['shots'] = mean
        draws = simulate_counts(means, draws=10000, seed=20261009, key=f'{gid}:{pid}')
        for j, row in g.iterrows():
            values = draws[row.category]
            hybrid.at[j,'simulated_mean'] = values.mean()
            for col,q in [('simulation_p10',.1),('simulation_median',.5),('simulation_p90',.9)]:
                hybrid.at[j,col] = np.quantile(values,q,method='inverted_cdf')
            hybrid.at[j,'probability_at_least_one_if_plays'] = (values >= 1).mean()
    hybrid['absolute_error'] = abs(hybrid.model_projection_if_plays - hybrid.actual)
    # A missing roster player's SOG receives a past-position prior, without
    # guessing other categories, injury status, or appearance probability.
    prior_path = root/'per_game_20262027_20261009T195052Z/process_components_provisional.csv'
    prior = pd.read_csv(prior_path).groupby('position_group').position_prior_shots_per_game.first()
    source_files.append(prior_path)
    missing_path = root/'simulation_2026-10-09_20261009T195119Z/players_without_model_history.csv'
    source_files.append(missing_path)
    missing = pd.read_csv(missing_path)
    raw = Path('data/raw/nhl/snapshots/simulation_context_20261009T194825Z')
    extra = []
    for r in missing.itertuples():
        roster_path = raw/f'roster_{r.team}.json'; source_files.append(roster_path)
        roster = json.loads(roster_path.read_text())
        group = 'D' if any(p['id'] == r.player_id for p in roster['defensemen']) else 'F'
        factor = ctx[ctx.index.get_level_values('game_id') == r.game_id]
        factor = factor[factor.team == r.team].combined_factor.iloc[0]
        mean, status, context = hybrid_shots(np.nan,factors['shots']['multiplier'],factor,prior[group])
        row = hybrid[(hybrid.game_id == r.game_id)&(hybrid.team == r.team)&(hybrid.category == 'shots')].iloc[0].copy()
        row['player_id'] = r.player_id; row['player_name'] = r.player_name
        row['model_projection_if_plays'] = mean; row['shot_rate_source'] = status
        row['context_input_status'] = context
        for c in ['actual','absolute_error','actual_toi_minutes','injury_status_latest','injury_status_at_original_issue','excluded_from_trial_lineup']:
            row[c] = np.nan
        row['actual_status'] = 'no_positive_toi_appearance_not_scored'
        rng = np.random.default_rng(r.player_id)
        d = rng.poisson(mean,10000); row['simulated_mean'] = d.mean()
        for c,q in [('simulation_p10',.1),('simulation_median',.5),('simulation_p90',.9)]: row[c] = np.quantile(d,q,method='inverted_cdf')
        row['probability_at_least_one_if_plays'] = (d>=1).mean()
        extra.append(row)
    hybrid = pd.concat([hybrid,pd.DataFrame(extra)],ignore_index=True)
    players = pd.concat([players,hybrid],ignore_index=True)
    teams = pd.read_csv(out/'team_projected_vs_actual.csv')
    teams = teams[teams.model != model]
    ht = teams[(teams.model == 'candidate')&(teams.lineup_version == 'refreshed_injury_trial')].copy()
    ht['model'] = model; ht['derivation_status'] = 'retrospective_new_model_not_issued_pregame'
    selection = pd.read_csv(source/'trial_lineup_audit.csv')
    source_files.append(source/'trial_lineup_audit.csv')
    for (gid,team), lineup in selection[selection.selected_for_trial].groupby(['game_id','team']):
        ps = hybrid[(hybrid.game_id == gid)&hybrid.player_id.isin(lineup.player_id)]
        td = {}
        for pid,g in ps.groupby('player_id'):
            draws = simulate_counts(g.set_index('category').model_projection_if_plays.to_dict(),draws=10000,seed=20261009,key=f'{gid}:{pid}')
            for cat,d in draws.items(): td[cat] = td.get(cat,0)+d
        for cat,g in ps.groupby('category'):
            idx = ht[(ht.game_id == gid)&(ht.team == team)&(ht.category == cat)].index[0]
            mean = g.model_projection_if_plays.sum(); guess = max(0,int(np.ceil(mean))-1)
            ht.at[idx,'projection_mean'] = mean; ht.at[idx,'whole_number_guess'] = guess
            ht.at[idx,'probability_of_guess'] = (td[cat] == guess).mean()
            ht.at[idx,'simulation_p10'] = np.quantile(td[cat],.1,method='inverted_cdf')
            ht.at[idx,'simulation_p90'] = np.quantile(td[cat],.9,method='inverted_cdf')
    lookup = ht.set_index(['game_id','team','category'])
    ht['opponent_projection_mean'] = [lookup.loc[(r.game_id,r.opponent,r.category),'projection_mean'] for r in ht.itertuples()]
    ht['absolute_error'] = abs(ht.projection_mean - ht.actual)
    ht['exact_guess_correct'] = ht.whole_number_guess == ht.actual
    teams = pd.concat([teams,ht],ignore_index=True)
    players.to_csv(out/'simulation_summary.csv',index=False)
    teams.to_csv(out/'team_projected_vs_actual.csv',index=False)
    m['hybrid_trial'] = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),model=model,
        archive=str(archive),status='retrospective_exploratory_not_pregame',
        formula='baseline SOG * Oct6-7 calibration * frozen opponent/form factor',
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
        missing_history='SOG-only past-position prior; no inferred lineup participation',
        missing_context='neutral factor, explicitly flagged',
        feed_discrepancies='flags retained; no invented shots or postgame feature adjustment')
    m['files'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    metrics=[]
    for name,g in players[(players.category == 'shots')&players.actual.notna()].groupby('model'):
        t = teams[(teams.model == name)&(teams.category == 'shots')&(teams.lineup_version == 'refreshed_injury_trial')]
        metrics.append(dict(model=name,appearances=len(g),player_mae=g.absolute_error.mean(),player_rmse=np.sqrt(((g.model_projection_if_plays-g.actual)**2).mean()),team_mae=t.absolute_error.mean()))
    report = '\n## Fourth model: retrospective combined trial\n\n'+table(pd.DataFrame(metrics))+'\n\nThe hybrid combines fixed October 6–7 shot/assist calibration with the frozen opponent/form SOG factor. Other categories follow candidate. It is exploratory after observing October 9, not an issued pregame success. Missing context falls back to a flagged neutral factor. Jake O’Brien now has a SOG-only past-position prior; he is not assumed to play. Damon Severson was absent from the saved NHL roster context and remains an uncovered actual appearance; adding him using the postgame lineup would misstate pregame coverage. Source shot-feed discrepancies remain flagged, without manufactured corrections.\n'
    p=Path('outputs/per_game_forecast/october_9_results_readout.md')
    text=p.read_text().split('\n## Fourth model: retrospective combined trial')[0]
    p.write_text(text+report)
    print(table(pd.DataFrame(metrics)))

if __name__ == '__main__':
    main()
