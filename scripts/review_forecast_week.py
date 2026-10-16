#!/usr/bin/env python3
"""Publish a date-bounded review without reconstructing unissued predictions.

Run after acquire_current_game_history.py and complete_fantasy_game_stats.py.
All published CSVs are compact diagnostics; full acquired data stay ignored.
"""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import CATEGORIES, digest, verify_manifest_files
from scripts.evaluate_october_9 import table
from src.fantasy.diagnostics import defense_opportunity, shot_contributions
from src.fantasy.per_game import require


def summarize(frame, groups, pred, actual):
    rows = []
    for key, g in frame.dropna(subset=[pred, actual]).groupby(groups):
        if not isinstance(key, tuple):
            key = (key,)
        e = g[pred] - g[actual]
        rows.append(dict(zip(groups, key), rows=len(g), games=g.game_id.nunique(),
            predicted_total=g[pred].sum(), actual_total=g[actual].sum(),
            mae=e.abs().mean(), bias=e.mean(), rmse=np.sqrt(e.pow(2).mean())))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--start', type=date.fromisoformat, required=True)
    ap.add_argument('--end', type=date.fromisoformat, required=True)
    ap.add_argument('--actuals', type=Path, required=True)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--evaluations', type=Path, nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    require(a.start <= a.end, 'Reversed date interval')
    require(not a.out.exists(), 'Use a new output directory; preserve published reviews')
    audit = []
    am = verify_manifest_files(a.actuals, audit)
    fm = verify_manifest_files(a.baseline, audit)
    for s in am['sources']:
        for kind in ['boxscore', 'landing']:
            require(digest(s[kind]) == s[kind+'_sha256'], 'Changed actual source')
    actual = pd.read_csv(a.actuals/'skater_game_stats.csv')
    require(not actual.duplicated(['game_id', 'player_id']).any(), 'Duplicate actual')
    require(actual[CATEGORIES].notna().all().all(), 'Missing actual categories')
    require((actual.points == actual.goals+actual.assists).all(), 'Invalid points')
    week = actual[actual.game_date.between(str(a.start), str(a.end)) & actual.toi_seconds.gt(0)].copy()
    require(not week.empty, 'No final appearances in requested period')
    f = pd.read_csv(a.baseline/'scheduled_skater_game_forecasts.csv')
    f = f[f.player_id.notna()].sort_values('pool', ascending=False).drop_duplicates(['game_id', 'player_id'])
    require((pd.to_datetime(f.start_time_utc, utc=True) > pd.Timestamp(fm['created_at_utc'])).all(), 'Late baseline')
    means = [c+'_if_plays' for c in CATEGORIES]
    b = week.merge(f[['game_id', 'player_id', 'pool', 'fantasy_team_name']+means], how='left',
                   on=['game_id', 'player_id'], validate='one_to_one')
    coverage = b.groupby('game_date').agg(final_games=('game_id', 'nunique'),
        appearances=('player_id', 'size'), baseline_covered=('shots_if_plays', 'count')).reset_index()
    coverage['baseline_missing'] = coverage.appearances-coverage.baseline_covered
    baseline_rows = []
    for c in CATEGORIES:
        t = summarize(b, ['game_date'], c+'_if_plays', c)
        t['category'] = c
        baseline_rows.append(t)
    baseline_metrics = pd.concat(baseline_rows, ignore_index=True)
    ps, ts, gs, contexts = [], [], [], []
    for ev in a.evaluations:
        em = verify_manifest_files(ev, audit)
        require(em['actuals_manifest_sha256'] == digest(a.actuals/'manifest.json'),
                'Re-evaluate frozen bundles against the supplied refreshed actuals first')
        bundle = Path(em['frozen_bundle'])
        require(digest(bundle/'manifest.json') == em['frozen_bundle_manifest_sha256'], 'Changed issued manifest')
        bm = verify_manifest_files(bundle, audit)
        # Evaluations already distinguish late games and conditional appearances.
        p = pd.read_csv(ev/'simulation_summary.csv')
        p = p[p.issue_timing.eq('pregame') & p.actual.notna()]
        t = pd.read_csv(ev/'team_projected_vs_actual.csv')
        t = t[t.issue_timing.eq('pregame') & t.actual.notna()]
        g = pd.read_csv(ev/'goalie_projections.csv')
        g = g[g.issue_timing.eq('pregame') & g.eligible_for_conditional_count_scoring.eq(True)]
        ps.append(p); ts.append(t); gs.append(g)
        ctx = pd.read_csv(bundle/'player_context.csv')
        ctx = ctx[ctx.issue_timing.eq('pregame')]
        ctx = shot_contributions(ctx, bm['calibration']['factors']['shots']['multiplier'])
        check = p[p.category.eq('shots') & p.model.eq('usage_shot_context_trial')]
        ctx = ctx.merge(check[['game_id', 'player_id', 'model_projection_if_plays', 'actual']],
                        on=['game_id', 'player_id'], validate='one_to_one')
        ctx['constraint_residual'] = ctx.model_projection_if_plays-ctx.reconstructed_usage_shots
        require(ctx.constraint_residual.ge(-1e-9).all(), 'Unexpected reconstruction difference')
        contexts.append(ctx)
    p = pd.concat(ps); t = pd.concat(ts); g = pd.concat(gs)
    require(not p.duplicated(['game_id', 'player_id', 'category', 'model']).any(), 'Overlapping evaluations')
    metrics = []
    for scope, lo, hi in [('this_week', str(a.start), str(a.end)), ('available_prospective', '0000', str(a.end))]:
        for level, data, pred in [('player', p, 'model_projection_if_plays'), ('team', t, 'projection_mean')]:
            z = summarize(data[data.date.between(lo, hi)], ['model', 'category'], pred, 'actual')
            z['scope'] = scope; z['level'] = level; metrics.append(z)
        for c in ['saves', 'shots_against', 'goals_against']:
            z = summarize(g[g.date.between(lo, hi)], ['model'], c+'_if_full_start', 'actual_'+c)
            z['category'] = c; z['scope'] = scope; z['level'] = 'goalie'; metrics.append(z)
    metrics = pd.concat(metrics, ignore_index=True)
    ctx = pd.concat(contexts)
    effects = ['toi_contribution', 'shot_rate_contribution', 'calibration_contribution', 'matchup_contribution']
    previous = ctx.baseline_shots.copy()
    error_effects = []
    for effect in effects+['constraint_residual']:
        current = previous+ctx[effect]
        column = effect+'_absolute_error_delta'
        ctx[column] = (current-ctx.actual).abs()-(previous-ctx.actual).abs()
        error_effects.append(column)
        previous = current
    player_cols = ['date', 'game_id', 'team', 'player_id', 'player_name', 'fantasy_team_name',
        'baseline_shots', 'model_projection_if_plays', 'actual']+effects+['constraint_residual', 'largest_forecast_movement']+error_effects
    team_effects = ctx.groupby(['date', 'game_id', 'team'])[effects+['constraint_residual']+error_effects].sum().reset_index()
    defense = defense_opportunity(actual, str(a.end+timedelta(days=1)))
    # All final games are visible even when a forecast was never issued.
    coverage['daily_trial_games'] = coverage.game_date.map(p.groupby('date').game_id.nunique()).fillna(0).astype(int)
    a.out.mkdir(parents=True)
    for name, frame in [('coverage', coverage), ('baseline_metrics', baseline_metrics),
            ('model_metrics', metrics), ('player_contributions', ctx[player_cols]),
            ('team_contributions', team_effects), ('defense_opportunity', defense)]:
        frame.to_csv(a.out/(name+'.csv'), index=False)
    # Stable matplotlib figures use the existing project stack.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, level in zip(axes, ['player', 'team']):
        z = metrics[(metrics.scope=='available_prospective') & (metrics.level==level) & (metrics.category=='shots')].sort_values('mae')
        ax.barh(z.model, z.mae, color='#246b88'); ax.invert_yaxis()
        ax.set_xlabel('SOG mean absolute error (lower is better)'); ax.set_title(level.title()+' — issued prospective games')
    fig.tight_layout(); fig.savefig(a.out/'model_accuracy.png', dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 6))
    z = defense.sort_values('defense_shots_per_game')
    ax.barh(z.team, z.defense_shots_per_game, color='#246b88')
    ax.set(xlabel='Defensemen SOG per team game, all strengths', title=f'Descriptive opportunity proxy through {a.end}')
    fig.tight_layout(); fig.savefig(a.out/'defense_opportunity.png', dpi=150); plt.close(fig)
    shot = metrics[(metrics.scope=='this_week') & (metrics.category=='shots')]
    pooled = metrics[(metrics.scope=='available_prospective') & (metrics.category=='shots')]
    goalie = metrics[(metrics.scope=='this_week') & (metrics.level=='goalie')]
    baseline_shots = baseline_metrics[baseline_metrics.category.eq('shots')]
    movement = ctx[effects].abs().mean().sort_values(ascending=False).rename('mean_absolute_shot_movement').reset_index()
    movement.columns = ['component', 'mean_absolute_shot_movement']
    text = [f'# Forecast review: {a.start} through {a.end}',
        '\nCompleted games in the requested date range; later dates are excluded. No missing forecasts were reconstructed. '
        f'Prospective trial dates this week: {", ".join(sorted(set(p.loc[p.date.between(str(a.start),str(a.end)), "date"])))}. '
        f'Older default forecasts were issued {fm["created_at_utc"]}. '
        'Missing predictions are coverage failures, not zero predictions.',
        '\n## Coverage\n\n'+table(coverage),
        '\n## This week: every evaluated model\n\n'+table(shot[['level','model','rows','games','mae','bias']]),
        '\nThe two-game trial is too small to promote a model. All nine skater/team categories, RMSE, totals and bias '
        'are in [model metrics](model_metrics.csv). Team metrics use issued lineup scenarios; player metrics condition on positive-TOI appearances.',
        '\n### Older default, by date\n\n'+table(baseline_shots[['game_date','rows','games','mae','bias','predicted_total','actual_total']]),
        '\nThese matched-player sums select participants after the game; they are not pregame team forecasts. '
        'Ownership and injury labels retain their original snapshot dates. Refreshed official actuals can differ from '
        'archived readouts because of source corrections; forecasts are unchanged.',
        '\n### Goalies this week\n\n'+table(goalie[['model','category','rows','games','mae','bias']]),
        '\nFull-start forecasts are compared only with eligible actual starters. Relief, pulls, empty-net time and uncertain starters limit interpretation.',
        '\n## Broader prospective evidence\n\n'+table(pooled[['level','model','rows','games','mae','bias']]),
        '\nKeep default as baseline and candidate as challenger. The prior October 13 readout contains the paired game-bootstrap '
        'and fantasy subgroup reversal; the new days do not add prospective challenger evidence. '
        'Do not tune on these outcomes and report the result as unseen performance.',
        '\n## Which inputs move forecasts?\n\n'+table(movement),
        '\n[Per-player accounting](player_contributions.csv) and [team accounting](team_contributions.csv) '
        'show signed SOG changes for every scored player in the October 10/12 trials. Order: baseline → TOI → shot rate '
        '→ calibration → matchup. Contributions sum exactly to the usage model minus baseline, with a separate feasibility residual. '
        'The decomposition depends on order and measures movement, not causal importance or validated predictive value. '
        'The absolute_error_delta columns show realized sequential changes: negative improves player error, positive worsens it. '
        'Team rows sum these player error changes, not team-total absolute errors. '
        'Team sums here condition on actual participants and are diagnostics.',
        '\nPP/EV usage, rest, home/away and ESPN benchmarks were saved as context but have no fitted coefficients. '
        'The default uses historical/current production; the candidate adds fixed shot/assist calibration. '
        'Opponent and combined variants add team context; usage replaces the SOG rate/exposure and blends raw SOG/xOnGoal context. '
        'Current model comparisons confound inputs: isolate TOI-only, rate-only, matchup-only and D-context-only variants on future games.',
        '\n## Defense-created opportunity\n\n![Defense shot proxy](defense_opportunity.png)',
        '\n[All 32 team inputs](defense_opportunity.csv): D shots/game, D share of team shots, D assist credits/game, '
        'and D shots per 60 summed defense-player minutes, with sample sizes and latest dates. '
        'This uses all final regular-season games before the stated cutoff, not just this week. '
        'It measures defensemen’s direct production, not offensive sequences created, distinct assisted chances, pair effects or on-ice xG. '
        'No TOI threshold beyond positive participation is imposed. No forecast coefficient has been fitted. '
        'Future daily builds now export the same context using strictly pre-target-date history.',
        '\n## Accuracy visual\n\n![Model accuracy](model_accuracy.png)',
        '\n## Next steps\n\n1. Issue complete daily bundles before each game: fresh injuries, current source cutoffs, official game IDs, '
        'hashes and lineup coverage; finish the date-aware finalizer and standalone MoneyPuck refresh.\n'
        '2. Acquire NHL play-by-play and distinguish D shots/attempts, D assists, 5v5/PP exposure, and D-involved sequences leading to chances. '
        'Use lagged, exposure-adjusted, shrunken team inputs; validate against existing shot/usage features.\n'
        '3. Freeze one-input-at-a-time challengers before future games. Compare paired game errors, fantasy/position/role groups, '
        'calibration and uncertainty; evaluate goalie saves and GA separately.\n'
        '4. Automate postgame acquisition → hash/coverage validation → review → charts. Add scheduled CI after a credential-free '
        'pregame runner has freshness gates, retries, idempotence and failure alerts. Keep personal ESPN access local.',
        '\n## Reproducibility\n\nOfficial NHL boxscore/scoring-summary sources, hashes and local input paths are recorded in '
        '[manifest](manifest.json). Corrected actuals retrieved later do not change frozen forecasts. '
        'Full snapshots remain local; compact report tables and figures are published.']
    (a.out/'README.md').write_text('\n'.join(text)+'\n')
    manifest = dict(start=str(a.start), end=str(a.end), actuals=str(a.actuals), baseline=str(a.baseline),
        evaluations=list(map(str,a.evaluations)), source_manifest_sha256=digest(a.actuals/'manifest.json'),
        actual_games=week.game_id.nunique(), actual_player_rows=len(week), hash_checks=len(audit),
        source_urls=sorted(set(s['url'] for s in am['sources'])),
        validation=dict(duplicate_actuals=0, missing_actual_categories=0,
            min_shots=int(week.shots.min()), max_shots=int(week.shots.max()),
            source_season=20262027, game_type=2, source_games=am['games']),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(a.out)
    print(coverage.to_string(index=False))


if __name__ == '__main__':
    main()
