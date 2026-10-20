#!/usr/bin/env python3
"""Score frozen experimental team SOG forecasts after official games finish."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest
from src.fantasy.feature_screen import paired_delta
from src.fantasy.per_game import require


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['evidence','actuals','out']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();require(not a.out.exists(),'Preserve earlier evaluations')
    em=verify_manifest_files(a.evidence,[]);verify_manifest_files(a.actuals,[])
    forecast=pd.read_csv(a.evidence/'tonight_experimental_team_forecasts.csv')
    require(not forecast.duplicated(['game_id','team','model']).any(),'Duplicate forecast')
    require((pd.to_datetime(forecast.issued_at_utc,utc=True)+pd.Timedelta(minutes=10)<pd.to_datetime(forecast.start_time_utc,utc=True)).all(),'Trial was not released with pregame lead')
    require(forecast.game_date.eq(em['target_date']).all(),'Target date mismatch')
    actual=pd.read_csv(a.actuals/'skater_game_stats.csv');require(not actual.duplicated(['game_id','player_id']).any(),'Duplicate actual appearance')
    actual=actual[actual.game_date.eq(em['target_date']) & actual.toi_seconds.gt(0)]
    totals=actual.groupby(['game_id','team']).shots.sum().rename('actual_shots').reset_index()
    require(len(totals)>0,'No completed target-date games; acquire official final actuals first')
    require(totals.groupby('game_id').size().eq(2).all(),'Incomplete final team pair')
    scored=forecast.merge(totals,on=['game_id','team'],how='left',validate='many_to_one')
    coverage=scored.groupby(['game_id','team']).actual_shots.first().reset_index();coverage['scored']=coverage.actual_shots.notna()
    scored=scored[scored.actual_shots.notna()].copy()
    scored['error']=scored.experimental_team_sog-scored.actual_shots;scored['absolute_error']=scored.error.abs()
    require(np.isfinite(scored[['experimental_team_sog','actual_shots']]).all().all(),'Invalid counts')
    metrics=scored.groupby('model').agg(team_rows=('team','size'),games=('game_id','nunique'),mae=('absolute_error','mean'),bias=('error','mean')).reset_index()
    deltas=paired_delta(scored)
    a.out.mkdir(parents=True)
    for name,frame in [('scored_predictions',scored),('metrics',metrics),('paired_uncertainty',deltas),('coverage',coverage)]:frame.to_csv(a.out/(name+'.csv'),index=False)
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),target_date=em['target_date'],
        evidence_manifest_sha256=digest(a.evidence/'manifest.json'),actuals_manifest_sha256=digest(a.actuals/'manifest.json'),
        completed_games=int(scored.game_id.nunique()),unscored_games=int(coverage[~coverage.scored].game_id.nunique()),
        selection='All frozen variants, same completed games; no postgame refit',
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print(metrics.to_string(index=False));print('Unscored games:',coverage[~coverage.scored].game_id.nunique())


if __name__=='__main__':main()
