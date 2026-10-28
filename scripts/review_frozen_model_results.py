"""Compare a frozen team challenger, daily models and saved fantasy roster on finals."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files, digest
from scripts.evaluate_october_9 import table
from src.fantasy.team_probability import scoring_win_probability


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ['team', 'bundle', 'evaluation', 'actuals', 'boxscores', 'fantasy', 'out']:
        ap.add_argument('--' + key, type=Path, required=True)
    a = ap.parse_args()
    tm = verify_manifest_files(a.team, [])
    verify_manifest_files(a.bundle, [])
    verify_manifest_files(a.actuals, [])
    release = Path(tm['model_release'])
    assert digest(release / 'manifest.json') == tm['model_release_sha256']
    verify_manifest_files(release, [])
    assert json.loads((release / 'fitted_model.json').read_text())['training_through'] < tm['date']
    f = pd.read_csv(a.team / 'team_win_probabilities.csv')
    old = pd.read_csv(a.bundle / 'team_projections.csv').query("model == 'default'")
    sk = pd.read_csv(a.actuals / 'skater_game_stats.csv').query('toi_seconds > 0')
    assert not f.game_id.duplicated().any()
    assert not sk.duplicated(['game_id', 'player_id']).any()
    bm = json.loads((a.boxscores / 'metadata.json').read_text())
    hashes = {s['file']: s['sha256'] for s in bm['sources']}
    games, scores = [], []
    for r in f.itertuples():
        path = a.boxscores / f'boxscore_{r.game_id}.json'
        assert digest(path) == hashes[path.name]
        b = json.loads(path.read_text())
        assert b['gameState'] in ['OFF', 'FINAL'] and b['gameType'] == 2
        assert b['season'] == 20262027 and b['gameDate'] == r.date
        assert b['homeTeam']['abbrev'] == r.home and b['awayTeam']['abbrev'] == r.away
        assert b['startTimeUTC'] == r.start_time_utc
        assert pd.Timestamp(r.issued_at_utc) < pd.Timestamp(r.start_time_utc)
        assert np.isclose(r.home_win_probability + r.away_win_probability, 1)
        hs, aws = b['homeTeam']['score'], b['awayTeam']['score']
        assert hs != aws
        y = int(hs > aws)
        o = old[old.game_id.eq(r.game_id)].set_index('team')
        assert len(o) == 2 and o.issue_timing.eq('pregame').all()
        oh, oa = o.loc[r.home, 'expected_goals'], o.loc[r.away, 'expected_goals']
        op = scoring_win_probability(oh, oa)
        actual = sk[sk.game_id.eq(r.game_id)].groupby('team').goals.sum()
        # Skater goals include overtime but exclude the artificial shootout winner goal.
        ah, aa = actual[r.home], actual[r.away]
        games.append(dict(game_id=r.game_id, away=r.away, home=r.home,
            away_score=aws, home_score=hs, new_home_probability=r.home_win_probability,
            original_home_probability=op, new_home_goals=r.home_goal_mean,
            new_away_goals=r.away_goal_mean, original_home_goals=oh, original_away_goals=oa))
        for name, p, h, away in [('new_team', r.home_win_probability, r.home_goal_mean, r.away_goal_mean),
                ('original_player_sum', op, oh, oa),
                ('goal_history_baseline', r.baseline_home_win_probability, r.baseline_home_goals, r.baseline_away_goals),
                ('coin_flip', .5, np.nan, np.nan)]:
            assert 0 <= p <= 1
            scores.append(dict(game_id=r.game_id, model=name, brier=(p-y)**2,
                log_loss=-np.log(np.clip(p if y else 1-p, 1e-12, 1)),
                favorite_correct=float((p > .5) == bool(y)) if p != .5 else np.nan,
                goal_mae=(abs(h-ah)+abs(away-aa))/2,
                predicted_goals=h+away, actual_goals=ah+aa))
    scored = pd.DataFrame(scores)
    metrics = scored.groupby('model').agg(games=('game_id','size'), brier=('brier','mean'),
        log_loss=('log_loss','mean'), favorite_accuracy=('favorite_correct','mean'),
        goal_mae=('goal_mae','mean'), predicted_goals=('predicted_goals','sum'), actual_goals=('actual_goals','sum')).reset_index()
    metrics.loc[metrics.model.eq('coin_flip'), 'predicted_goals'] = np.nan
    wide = scored.pivot(index='game_id', columns='model', values='brier')
    delta = (wide.new_team-wide.original_player_sum).to_numpy()
    rng = np.random.default_rng(20261028)
    ci = np.quantile(rng.choice(delta, (10000,len(delta)), replace=True).mean(axis=1), [.025,.975])
    roster = pd.read_csv(a.fantasy / 'roster.csv')
    fm = json.loads((a.fantasy / 'manifest.json').read_text())
    assert fm['bundle'] == str(a.bundle)
    for name, sha in fm.get('files', {}).items():
        assert digest(a.fantasy / name) == (sha.get('sha256') if isinstance(sha,dict) else sha)
    roster = roster.merge(sk[['game_id','player_id','toi_minutes']], on=['game_id','player_id'], how='left', validate='many_to_one')
    q = roster[roster.toi_minutes.notna()].copy()
    q['old_error'] = (q.baseline_expected_toi_minutes_if_plays-q.toi_minutes).abs()
    q['new_error'] = (q.expected_toi_minutes_if_plays-q.toi_minutes).abs()
    player_metrics = pd.read_csv(a.evaluation / 'player_metrics.csv')
    fantasy_metrics = pd.read_csv(a.evaluation / 'fantasy_player_metrics.csv')
    goalie_metrics = pd.read_csv(a.evaluation / 'goalie_metrics.csv')
    coverage = pd.read_csv(a.evaluation / 'game_team_coverage.csv')
    assert set(coverage.game_id) == set(f.game_id)
    em = json.loads((a.evaluation / 'manifest.json').read_text())
    assert em['frozen_bundle_manifest_sha256'] == digest(a.bundle / 'manifest.json')
    assert em['actuals_manifest_sha256'] == digest(a.actuals / 'manifest.json')
    a.out.mkdir(parents=True, exist_ok=False)
    for name, frame in [('team_games',pd.DataFrame(games)), ('team_scores',scored), ('team_metrics',metrics), ('fantasy_roster_scored',roster), ('fantasy_toi_comparison',q)]:
        frame.to_csv(a.out / (name+'.csv'), index=False)
    for name, frame in [('player_metrics',player_metrics),('fantasy_player_metrics',fantasy_metrics),('goalie_metrics',goalie_metrics),('coverage',coverage)]:
        frame.to_csv(a.out / (name+'.csv'), index=False)
    cols = ['model','category','rows_scored','mae','bias']
    report = f'''# Frozen model results — {tm['date']}

All {len(f)} games scored against official NHL finals. No refitting.

{table(metrics)}

Brier and goal MAE: lower is better. Goal MAE is per team; excludes shootout bonus goals.
Winner scores include overtime/shootouts, one home outcome per game.
Original-model probabilities are the existing Poisson/tie-split transform of saved pregame goal means.
New-minus-original Brier delta: {delta.mean():.4f}; paired game-bootstrap 95% interval [{ci[0]:.4f}, {ci[1]:.4f}].
One slate cannot establish lasting superiority. No market benchmark is scored in this report.

## Game results and home win probabilities

{table(pd.DataFrame(games)[['away','home','away_score','home_score','new_home_probability','original_home_probability']])}

## Player shots and fantasy ice time

{table(player_metrics[player_metrics.category.eq('shots')][cols])}

{table(fantasy_metrics[fantasy_metrics.category.isin(['shots','toi_minutes'])][cols])}

These fantasy metrics cover all saved league rosters, not only Quinn. The deployed fantasy policy changes TOI only;
other usage-trial categories remain experimental. MAE is average absolute error; bias is prediction minus actual.

## Goalie counts

{table(goalie_metrics[goalie_metrics.population.eq('actual_starters')][cols])}

Full-start predictions compared with actual starters; 55–65 minute sensitivity is in goalie_metrics.csv.
All {int(coverage.actual_skaters.sum())} actual skater appearances covered;
{int(coverage.selected_identified_nonparticipants.sum())} selected lineup players did not appear.
Goalie count identity exceptions: {int(coverage.goalie_count_exceptions.sum())}.

## Saved fantasy roster ice time

{len(q)} observed skaters; old TOI MAE {q.old_error.mean():.3f} minutes; new {q.new_error.mean():.3f} minutes.
Includes saved active and bench skaters who played, not inferred final lineup decisions.
Absent/zero-TOI skaters remain unscored rather than assigned zero production.

[Game-by-game](team_games.csv) · [Fantasy roster](fantasy_toi_comparison.csv)

Daily player/category, team, goalie, coverage and source-hash diagnostics: `{a.evaluation}`.
Actuals: `{a.actuals}`. Official source snapshot: `{a.boxscores}`.
'''
    (a.out / 'README.md').write_text(report)
    (a.out / 'manifest.json').write_text(json.dumps(dict(inputs={k:str(v) for k,v in vars(a).items() if k != 'out'},
        source_manifests={str(p/'manifest.json'):digest(p/'manifest.json') for p in [a.team,a.bundle,a.actuals,a.fantasy]},
        boxscore_metadata_sha256=digest(a.boxscores/'metadata.json'),
        files={p.name:digest(p) for p in a.out.iterdir()}), indent=2)+'\n')
    print(report)


if __name__ == '__main__':
    main()
