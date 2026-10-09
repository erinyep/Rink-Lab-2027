#!/usr/bin/env python3
"""Reconcile game aggregates with latest authoritative player-season observations."""
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fantasy-games',type=Path,required=True)
    parser.add_argument('--forecast',type=Path,required=True)
    args=parser.parse_args()
    games=pd.read_csv(args.fantasy_games/'skater_game_stats.csv')
    games=games[games.toi_seconds>0].copy()
    categories=['goals','assists','points','shots','hits','penalty_minutes','plus_minus','pp_points','toi_minutes']
    aggregate=games.groupby('player_id')[categories].sum()
    aggregate['games_played']=games.groupby('player_id').size()
    season=pd.read_csv(args.forecast/'current_observed_stats.csv')
    audit=season[['player_id','skater_full_name','games_played']+categories].merge(aggregate.reset_index(),
        on='player_id',how='outer',suffixes=('_season','_games'),indicator=True,validate='one_to_one')
    checks=[]
    for c in ['games_played']+categories:
        audit[f'{c}_matches']=np.isclose(audit[f'{c}_season'],audit[f'{c}_games'],rtol=0,atol=.02 if c=='toi_minutes' else 0)
        checks.append(dict(category=c,players=len(audit),matching=int(audit[f'{c}_matches'].sum()),
                           exceptions=int((~audit[f'{c}_matches']).sum())))
    audit.to_csv(args.fantasy_games/'cumulative_skater_audit.csv',index=False)
    pd.DataFrame(checks).to_csv(args.fantasy_games/'cumulative_category_audit.csv',index=False)
    (args.fantasy_games/'cumulative_audit_provenance.json').write_text(json.dumps(dict(
        game_sources=str(args.fantasy_games),season_observations=str(args.forecast),
        note='Different retrieval times can contain source corrections; discrepancies are retained, not repaired.'),indent=2)+'\n')
    print(pd.DataFrame(checks).to_string(index=False))


if __name__=='__main__':
    main()
