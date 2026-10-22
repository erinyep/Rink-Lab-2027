#!/usr/bin/env python3
"""Archive issued predictions and versioned results; derive rolling scoreboards."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from src.fantasy.history import archive_snapshot, digest
from scripts.evaluate_daily_forecasts import verify_manifest_files


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--review', required=True, type=Path)
    ap.add_argument('--bundle', required=True, type=Path)
    ap.add_argument('--root', type=Path, default=Path('data/processed/prediction_history'))
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise ValueError('Preserve earlier scoreboards; use a new output directory')
    review = verify_manifest_files(a.review, [])
    registry = []

    def save(source, kind):
        archived = archive_snapshot(source, a.root, kind)
        registry.append(dict(kind=kind, source=str(source), archive=str(archived), manifest_sha256=digest(Path(source)/'manifest.json')))

    save(a.bundle, 'predictions')
    save(Path(review['actuals']), 'actuals')
    frames = []
    for directory in review['evaluations']:
        directory = Path(directory)
        m = verify_manifest_files(directory, [])
        if m['actuals_manifest_sha256'] != review['actuals_sha256']:
            raise ValueError('Mixed actual vintages')
        if digest(Path(m['frozen_bundle'])/'manifest.json') != m['frozen_bundle_manifest_sha256']:
            raise ValueError('Changed forecast version')
        save(Path(m['frozen_bundle']), 'predictions')
        save(directory, 'evaluations')
        for name, level, mean in [('simulation_summary', 'player', 'model_projection_if_plays'), ('team_projected_vs_actual', 'team', 'projection_mean')]:
            z = pd.read_csv(directory/(name+'.csv'))
            z = z[z.issue_timing.eq('pregame')].copy()
            z['prediction'] = z[mean]
            z['level'] = level
            z['date'] = m['date']
            z['population'] = 'all'
            frames.append(z)
            if level == 'player':
                fantasy = z[z.fantasy_team_name.fillna('').str.strip().ne('')].copy()
                fantasy['population'] = 'saved_fantasy_roster'
                frames.append(fantasy)
        g = pd.read_csv(directory/'goalie_projections.csv')
        g = g[g.issue_timing.eq('pregame') & g.actual_starter.eq(1) & g.eligible_for_conditional_count_scoring.eq(True)]
        for cat in ['shots_against', 'saves', 'goals_against']:
            z = g.copy()
            z['prediction'] = z[cat+'_if_full_start']
            z['actual'] = z['actual_'+cat]
            z['category'], z['level'], z['population'], z['date'] = cat, 'goalie', 'eligible_actual_starters', m['date']
            frames.append(z)
    data = pd.concat(frames, ignore_index=True)
    rows = []
    through = pd.Timestamp(review['through'])
    for window, days in [('season', None), ('7_day', 7), ('30_day', 30)]:
        z = data if days is None else data[pd.to_datetime(data.date).ge(through-pd.Timedelta(days=days-1))]
        for keys, part in z.groupby(['level', 'population', 'model', 'category']):
            observed = part[part.actual.notna() & part.prediction.notna()]
            error = observed.prediction-observed.actual
            rows.append(dict(zip(['level', 'population', 'model', 'category'], keys), window=window,
                through=review['through'], forecast_rows=len(part), scored_rows=len(observed),
                unscored_rows=len(part)-len(observed), games=observed.game_id.nunique(),
                mae=error.abs().mean(), rmse=np.sqrt((error**2).mean()), bias=error.mean()))
    a.out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(a.out/'model_scoreboard.csv', index=False)
    pd.DataFrame(registry).drop_duplicates().to_csv(a.out/'source_registry.csv', index=False)
    (a.out/'README.md').write_text(f'''# Prediction history — through {review['through']}

[Season and rolling 7/30-day scoreboard](model_scoreboard.csv) · [Source registry](source_registry.csv).

Immutable, content-addressed copies of issued forecasts, official actuals and evaluations
are stored locally under `data/processed/prediction_history/`. Repeating registration
verifies hashes; corrected actuals receive a new version. Issuance, input cutoffs,
ownership labels and original manifests are retained. Tonight's forecasts are registered
but unscored. No missing forecast is reconstructed; absent conditional outcomes are not zero.

The derived scoreboard uses the review's canonical forecast per date and one actuals
vintage, so revisions and repeated issuances are not double-counted. Separate player,
fantasy, team and eligible goalie-start populations are shown. The October 17 export-only
cohort and older October 9 trials remain in their separate research reports. This first
scoreboard covers full daily bundles only. Rates are not pooled across goalie exposures.
Probability calibration, interval coverage and paired uncertainty remain in the detailed
evaluation reports; this CSV summarizes count errors, not proof of a model improvement.
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        through=review['through'], review=str(a.review), review_sha256=digest(a.review/'manifest.json'),
        actuals_manifest_sha256=review['actuals_sha256'],
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}), indent=2)+'\n')
    print('Scoreboard:', a.out)


if __name__ == '__main__':
    main()
