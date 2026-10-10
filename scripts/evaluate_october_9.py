#!/usr/bin/env python3
"""Score frozen October 9 artifacts; acquire published MoneyPuck team metrics.

Postgame xOnGoal/xGoals describe observed chances, never pregame inputs here.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import numpy as np
import pandas as pd

URL = 'https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv'
ROOT = Path('data/processed/forecasts')

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def table(x):
    x = x.round(3)
    lines = ['| '+' | '.join(map(str,x.columns))+' |',
             '| '+' | '.join(['---']*len(x.columns))+' |']
    lines += ['| '+' | '.join(map(str,row))+' |' for row in x.itertuples(index=False, name=None)]
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--actuals', type=Path, required=True)
    ap.add_argument('--boxscores', type=Path, required=True)
    ap.add_argument('--moneypuck-download', type=Path, help='Reuse a freshly downloaded published CSV')
    ap.add_argument('--moneypuck-snapshot', type=Path, help='Reuse an immutable acquisition snapshot')
    a = ap.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT/'october_9_review'
    manifest = json.loads((out/'manifest.json').read_text())
    assert 'evaluation' not in manifest, 'Restore the archived pre-evaluation view before re-evaluating'
    for file, h in manifest['files'].items():
        assert digest(out/file) == h, f'Consolidated hash mismatch: {file}'
    for source, h in manifest['source_manifest_sha256'].items():
        assert digest(Path(source)/'manifest.json') == h
        source_manifest = json.loads((Path(source)/'manifest.json').read_text())
        for file, source_hash in source_manifest['files'].items():
            assert digest(Path(source)/file) == source_hash
    am = json.loads((a.actuals/'manifest.json').read_text())
    for file, h in am['files'].items():
        assert digest(a.actuals/file) == h
    sk = pd.read_csv(a.actuals/'skater_game_stats.csv')
    gl = pd.read_csv(a.actuals/'goalie_game_stats.csv')
    ids = set(range(2026020066, 2026020070))
    assert set(sk.game_id) == ids and set(gl.game_id) == ids
    assert not sk.duplicated(['game_id','player_id']).any()
    assert not gl.duplicated(['game_id','player_id']).any()
    sk = sk[sk.toi_seconds > 0].copy()
    # Archive the convenience view before filling actuals; frozen sources stay intact.
    backup = ROOT/f'october_9_review_before_evaluation_{stamp}'
    shutil.copytree(out, backup)
    raw = a.moneypuck_snapshot
    if raw is None:
        raw = Path('data/raw/moneypuck/snapshots')/f'team_games_{stamp}'
        raw.mkdir(parents=True, exist_ok=False)
        if a.moneypuck_download:
            shutil.copyfile(a.moneypuck_download, raw/'all_teams.csv')
        else:
            urllib.request.urlretrieve(URL, raw/'all_teams.csv')
        (raw/'metadata.json').write_text(json.dumps(dict(url=URL,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            sha256=digest(raw/'all_teams.csv'),
            source='MoneyPuck published game-by-game team download',
            license='Non-commercial use with MoneyPuck attribution'), indent=2)+'\n')
    rm = json.loads((raw/'metadata.json').read_text())
    assert digest(raw/'all_teams.csv') == rm['sha256']
    cols = ['team','season','gameId','gameDate','situation','xOnGoalFor','xOnGoalAgainst',
            'xGoalsFor','xGoalsAgainst','shotsOnGoalFor','shotsOnGoalAgainst']
    mp = pd.read_csv(raw/'all_teams.csv', usecols=cols)
    mp = mp[(mp.season == 2026)&(mp.situation == 'all')&mp.gameId.isin(ids)].copy()
    assert len(mp) == 8 and not mp.duplicated(['gameId','team']).any()
    assert set(mp.gameDate) == {20261009}
    assert mp[cols[5:]].notna().all().all() and (mp[cols[5:]] >= 0).all().all()
    boxes = {gid: json.loads((a.boxscores/f'boxscore_{gid}.json').read_text()) for gid in ids}
    for gid, box in boxes.items():
        assert box['gameState'] in ['OFF','FINAL'] and box['gameType'] == 2
        for side, opp in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            r = mp[(mp.gameId == gid)&(mp.team == box[side]['abbrev'])].iloc[0]
            # Different feeds may omit or revise events. Retain discrepancies;
            # official boxscore SOG is the team outcome used for evaluation.
            mp.loc[(mp.gameId == gid)&(mp.team == box[side]['abbrev']), 'nhl_shots_for'] = box[side]['sog']
            mp.loc[(mp.gameId == gid)&(mp.team == box[side]['abbrev']), 'nhl_shots_against'] = box[opp]['sog']
            other = mp[(mp.gameId == gid)&(mp.team == box[opp]['abbrev'])].iloc[0]
            assert np.isclose(r.xOnGoalFor, other.xOnGoalAgainst)
            assert np.isclose(r.xGoalsFor, other.xGoalsAgainst)
    players = pd.read_csv(out/'simulation_summary.csv')
    actual = sk.melt(id_vars=['game_id','player_id','toi_minutes'],
        value_vars=['goals','assists','shots','hits','points','pp_points'],
        var_name='category', value_name='observed')
    players = players.drop(columns=['actual','absolute_error']).merge(actual,
        on=['game_id','player_id','category'], how='left', validate='many_to_one')
    players = players.rename(columns={'observed':'actual','toi_minutes':'actual_toi_minutes'})
    players['absolute_error'] = abs(players.model_projection_if_plays - players.actual)
    players['actual_status'] = np.where(players.actual.notna(), 'positive_toi_appearance',
        'no_positive_toi_appearance_not_scored')
    metrics = []
    scored = players[players.actual.notna()]
    for (model, category), g in scored.groupby(['model','category']):
        error = g.model_projection_if_plays - g.actual
        metrics.append(dict(model=model, category=category, appearances=len(g),
            predicted_total=g.model_projection_if_plays.sum(), actual_total=g.actual.sum(),
            mae=abs(error).mean(), bias=error.mean(), rmse=np.sqrt((error**2).mean()),
            interval_p10_p90_coverage=((g.actual >= g.simulation_p10)&(g.actual <= g.simulation_p90)).mean()))
    metrics = pd.DataFrame(metrics)
    teams = pd.read_csv(out/'team_projected_vs_actual.csv')
    totals = sk.groupby(['game_id','team']).sum(numeric_only=True)
    teams['actual'] = [totals.loc[(r.game_id,r.team),r.category] for r in teams.itertuples()]
    teams['actual_skater_sum'] = teams.actual
    mp_index = mp.set_index(['gameId','team'])
    for idx, r in teams[teams.category == 'shots'].iterrows():
        teams.at[idx,'actual'] = mp_index.loc[(r.game_id,r.team),'nhl_shots_for']
    teams['absolute_error'] = abs(teams.projection_mean - teams.actual)
    teams['exact_guess_correct'] = teams.whole_number_guess == teams.actual
    teams['actual_population'] = np.where(teams.category == 'shots', 'official_team_boxscore_sog', 'all_positive_toi_skaters_including_unmodeled')
    lookup = teams.set_index(['game_id','team','model','category','lineup_version'])
    teams['opponent_projection_mean'] = [lookup.loc[(r.game_id,r.opponent,r.model,r.category,r.lineup_version),'projection_mean'] for r in teams.itertuples()]
    for c in ['xOnGoalFor','xOnGoalAgainst','xGoalsFor','xGoalsAgainst']:
        teams['moneypuck_'+c] = [mp.set_index(['gameId','team']).loc[(r.game_id,r.team),c] for r in teams.itertuples()]
    teams['moneypuck_sog_for'] = [mp_index.loc[(r.game_id,r.team),'shotsOnGoalFor'] for r in teams.itertuples()]
    teams['moneypuck_sog_matches_nhl'] = [mp_index.loc[(r.game_id,r.team),'shotsOnGoalFor'] == mp_index.loc[(r.game_id,r.team),'nhl_shots_for'] for r in teams.itertuples()]
    goalies = pd.read_csv(out/'goalie_projected_vs_actual.csv')
    ga = gl.set_index(['game_id','player_id'])
    for col in ['shots_against','saves','goals_against','wins','gaa','save_percentage','starter','toi_seconds','count_identity_ok']:
        goalies['actual_'+col] = [ga.loc[(r.game_id,r.player_id),col] if (r.game_id,r.player_id) in ga.index else np.nan for r in goalies.itertuples()]
    goalies['eligible_for_conditional_count_scoring'] = (goalies.actual_toi_seconds > 0)&(goalies.actual_count_identity_ok == True)
    for c in ['shots_against','saves','goals_against']:
        goalies[c+'_absolute_error'] = abs(goalies[c+'_if_full_start'] - goalies['actual_'+c]).where(goalies.eligible_for_conditional_count_scoring)
    coverage = pd.read_csv(out/'game_team_coverage.csv')
    modeled = set(zip(players.game_id, players.player_id))
    coverage['actual_skaters'] = [len(sk[(sk.game_id == r.game_id)&(sk.team == r.team)]) for r in coverage.itertuples()]
    coverage['actual_skaters_with_forecast'] = [sum((r.game_id,p) in modeled for p in sk[(sk.game_id == r.game_id)&(sk.team == r.team)].player_id) for r in coverage.itertuples()]
    lineup = pd.read_csv(ROOT/'opponent_sog_trial_2026-10-09_20261009T225456Z/trial_lineup_audit.csv')
    selected = set(zip(lineup[lineup.selected_for_trial].game_id, lineup[lineup.selected_for_trial].player_id))
    coverage['refreshed_lineup_actual_overlap'] = [sum((r.game_id,p) in selected for p in sk[(sk.game_id == r.game_id)&(sk.team == r.team)].player_id) for r in coverage.itertuples()]
    for name, frame in [('simulation_summary',players),('team_projected_vs_actual',teams),('goalie_projected_vs_actual',goalies),('game_team_coverage',coverage)]:
        frame.to_csv(out/f'{name}.csv', index=False)
    manifest['evaluation'] = dict(evaluated_at_utc=datetime.now(timezone.utc).isoformat(),
        actuals=str(a.actuals), actuals_manifest_sha256=digest(a.actuals/'manifest.json'),
        pre_evaluation_archive=str(backup), moneypuck_snapshot=str(raw), moneypuck_sha256=rm['sha256'])
    manifest['note'] = 'Actuals filled from final NHL observations. MoneyPuck metrics are postgame descriptions, not frozen forecast inputs.'
    manifest['files'] = {p.name:digest(p) for p in out.glob('*.csv')}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    shots = teams[(teams.lineup_version == 'refreshed_injury_trial')&(teams.category == 'shots')]
    comparison = shots.pivot(index=['game_id','team','opponent','actual'], columns='model', values='projection_mean').reset_index()
    m = mp.rename(columns={'gameId':'game_id'})
    comparison = comparison.merge(m[['game_id','team','xOnGoalFor','xOnGoalAgainst','xGoalsFor','xGoalsAgainst']], on=['game_id','team'], validate='one_to_one')
    gm = goalies[goalies.eligible_for_conditional_count_scoring].groupby('model')[['shots_against_absolute_error','saves_absolute_error','goals_against_absolute_error']].mean().reset_index()
    starter_metrics = goalies[goalies.eligible_for_conditional_count_scoring & (goalies.actual_starter == True)].groupby('model')[['shots_against_absolute_error','saves_absolute_error','goals_against_absolute_error']].mean().reset_index()
    report = ['# October 9 postgame readout',
        '\nAll four final regular-season games, eight teams. Frozen means are unchanged. Refreshed-lineup team totals were derived after puck drop from frozen pregame inputs, not independently issued pregame forecasts.',
        f'\nConditional player comparison covers {scored[scored.model=="default"].player_id.groupby(scored[scored.model=="default"].game_id).nunique().sum()} modeled appearances out of {len(sk)} observed positive-TOI skaters. Unobserved roster members remain missing and are not scored as zero.',
        '\n## Player results', '\n'+table(metrics),
        '\n## Team shots and chance context', '\n'+table(comparison),
        '\nThe three model columns are pregame shot-on-goal expectations. xOnGoalFor/Against are MoneyPuck postgame chance-context measures: expected on-target outcomes of observed unblocked attempts, assuming average shooting talent. xGoalsFor/Against measure expected goals instead. They are not forecasts of the game that were available beforehand. Team shot outcomes use official NHL boxscores; player outcomes use individual NHL skater stats.',
        '\nMoneyPuck/NHL shot-feed audit (discrepancies retained):\n'+table(mp[['team','shotsOnGoalFor','nhl_shots_for','shotsOnGoalAgainst','nhl_shots_against']]),
        '\n## Goalies', '\n'+table(gm),
        '\nActual starters only (eight per model; includes shortened starts and overtime):\n'+table(starter_metrics),
        '\nErrors above cover positive-TOI, internally consistent goalie observations; backups are excluded from conditional count scoring. Full-60 projections are imperfect comparisons for partial starts, pulls and relief. Check actual_starter and actual_toi_seconds in the consolidated goalie table. Win probabilities remain provisional team-win proxies.',
        '\n## Coverage and lineup assumptions', '\n'+table(coverage[['team','actual_skaters','actual_skaters_with_forecast','refreshed_lineup_actual_overlap']]),
        '\n## Next decisions',
        '\nKeep the default baseline while accumulating chronological evidence. Compare the SOG trial on identical appearances and lineup versions; four games cannot validate an opponent model. Prioritize actual lineup/TOI prediction and rookie shrinkage before stronger opponent adjustments. Acquire historical MoneyPuck team game data for lagged, strength-specific shot volume and xOnGoal rates, with prior-season shrinkage and cutoff checks. Compare lagged raw SOG, unblocked attempts, xOnGoal and xGoals in held-out games before using any as a feature. Never use this game’s postgame chance metrics to predict this same game.',
        '\nMoneyPuck data: [published downloads](https://moneypuck.com/data.htm) and [data dictionary](https://peter-tanner.com/moneypuck/downloads/MoneyPuckDataDictionaryForPlayers.csv). Non-commercial research use; credit MoneyPuck.',
        f'\nSources: `{a.actuals}`, `{a.boxscores}`, `{raw}`. Convenience view: `data/processed/forecasts/october_9_review/`.',
        '\nReproduce after restoring the archived pre-evaluation convenience view:\n```sh\nrink-lab.venv/bin/python scripts/evaluate_october_9.py \\\n'+f'  --actuals {a.actuals} \\\n  --boxscores {a.boxscores} \\\n  --moneypuck-snapshot {raw}\n```']
    Path('outputs/per_game_forecast/october_9_results_readout.md').write_text('\n'.join(report)+'\n')
    print(table(metrics[metrics.category == 'shots']))
    print(table(comparison))

if __name__ == '__main__':
    main()
