#!/usr/bin/env python3
"""Review issued October 13 baseline forecasts and earlier prospective trials.

This deliberately does not reconstruct missing October 13 challenger forecasts.
Team sums conditioned on actual participants are labeled postgame diagnostics.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import CATEGORIES, digest, verify_hash, verify_manifest_files
from scripts.evaluate_october_9 import table
from src.fantasy.per_game import require


def error_summary(frame, predicted, observed):
    valid = frame[[predicted, observed]].dropna()
    error = valid[predicted] - valid[observed]
    return dict(rows=len(valid), predicted_total=valid[predicted].sum(),
                actual_total=valid[observed].sum(), mae=error.abs().mean(),
                bias=error.mean(), rmse=np.sqrt(error.pow(2).mean()))


def clustered_difference(frame, population):
    """Paired player errors; resample games and retain appearance weights."""
    wide = frame.pivot(index=['game_id', 'player_id'], columns='model', values='absolute_error')
    require(wide.notna().all().all(), 'Models must share every scored appearance')
    delta = wide.subtract(wide['default'], axis=0)
    sums = delta.groupby(level='game_id').sum()
    counts = delta.groupby(level='game_id').size().to_numpy()
    rng = np.random.default_rng(20261014)
    draws = rng.integers(0, len(sums), (20000, len(sums)))
    boot = sums.to_numpy()[draws].sum(axis=1) / counts[draws].sum(axis=1)[:, None]
    return pd.DataFrame(dict(population=population, model=sums.columns,
        games=len(sums), appearances=len(wide), mae_delta_vs_default=delta.mean().values,
        lower_95=np.quantile(boot, .025, axis=0), upper_95=np.quantile(boot, .975, axis=0),
        games_improved=(sums < 0).sum().values))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--review', type=Path, required=True)
    ap.add_argument('--actuals', type=Path, required=True)
    ap.add_argument('--evaluations', type=Path, nargs='+', required=True)
    args = ap.parse_args()
    audit = []
    rm = json.loads((args.review / 'manifest.json').read_text())
    frozen = Path(rm['frozen_forecast'])
    fm = verify_manifest_files(frozen, audit)
    am = verify_manifest_files(args.actuals, audit)
    boxes = Path(rm['raw_snapshot'])
    for source in json.loads((boxes / 'metadata.json').read_text())['sources']:
        verify_hash(boxes / source['file'], source['sha256'], audit)
    for source in am['sources']:
        for field in ['boxscore', 'landing']:
            verify_hash(Path(source[field]), source[field + '_sha256'], audit)
    require(am['dates_covered'] == ['2026-10-13'], 'This report is for October 13 only')
    schedule = json.loads((boxes / 'schedule.json').read_text())
    games = [g for day in schedule['gameWeek'] if day['date'] == '2026-10-13'
             for g in day['games'] if g['gameType'] == 2]
    require(all(g['season'] == 20262027 and g['gameState'] in ['OFF', 'FINAL'] for g in games),
            'Wrong season or unfinished games')
    game_ids = {g['id'] for g in games}
    actual = pd.read_csv(args.actuals / 'skater_game_stats.csv')
    require(set(actual.game_id) == game_ids, 'Incomplete official game coverage')
    require(not actual.duplicated(['game_id', 'player_id']).any(), 'Duplicate actual player')
    require(not actual[CATEGORIES].isna().any().any(), 'Missing skater actuals')
    require((actual.points == actual.goals + actual.assists).all(), 'Points identity')
    require((actual.pp_points <= actual.points).all(), 'PPP exceeds points')
    joined = pd.read_csv(args.review / 'frozen_forecast_vs_actual.csv')
    forecast = pd.read_csv(frozen / 'scheduled_skater_game_forecasts.csv')
    forecast = forecast[forecast.game_id.isin(game_ids)]
    require(set(forecast.game_id) == game_ids, 'Missing frozen games')
    require((pd.to_datetime(forecast.start_time_utc, utc=True) > pd.Timestamp(fm['created_at_utc'])).all(),
            'Late baseline issuance')
    # Recheck the earlier join against hashed frozen values, including alias resolution.
    keys = ['game_id', 'player_id']
    means = [c + '_if_plays' for c in CATEGORIES]
    expected = forecast[forecast.player_id.notna()].sort_values('pool', ascending=False).drop_duplicates(keys)
    check = joined[joined.player_id.notna()].merge(expected[keys + means], on=keys,
        suffixes=('', '_frozen'), validate='one_to_one')
    require(len(check) == len(expected), 'Review lost resolved forecast rows')
    for c in means:
        require(np.allclose(check[c], check[c + '_frozen'], equal_nan=True), 'Changed frozen mean: ' + c)
    labels = ['player_name', 'fantasy_team_name', 'pool', 'injury_status', 'position_group',
              'forecast_status', 'nhl_team_abbrev']
    players = expected[keys + labels + means].rename(columns={c+'_if_plays': 'expected_'+c+'_if_plays' for c in CATEGORIES})
    players = players.merge(actual.rename(columns={c: 'actual_'+c for c in CATEGORIES}),
                            on=keys, how='left', validate='one_to_one')
    players['scoring_status'] = np.where(players.toi_seconds.gt(0), 'positive_toi', 'no_positive_toi_not_scored')
    players['model'] = 'default_issued_2026-10-09'
    players['issued_at_utc'] = fm['created_at_utc']
    for c in CATEGORIES:
        players.loc[players.toi_seconds.fillna(0).le(0), 'actual_'+c] = np.nan
        players[c+'_error'] = players['expected_'+c+'_if_plays'] - players['actual_'+c]
    observed = players[players.scoring_status.eq('positive_toi')].copy()
    require(observed[['expected_'+c+'_if_plays' for c in CATEGORIES]].notna().all().all(), 'Missing mean among covered appearances')
    missing = actual[actual.toi_seconds.gt(0)].merge(expected[keys], on=keys, how='left', indicator=True)
    missing = missing[missing._merge.eq('left_only')].drop(columns='_merge')
    category_rows = []
    for population, frame in [('all_covered', observed), ('saved_fantasy_roster', observed[observed.pool.eq('rostered')])]:
        for c in CATEGORIES:
            category_rows.append(dict(population=population, category=c,
                **error_summary(frame, 'expected_'+c+'_if_plays', 'actual_'+c)))
    categories = pd.DataFrame(category_rows)
    owner_rows = [dict(fantasy_team_name=name, **error_summary(g, 'expected_shots_if_plays', 'actual_shots'))
                  for name, g in observed[observed.pool.eq('rostered')].groupby('fantasy_team_name')]
    owners = pd.DataFrame(owner_rows)
    observed['shot_tier'] = pd.cut(observed.expected_shots_if_plays, [0,1,2,3,np.inf], right=False).astype(str)
    strata = pd.DataFrame([dict(stratum=field, value=value,
        **error_summary(g, 'expected_shots_if_plays', 'actual_shots'))
        for field in ['position_group', 'shot_tier'] for value, g in observed.groupby(field)])
    team_rows = []
    for game in games:
        box = json.loads((boxes / f"boxscore_{game['id']}.json").read_text())
        for side, other in [('awayTeam','homeTeam'), ('homeTeam','awayTeam')]:
            team = box[side]['abbrev']; group = observed[observed.game_id.eq(game['id']) & observed.team.eq(team)]
            all_team = actual[actual.game_id.eq(game['id']) & actual.team.eq(team)]
            require(all_team.shots.sum() == box[side]['sog'], 'Official/player SOG disagreement')
            team_rows.append(dict(game_id=game['id'], team=team, opponent=box[other]['abbrev'],
                final_goals=box[side]['score'], official_shots=box[side]['sog'],
                actual_positive_toi_skaters=int(all_team.toi_seconds.gt(0).sum()), covered_skaters=len(group),
                **error_summary(group, 'expected_shots_if_plays', 'actual_shots')))
    teams = pd.DataFrame(team_rows).rename(columns={'predicted_total':'matched_player_expected_shots',
                                                   'actual_total':'matched_player_actual_shots'})
    # Earlier complete daily trials are a distinct sample, never pooled with the aged baseline.
    ps, ts, gs, prior_exceptions = [], [], [], []
    for p in args.evaluations:
        em = verify_manifest_files(p, audit)
        verify_hash(Path(em['frozen_bundle'])/'manifest.json', em['frozen_bundle_manifest_sha256'], audit)
        prior_exceptions.extend(em.get('source_hash_exceptions', []))
        ps.append(pd.read_csv(p/'simulation_summary.csv'))
        ts.append(pd.read_csv(p/'team_projected_vs_actual.csv'))
        gs.append(pd.read_csv(p/'goalie_projections.csv'))
    p = pd.concat(ps); p = p[p.issue_timing.eq('pregame') & p.actual.notna()]
    require(not p.duplicated(['game_id','player_id','category','model']).any(), 'Repeated evaluation games')
    require(set(p.date) == {'2026-10-10','2026-10-12'}, 'Update report narrative for different trial dates')
    t = pd.concat(ts); t = t[t.issue_timing.eq('pregame') & t.actual.notna()]
    shot = p[p.category.eq('shots')]
    fantasy = shot[shot.fantasy_team_name.fillna('').str.strip().ne('')]
    model_rows = []
    for model, frame in shot.groupby('model'):
        te = t[t.model.eq(model) & t.category.eq('shots')]
        fa = fantasy[fantasy.model.eq(model)]
        model_rows.append(dict(model=model, **error_summary(frame,'model_projection_if_plays','actual'),
            team_sog_mae=te.absolute_error.mean(), fantasy_sog_mae=fa.absolute_error.mean(),
            exact_player_rate=frame.exact_guess_correct.mean(), interval_coverage=frame.inside_p10_p90.mean()))
    models = pd.DataFrame(model_rows)
    uncertainty = pd.concat([clustered_difference(shot, 'all_players'),
                             clustered_difference(fantasy, 'saved_fantasy_roster')], ignore_index=True)
    toi = pd.DataFrame([dict(model=m, **error_summary(g,'model_projection_if_plays','actual'))
                       for m,g in p[p.category.eq('toi_minutes')].groupby('model')])
    goalie = pd.concat(gs); goalie = goalie[goalie.issue_timing.eq('pregame') &
        goalie.actual_starter.eq(True) & goalie.actual_count_identity_ok.eq(True) & goalie.actual_toi_seconds.gt(0)]
    goalie_metrics = pd.DataFrame([dict(model=m,category=c,
        **error_summary(g, c+'_if_full_start', 'actual_'+c))
        for m,g in goalie.groupby('model') for c in ['shots_against','saves','goals_against']])
    goalie_actual = pd.read_csv(args.actuals/'goalie_game_stats.csv')
    require(not goalie_actual.duplicated(keys).any(), 'Duplicate goalie actual')
    require(goalie_actual.loc[goalie_actual.toi_seconds.gt(0),'count_identity_ok'].all(), 'Goalie count exceptions need review')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = Path('data/processed/forecasts')/f'october_13_review_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    frames = dict(player_projected_vs_actual=players, team_matched_player_diagnostics=teams,
        category_metrics=categories, fantasy_team_metrics=owners, shot_strata=strata,
        unmodeled_actual_skaters=missing, earlier_model_comparison=models,
        earlier_game_bootstrap=uncertainty, earlier_toi_metrics=toi, earlier_goalie_metrics=goalie_metrics,
        source_hash_audit=pd.DataFrame(audit).drop_duplicates())
    for name, frame in frames.items(): frame.to_csv(out/(name+'.csv'), index=False)
    manifest = dict(date='2026-10-13', created_at_utc=datetime.now(timezone.utc).isoformat(),
        frozen_forecast=str(frozen), frozen_manifest_sha256=digest(frozen/'manifest.json'),
        review=str(args.review), actuals=str(args.actuals), boxscores=str(boxes),
        earlier_evaluations=[str(p) for p in args.evaluations], earlier_source_exceptions=prior_exceptions,
        official_games=len(games),
        positive_toi_skaters=int(actual.toi_seconds.gt(0).sum()), scored_skaters=len(observed),
        unmodeled_skaters=len(missing), code_sha256=digest(Path(__file__)),
        bootstrap_seed=20261014, bootstrap_draws=20000,
        limitations=['No October 13 daily challenger/goalie run located; only older default is scored.',
            'Matched-player team diagnostics select participants after games and are not issued team forecasts.',
            'Fantasy ownership is the October 9 snapshot; nonparticipants are not scored as zeros.',
            'Earlier five-model trials are pooled only across October 10/12 pregame games.'],
        files={p.name:digest(p) for p in out.glob('*.csv')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report = Path('outputs/per_game_forecast/2026-10-13_results_readout.md')
    lines = ['# October 13 results and model recommendations',
        '\n## What was actually issued',
        f'\nAll {len(games)} final regular-season games were acquired from the [official NHL schedule](https://api-web.nhle.com/v1/schedule/2026-10-13), with boxscores and scoring summaries. The latest saved default covering them was issued **{fm["created_at_utc"]}** (October 9, 3:50 PM Eastern), over four days before the games. The October 13 daily run remained pending; no five-model slate, goalie predictions, team simulations or exact-count guesses for this date were located. No missing predictions were reconstructed after seeing results.',
        f'\nThe boxscores contain {len(actual)} skater rows, including one zero-TOI row (Z. L’Heureux, Colorado), leaving {actual.toi_seconds.gt(0).sum()} appearances. The saved ESPN pool covers **{len(observed)}**, with **{len(missing)} unmodeled appearances** retained in an audit. All covered appearances have all nine conditional means. Fantasy ownership/injuries reflect October 9, not game-day rosters. Do not score missing/unused players as zeros.',
        '\n## October 13: default projected versus actual', '\n'+table(categories),
        '\nMAE is average absolute error per appearance; lower is better. Bias is predicted minus actual. Totals use identical covered players. TOI is in minutes. PPP is completed from NHL scoring summaries. `expected_*_if_plays` is the conditional prediction; absent unconditional `expected_*` values in older sources do not mean these conditional predictions are missing.',
        '\n## Where the shot error came from', '\n'+table(strata),
        '\nThe league-wide excess is concentrated among defensemen in this sample; forwards are close in aggregate. Players projected below two shots are also close as a group, while the two-to-three-shot group is high. This motivates testing position/role-specific calibration, not fitting new correction factors to this one night. Aggregate agreement can hide substantial individual errors.',
        '\n## Fantasy teams at the saved ownership snapshot', '\n'+table(owners),
        '\nThese are shot results for players who appeared, using saved scoring-roster membership; they are not current ESPN lineup totals or fantasy-point scores. Quinn’s cohort is overpredicted on this night, unlike the earlier concern about underprediction. Ownership itself should not drive hockey-rate adjustments.',
        '\n## All games: matched-player shot diagnostics',
        '\nThese sums select actual participants after the games. They diagnose player-forecast errors, **not pregame team-total forecast accuracy**. Missing players explain any gap between matched actual shots and official team SOG. Final score includes shootout decisions, where applicable; player goals exclude shootout deciding goals.',
        '\n'+table(teams.drop(columns=['rows','rmse'])),
        '\n## How the five models are performing: earlier prospective evidence',
        f'\nThis comparison is **October 10 and 12 only**: {shot.game_id.nunique()} games, {len(shot[shot.model.eq("default")])} matched appearances, {len(t[t.model.eq("default") & t.category.eq("shots")])} team observations and {len(fantasy[fantasy.model.eq("default")])} fantasy-rostered appearances. It excludes late forecasts, retrospective October 9 hybrid results, and October 13’s aged baseline.',
        '\n'+table(models),
        '\nCandidate has the lowest player/team SOG MAE and reduces positive bias. Its advantage is modest. Default remains slightly better on the saved fantasy cohort. The opponent-only effect does not improve the baseline, and combining it with candidate has no demonstrated incremental gain. Model ranking depends on the population and objective; include RMSE and mean bias alongside MAE when evaluating expected counts.',
        '\nPaired game-cluster bootstrap: 20,000 resamples with appearance-weighted errors. Negative differences favor the challenger. These are exploratory intervals over only 13 game clusters, not guarantees of future performance.', '\n'+table(uncertainty),
        '\nPlayer shot p10–p90 ranges contain about 92–93% of outcomes. Discrete count quantiles can cover more than 80% even for a correct model; this does not establish overdispersion or justify mechanically narrowing intervals. Check discrete probability calibration, proper scores and conditional coverage over a larger holdout. Exact player counts are correct about 32% of the time and should be a secondary metric to the forecast distribution.',
        '\n## Usage and goalies', '\n'+table(toi[['model','rows','mae','bias','rmse']]),
        '\nThe usage model improves TOI errors, but its shot result remains behind candidate. Test TOI-only, rate-only and opponent-context changes separately rather than assuming the whole combined model is better.',
        '\nEarlier October 10/12 actual-starter goalie comparison:\n'+table(goalie_metrics),
        f'\nOctober 13 goalie actuals are saved: {goalie_actual.starter.eq(True).sum()} starters and {goalie_actual.toi_seconds.gt(0).sum()} positive-TOI appearances; all active goalie rows satisfy SA = saves + GA. There are no saved October 13 goalie predictions to score. Earlier full-60-minute projections have mixed results across SA, saves and GA; actual pulls/empty-net time matter. Start probabilities remain provisional.',
        '\n## Recommended next changes, in order',
        '\n1. **Make daily issuance reliable.** Finish the MoneyPuck refresh command and date-aware finalizer, then use one orchestrated refresh/build/goalie/finalize/check command. Require current injury timestamps, declare source publication lag, cover every official game, and record issue times and immutable hashes. October 13 missed the intended experiment because no daily challenger bundle was issued.',
        '\n2. **Repair player and lineup coverage.** Use the current official roster plus recent participants, stable NHL IDs and explicit position priors for missing history. Review the 17 unmodeled October 13 appearances. Model probability of dressing separately from conditional production; do not sum the entire ESPN pool as a team lineup.',
        '\n3. **Retain default and candidate.** Candidate is the leading all-player/team challenger; default remains the fantasy baseline until more prospective evidence accumulates. Do not make another global SOG cut, strengthen the opponent factor, or claim an October 13 challenger win.',
        '\n4. **Test deployment before added complexity.** Isolate the usage model’s TOI improvement; then test EV/PP exposure times shot rate, with shrinkage for sparse histories and neutral fallbacks. Evaluate position and pregame shot-rate strata on later games. The October 13 defense/forward split is a hypothesis to validate, not a fitted fix.',
        '\n5. **Improve goalie participation/duration.** Timestamp confirmed starters where available, otherwise retain provisional probabilities; score starting probability and conditional shot/save/GA counts separately. Test duration/pull effects and opponent shot volume without assuming all components improve together.',
        '\n6. **Continue chronological validation.** Keep a predeclared holdout, paired model populations, game-cluster uncertainty, MAE/RMSE/bias and discrete calibration. Keep fantasy and league-wide cohorts separate. These outcomes are now development evidence; newly tuned changes need later unseen games.',
        '\n## Files and reproduction',
        f'\n[Player projected versus actual](../../{out}/player_projected_vs_actual.csv) · [Team diagnostics](../../{out}/team_matched_player_diagnostics.csv) · [Missing-player audit](../../{out}/unmodeled_actual_skaters.csv) · [Goalie actuals, no forecasts](../../{args.actuals}/goalie_game_stats.csv)',
        f'\nSaved baseline: `{frozen}`. Evaluated output: `{out}`. Frozen data, acquired actual-file hashes and earlier evaluation files used here were verified. The October 10 evaluation retains its documented unavailable historical parent-manifest back-reference; this is not a changed forecast-data hash and is preserved in this review manifest. Statistical settings and frozen predictions were unchanged.',
        '\n```sh\nrink-lab.venv/bin/python scripts/write_october_13_review.py \\\n'+f'  --review {args.review} \\\n  --actuals {args.actuals} \\\n  --evaluations '+' '.join(map(str,args.evaluations))+'\n```']
    report.write_text('\n'.join(lines)+'\n')
    (out/'README.md').write_text('# October 13 review\n\nRead `player_projected_vs_actual.csv`; filter `scoring_status=positive_toi`.\n'
        'Team aggregates are matched-player postgame diagnostics, not issued team forecasts.\n'
        'Earlier model comparisons are October 10/12 only. See outputs/per_game_forecast/2026-10-13_results_readout.md.\n')
    print('Readout:', report); print('Artifacts:', out)
    print(models.to_string(index=False)); print(uncertainty.to_string(index=False))


if __name__ == '__main__':
    main()
