#!/usr/bin/env python3
"""Attach compact source-quality tables and a defense chart to a season review."""
import argparse
import json
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest
from scripts.evaluate_october_9 import table
from src.fantasy.play_by_play import lagged_shot_quality


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['pbp','shots','kalshi','out']: ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--before',required=True)
    a=ap.parse_args()
    for p in [a.pbp,a.shots,a.kalshi,a.out]: verify_manifest_files(p,[])
    if (a.out/'source_quality.md').exists(): raise ValueError('Source audit exists; preserve published files')
    pm=json.loads((a.pbp/'manifest.json').read_text()); sm=json.loads((a.shots/'manifest.json').read_text())
    q=lagged_shot_quality(pd.read_csv(a.shots/'defense_shot_quality_team_games.csv'),a.before)
    k=pd.read_csv(a.kalshi/'series_coverage.csv').fillna({'markets':0,'two_sided_quotes':0})
    q.to_csv(a.out/'defense_shot_quality_context.csv',index=False)
    k.to_csv(a.out/'kalshi_series_coverage.csv',index=False)
    for folder,name in [(a.pbp,'nhl_pbp_source_audit'),(a.shots,'moneypuck_shots_source_audit')]:
        pd.read_csv(folder/'source_audit.csv').to_csv(a.out/(name+'.csv'),index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,6))
    z=q[q.strength.eq('all') & q.games_used.gt(0)]
    ax.scatter(z.defense_unblocked_attempts_per_game,z.defense_xg_per_game,s=15+z.games_used*8,color='#246b88',alpha=.7)
    for row in z.itertuples(): ax.annotate(row.team,(row.defense_unblocked_attempts_per_game,row.defense_xg_per_game),xytext=(3,3),textcoords='offset points',fontsize=8)
    ax.set(xlabel='D unblocked attempts / usable game',ylabel='D expected goals / usable game',
        title='Defense shot volume and quality — MoneyPuck.com\nAudited past games only; marker size reflects games used')
    fig.tight_layout(); fig.savefig(a.out/'defense_shot_quality.png',dpi=150); plt.close(fig)
    text=('# Source-quality audit\n\n'
        f'Official NHL PBP: {pm["games"]} games, {pm["events"]:,} attempts; '
        f'{pm["sog_disagreement_team_games"]} team-game SOG discrepancies. Both affected games excluded from derived context.\n\n'
        f'MoneyPuck.com shot download: {sm["eligible_games"]} games, {sm["eligible_rows"]:,} unblocked events, '
        f'{sm["columns"]} original columns. {len(sm["quarantined_games"])} games quarantined for an official team SOG disagreement. '
        f'{sm["missing_positions"]} raw positions missing, {sm["unresolved_positions"]} remain unresolved after the documented same-game NHL fallback.\n\n'
        '[Official PBP reconciliation](nhl_pbp_source_audit.csv) · [MoneyPuck reconciliation](moneypuck_shots_source_audit.csv). '
        'Retain source differences rather than modifying raw values to match.\n\n'
        '## Defense shot quality\n\n![Defense shot quality](defense_shot_quality.png)\n\n'
        '[Team values and usable/quarantined sample sizes](defense_shot_quality_context.csv). '
        'Both axes use the same usable games within each team. Samples differ across teams and schedules; '
        'this is descriptive, not a ranking of talent or evidence of predictive benefit. Credit MoneyPuck.com.\n\n'
        '## Kalshi series coverage\n\n'+table(k)+'\n\n'
        'A public current snapshot, not historical pregame quotes. Empty requested series do not establish absence of '
        'equivalent contracts elsewhere. Volume, wide spreads, mapping and quote timing need work before any feature use. '
        'No account access, orders or model changes.\n\n'
        '[Detailed source priorities and experiment design](../../../docs/DATA_SOURCE_STRATEGY.md).\n')
    (a.out/'source_quality.md').write_text(text)
    report=a.out/'README.md'; report.write_text(report.read_text()+'\n## Additional source audit\n\n[MoneyPuck shot quality, Kalshi coverage and source discrepancies](source_quality.md).\n')
    m=json.loads((a.out/'manifest.json').read_text())
    m['source_quality_inputs']={str(p):digest(p/'manifest.json') for p in [a.pbp,a.shots,a.kalshi]}
    m['files']={p.name:digest(p) for p in a.out.iterdir() if p.is_file() and p.name!='manifest.json'}
    (a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print('Source audit:',a.out/'source_quality.md')


if __name__=='__main__': main()
