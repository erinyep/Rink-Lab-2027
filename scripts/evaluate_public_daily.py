"""Score sanitized frozen releases without requiring private issuance bundles.

Actuals must come from complete_fantasy_game_stats.py. Preserve all original
forecasts, verify recorded hashes and exclude late releases and nonparticipants.
"""
import argparse
from html import escape
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import CATEGORIES, digest, score_goalies, verify_manifest_files
from src.fantasy.per_game import require
from src.fantasy.team_probability import scoring_win_probability
from src.fantasy.model_policy import validate_current_model_policy, validate_frozen_model_policy


def metrics(frame, groups):
    rows = []
    for key, g in frame.groupby(groups):
        key = key if isinstance(key, tuple) else (key,)
        g = g.dropna(subset=['prediction', 'actual'])
        e = g.prediction - g.actual
        rows.append(dict(zip(groups, key), rows=len(g), games=g.game_id.nunique(),
                         predicted_total=g.prediction.sum(), actual_total=g.actual.sum(),
                         mae=e.abs().mean(), bias=e.mean(), rmse=np.sqrt((e**2).mean())))
    return pd.DataFrame(rows)


def scorecard_table(frame, columns=None, percentages=()):
    """Render a compact, escaped table for the standalone postgame report."""
    shown = frame.loc[:, columns].copy() if columns else frame.copy()
    for column in percentages:
        if column in shown:
            shown[column] = shown[column].map(lambda x: '' if pd.isna(x) else f'{x:.1%}')
    return shown.to_html(index=False, border=0, classes='data', na_rep='—',
                         float_format=lambda value: f'{value:.3f}', escape=True)


def write_scorecard(out, date, frames, policy):
    games = frames['team_games'].copy()
    games['score'] = games.away_score.astype(int).astype(str) + '–' + games.home_score.astype(int).astype(str)
    games['direct_home_probability'] = games.direct_home_probability.astype(float)
    games['original_home_probability'] = games.original_home_probability.astype(float)
    game_table = scorecard_table(games, ['away', 'home', 'score', 'direct_home_probability',
                                         'original_home_probability', 'ending'],
                                 percentages=['direct_home_probability', 'original_home_probability'])

    player = frames['player_metrics']
    player = player[player.category.isin(['shots', 'toi_minutes'])].copy()
    team = frames['team_metrics']
    team = team[team.category.isin(['shots', 'goals'])].copy()
    goalie = frames['goalie_metrics'].copy()
    winners = frames['winner_metrics'].copy()
    coverage = frames['coverage']
    coverage_table = scorecard_table(coverage)

    policy_rows = [
        {'Area': 'NHL all-player shots', 'Selected': policy['primary_sog_model'], 'Status': 'selected'},
        {'Area': 'NHL conditional TOI', 'Selected': policy['primary_toi_model'], 'Status': 'selected'},
        {'Area': 'Fantasy shots', 'Selected': policy['fantasy_shots_model'], 'Status': 'selected'},
        {'Area': 'Fantasy TOI', 'Selected': policy['fantasy_toi_model'] or 'default', 'Status': 'selected'},
        {'Area': 'Team win probability', 'Selected': policy['selected_probability_model'], 'Status': 'selected'},
        {'Area': 'Team probability calibration', 'Selected': 'calibrated_team_trial', 'Status': 'challenger only'},
        {'Area': 'Goalie opponent context', 'Selected': 'goalie_opponent_context_trial', 'Status': 'challenger only'},
    ]
    policy_table = scorecard_table(pd.DataFrame(policy_rows))

    sections = [
        ('Final scores and home win probabilities', game_table),
        ('Player shots and conditional ice time', scorecard_table(player)),
        ('Team scoring and shots', scorecard_table(team)),
        ('Goalie scoring', scorecard_table(goalie)),
        ('Winner probability scoring', scorecard_table(winners)),
        ('Coverage', coverage_table),
        ('Model policy in force', policy_table),
    ]
    section_html = '\n'.join(f'<section><h2>{escape(title)}</h2>{table}</section>'
                             for title, table in sections)
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Postgame model scorecard — {escape(str(date))}</title>
<style>body{{font:16px system-ui,sans-serif;max-width:1200px;margin:32px auto;padding:0 20px;color:#18313d;line-height:1.5}}h1,h2{{color:#123e50}}section{{margin:30px 0;overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:8px 10px;border-bottom:1px solid #d8e0e3;text-align:left;white-space:nowrap}}th{{background:#eef4f5}}.note{{background:#f2f7f7;padding:14px 18px;border-radius:8px}}</style></head>
<body><h1>Postgame model scorecard — {escape(str(date))}</h1>
<p class="note">Scored from the saved pregame forecasts and official final boxscores. All-player SOG uses {escape(policy['primary_sog_model'])}; conditional TOI uses {escape(policy['primary_toi_model'])}. Fantasy shots remain on default. Raw direct-team probabilities remain selected; calibrated team probabilities and goalie opponent context remain challengers. Player counts are conditional on a positive-TOI appearance.</p>
{section_html}
<p><a href="README.md">Report notes</a> · CSV files contain the underlying scored rows and summaries.</p></body></html>
'''
    (out/'index.html').write_text(html)
    (out/'README.md').write_text(f'''# Postgame model scorecard — {date}

[Open the interactive scorecard](index.html)

This report scores forecasts issued before puck drop against final NHL boxscores. It excludes late-issued games and treats player count forecasts as conditional on playing. The scorecard includes final scores, direct home win probabilities, player and team category errors, goalie scores, winner metrics, and coverage.

## Model policy

- NHL all-player shots: `{policy['primary_sog_model']}`
- NHL conditional TOI: `{policy['primary_toi_model']}`
- Fantasy shots: `{policy['fantasy_shots_model']}`
- Fantasy TOI: `{policy['fantasy_toi_model'] or 'default'}`
- Team win probabilities: `{policy['selected_probability_model']}`
- Calibrated team probabilities and goalie opponent context remain challenger-only.

See `index.html` for the tables and the CSV files for full scored records. `manifest.json` records input and output hashes.
''')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['bundle', 'team', 'actuals', 'boxscores', 'out']:
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    require(not a.out.exists(), 'Use a new output directory')
    bm = verify_manifest_files(a.bundle, [])
    verify_manifest_files(a.team, [])
    active_policy = validate_current_model_policy(bm['date'])
    frozen_policy = validate_frozen_model_policy(bm['date'], dict(
        models=bm['models'], primary_sog_model=bm['primary_sog_model'],
        primary_toi_model=bm['primary_toi_model']))
    require(frozen_policy['primary_sog_model'] == active_policy['primary_sog_model'] and
            frozen_policy['primary_toi_model'] == active_policy['primary_toi_model'],
            'Scored release selections differ from the active reviewed policy')
    am = verify_manifest_files(a.actuals, [])
    for source in am['sources']:
        for field in ['boxscore', 'landing']:
            require(digest(source[field]) == source[field+'_sha256'], 'Changed actual source')
    meta = json.loads((a.boxscores/'metadata.json').read_text())
    for source in meta['sources']:
        require(digest(a.boxscores/source['file']) == source['sha256'], 'Changed NHL source')
    boxes = {b['id']: b for b in (json.loads(p.read_text()) for p in a.boxscores.glob('boxscore_*.json'))}
    sk = pd.read_csv(a.actuals/'skater_game_stats.csv')
    ga = pd.read_csv(a.actuals/'goalie_game_stats.csv')
    require(not sk.duplicated(['game_id', 'player_id']).any(), 'Duplicate actual skater')
    p = pd.read_csv(a.bundle/'player_projections.csv')
    t = pd.read_csv(a.bundle/'team_projections.csv')
    g = pd.read_csv(a.bundle/'goalie_projections.csv')
    require({'goalie_history_baseline', 'goalie_opponent_context_trial'} <= set(g.model),
            'Expected goalie baseline and context challenger in the frozen release')
    for frame, keys in [(p, ['game_id','player_id','model']), (t,['game_id','team','model']),
                        (g,['game_id','player_id','model'])]:
        require(not frame.duplicated(keys).any(), 'Duplicate forecast')
        issued = pd.to_datetime(frame.released_at_utc, utc=True)
        start = pd.to_datetime(frame.start_time_utc, utc=True)
        require(((frame.issue_timing.eq('pregame')) == (issued < start)).all(), 'Timing mismatch')
    excluded = t.loc[t.issue_timing.ne('pregame'), ['game_id','team']].drop_duplicates()
    p = p[p.issue_timing.eq('pregame')].copy()
    t = t[t.issue_timing.eq('pregame')].copy()
    g = g[g.issue_timing.eq('pregame')].copy()
    ids = set(p.game_id)
    require(len(ids) == bm.get('pregame_games', bm['games']) and ids == set(t.game_id) == set(g.game_id), 'Coverage mismatch')
    require(ids <= set(boxes), 'Missing final boxscores')
    for gid in ids:
        b = boxes[gid]
        require(b['season'] == 20262027 and b['gameType'] == 2 and b['gameDate'] == bm['date']
                and b['gameState'] in ['OFF','FINAL'], 'Wrong actual population')
        require(p.loc[p.game_id.eq(gid),'start_time_utc'].eq(b['startTimeUTC']).all(), 'Changed game start')
    sk = sk[sk.game_id.isin(ids) & sk.toi_seconds.gt(0)].copy()
    require(sk[CATEGORIES].notna().all().all(), 'Incomplete actual categories')
    actual = sk[['game_id','player_id']+CATEGORIES].rename(columns={c:'actual_'+c for c in CATEGORIES})
    p = p.merge(actual, on=['game_id','player_id'], how='left', validate='many_to_one')
    parts = []
    for c in CATEGORIES:
        z = p[['game_id','player_id','player_name','team','model','selected_for_trial']].copy()
        z['category'] = c
        z['prediction'] = p['expected_'+c+'_if_plays']
        z['actual'] = p['actual_'+c]
        z['signed_error'] = z.prediction-z.actual
        z['absolute_error'] = z.signed_error.abs()
        parts.append(z)
    long = pd.concat(parts, ignore_index=True)
    covered = p[['game_id','player_id']].drop_duplicates()
    missing = sk.merge(covered.assign(modeled=True), on=['game_id','player_id'], how='left')
    missing = missing[missing.modeled.isna()]
    participants = p[p.actual_toi_minutes.notna()].drop_duplicates(['game_id','player_id'])
    selected = p[p.selected_for_trial.eq(True)].drop_duplicates(['game_id','player_id'])
    coverage = pd.DataFrame([dict(games=len(ids), actual_participants=len(sk), modeled_participants=len(participants),
        unmodeled_participants=len(missing), forecast_player_games=len(covered),
        selected_player_games=len(selected), selected_nonparticipants=int(selected.actual_toi_minutes.isna().sum()))])
    totals = sk.groupby(['game_id','team'])[CATEGORIES].sum()
    teams = []
    for r in t.itertuples():
        box = boxes[r.game_id]
        side = 'homeTeam' if box['homeTeam']['abbrev'] == r.team else 'awayTeam'
        for c in ['shots','goals','assists','points','hits','pp_points']:
            actual_value = box[side]['sog'] if c == 'shots' else totals.loc[(r.game_id,r.team),c]
            teams.append(dict(game_id=r.game_id,team=r.team,model=r.model,category=c,
                              prediction=getattr(r,'expected_'+c),actual=actual_value))
    teams = pd.DataFrame(teams)
    gs, gm, starts = score_goalies(g, ga)
    direct = pd.read_csv(a.team/'team_win_probabilities.csv')
    require(set(direct.game_id) == ids, 'Direct-team cohort differs')
    games, scores = [], []
    for r in direct.itertuples():
        b = boxes[r.game_id]
        require(pd.Timestamp(r.start_time_utc)-pd.Timestamp(r.issued_at_utc) >= pd.Timedelta(minutes=10), 'Late team forecast')
        require(r.training_through < r.date, 'Team model training leaks outcomes')
        require(r.home == b['homeTeam']['abbrev'] and r.away == b['awayTeam']['abbrev'], 'Fixture mismatch')
        y = int(b['homeTeam']['score'] > b['awayTeam']['score'])
        old = t[t.game_id.eq(r.game_id) & t.model.eq('default')].set_index('team')
        oh, oa = old.loc[r.home,'expected_goals'], old.loc[r.away,'expected_goals']
        op = scoring_win_probability(oh,oa)
        ah, aa = totals.loc[(r.game_id,r.home),'goals'], totals.loc[(r.game_id,r.away),'goals']
        games.append(dict(game_id=r.game_id,away=r.away,home=r.home,away_score=b['awayTeam']['score'],
            home_score=b['homeTeam']['score'],ending=b['periodDescriptor']['periodType'],
            direct_home_probability=r.home_win_probability,original_home_probability=op,
            direct_home_goals=r.home_goal_mean,direct_away_goals=r.away_goal_mean,
            original_home_goals=oh,original_away_goals=oa,actual_home_goals=ah,actual_away_goals=aa))
        models_to_score = [('direct_team',r.home_win_probability,r.home_goal_mean,r.away_goal_mean),
                ('original_player_sum',op,oh,oa),('goal_history_baseline',r.baseline_home_win_probability,r.baseline_home_goals,r.baseline_away_goals),
                ('coin_flip',.5,np.nan,np.nan)]
        if hasattr(r,'calibrated_home_win_probability'):
            require(r.probability_calibration_training_through < r.date, 'Calibration training leakage')
            require(np.isclose(r.calibrated_home_win_probability+r.calibrated_away_win_probability,1), 'Calibration probabilities do not sum to one')
            models_to_score.append(('calibrated_team_trial',r.calibrated_home_win_probability,r.home_goal_mean,r.away_goal_mean))
        for name, prob, h, aw in models_to_score:
            require(np.isfinite(prob) and 0 <= prob <= 1, 'Invalid winner probability')
            scores.append(dict(game_id=r.game_id,model=name,brier=(prob-y)**2,
                log_loss=-np.log(np.clip(prob if y else 1-prob,1e-12,1)),
                favorite_correct=float((prob>.5)==bool(y)) if prob != .5 else np.nan,
                goal_mae=(abs(h-ah)+abs(aw-aa))/2,predicted_goals=h+aw,actual_goals=ah+aa))
    scores = pd.DataFrame(scores)
    win_metrics = scores.groupby('model').agg(games=('game_id','size'),brier=('brier','mean'),
        log_loss=('log_loss','mean'),favorite_accuracy=('favorite_correct','mean'),goal_mae=('goal_mae','mean'),
        predicted_goals=('predicted_goals','sum'),actual_goals=('actual_goals','sum')).reset_index()
    win_metrics.loc[win_metrics.model.eq('coin_flip'),'predicted_goals'] = np.nan
    a.out.mkdir(parents=True)
    frames = dict(player_projections_scored=p,player_category_scores=long,player_metrics=metrics(long,['model','category']),
        player_shots_by_game=metrics(long[long.category.eq('shots')],['game_id','model']),
        team_category_scores=teams,team_metrics=metrics(teams,['model','category']),goalie_scores=gs,
        goalie_metrics=gm,goalie_starter_scores=starts,coverage=coverage,unmodeled_actual_skaters=missing,
        excluded_late_games=excluded,team_games=pd.DataFrame(games),winner_scores=scores,winner_metrics=win_metrics)
    for name, frame in frames.items():
        frame.to_csv(a.out/(name+'.csv'),index=False)
    write_scorecard(a.out, bm['date'], frames, active_policy)
    (a.out/'manifest.json').write_text(json.dumps(dict(date=bm['date'],inputs={k:str(v) for k,v in vars(a).items() if k!='out'},
        code_sha256={str(path):digest(path) for path in [Path(__file__),
            Path(__file__).resolve().parents[1]/'scripts/evaluate_daily_forecasts.py',
            Path(__file__).resolve().parents[1]/'scripts/validate_daily_bundle.py',
            Path(__file__).resolve().parents[1]/'src/fantasy/model_policy.py',
            Path(__file__).resolve().parents[1]/'src/fantasy/team_probability.py']},
        source_manifest_hashes={str(folder/'manifest.json'):digest(folder/'manifest.json')
            for folder in [a.bundle,a.team,a.actuals]},boxscore_metadata_sha256=digest(a.boxscores/'metadata.json'),
        model_policy=active_policy,
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    print(win_metrics.to_string(index=False))
    print(frames['player_metrics'].query("category in ['shots','toi_minutes']").to_string(index=False))
    print(coverage.to_string(index=False))


if __name__ == '__main__':
    main()
