#!/usr/bin/env python3
"""Acquire published MoneyPuck unblocked shots and audit D shot-quality inputs.

Credit MoneyPuck.com. Raw outcome/future-event columns are preserved but not
used as contemporaneous predictors. Only lagged aggregates are candidates.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import ssl
import zipfile
from urllib.request import Request,urlopen
import numpy as np
import pandas as pd
import truststore


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--season',type=int,default=2026); ap.add_argument('--download',type=Path)
    ap.add_argument('--boxscores',type=Path,required=True)
    a=ap.parse_args(); stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    url=f'https://peter-tanner.com/moneypuck/downloads/shots_{a.season}.zip'
    raw=Path('data/raw/moneypuck/snapshots')/f'shots_{a.season}_{stamp}'; raw.mkdir(parents=True)
    path=raw/'shots.zip'
    if a.download: shutil.copyfile(a.download,path)
    else:
        with urlopen(Request(url,headers={'User-Agent':'Rink-Lab/0.1 research'}),context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=180) as r,path.open('wb') as f: shutil.copyfileobj(r,f)
    with zipfile.ZipFile(path) as z:
        name=f'shots_{a.season}.csv'
        f=pd.read_csv(z.open(name)).copy()
    raw_columns=len(f.columns)
    # shotID is not globally unique in the published season file.
    if f.duplicated(['game_id','shotID']).any() or not f.season.eq(a.season).all(): raise ValueError('Shot ID/season invalid')
    for column in ['xGoal','xRebound','shotWasOnGoal']:
        if not (np.isfinite(f[column]) & f[column].between(0,1)).all():
            raise ValueError('Invalid probability/count flag: '+column)
    f['nhl_game_id']=a.season*1000000+f.game_id
    bm=json.loads((a.boxscores/'metadata.json').read_text()); boxes={}
    for source in bm['sources']:
        if not source['file'].startswith('boxscore_'): continue
        p=a.boxscores/source['file']
        if sha(p)!=source['sha256']: raise ValueError('Changed official boxscore')
        b=json.loads(p.read_text()); boxes[b['id']]=b
    eligible=f[f.nhl_game_id.isin(boxes) & f.isPlayoffGame.eq(0)].copy()
    aliases={'T.B':'TBL','L.A':'LAK','S.J':'SJS','N.J':'NJD'}
    eligible['team']=eligible.teamCode.replace(aliases)
    eligible['game_date']=eligible.nhl_game_id.map({gid:b['gameDate'] for gid,b in boxes.items()})
    official_positions={(gid,p['playerId']):p['position'] for gid,b in boxes.items()
        for side in ['homeTeam','awayTeam'] for group in ['forwards','defense'] for p in b['playerByGameStats'][side][group]}
    # Preserve raw missing position; derive a labeled fallback from the same
    # game's official participant roster rather than classifying unknowns as F.
    eligible['official_position']=[official_positions.get((r.nhl_game_id,r.shooterPlayerId)) for r in eligible.itertuples()]
    eligible['resolved_position']=eligible.playerPositionThatDidEvent.fillna(eligible.official_position)
    eligible['is_defense']=eligible.resolved_position.eq('D')
    eligible['five_on_five']=eligible.homeSkatersOnIce.eq(5)&eligible.awaySkatersOnIce.eq(5)&eligible.homeEmptyNet.eq(0)&eligible.awayEmptyNet.eq(0)
    audit=[]
    for gid,b in boxes.items():
        for side in ['homeTeam','awayTeam']:
            t=b[side]['abbrev']; e=eligible[(eligible.nhl_game_id==gid)&(eligible.team==t)]
            audit.append(dict(game_id=gid,team=t,shots=len(e),moneypuck_sog=int(e.shotWasOnGoal.sum()),official_sog=b[side]['sog'],
                sog_match=len(e)>0 and int(e.shotWasOnGoal.sum())==b[side]['sog']))
    audit=pd.DataFrame(audit); bad=set(audit.loc[~audit.sog_match,'game_id'])
    # Preserve all source discrepancies; exclude both teams from usable quality aggregates.
    rows=[]
    for (team,gid),e in eligible.groupby(['team','nhl_game_id']):
        for strength in ['all','5v5']:
            g=e if strength=='all' else e[e.five_on_five]
            d=g[g.is_defense]
            rows.append(dict(team=team,game_id=gid,game_date=e.game_date.iloc[0],strength=strength,
                source_quarantined=gid in bad,team_unblocked_attempts=len(g),team_xg=float(g.xGoal.sum()),
                defense_unblocked_attempts=len(d),defense_xg=float(d.xGoal.sum()),
                defense_expected_rebounds=float(d.xRebound.sum()),defense_empty_net_attempts=int(d.shotOnEmptyNet.sum())))
    out=Path('data/processed/forecasts')/f'moneypuck_shots_{stamp}'; out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(out/'defense_shot_quality_team_games.csv',index=False)
    audit.to_csv(out/'source_audit.csv',index=False)
    meta=dict(url=url,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),sha256=sha(path),
        source='MoneyPuck.com published unblocked-shot data',license='Non-commercial research with MoneyPuck.com attribution',
        raw_snapshot=str(raw),boxscores=str(a.boxscores),rows=len(f),columns=raw_columns,eligible_rows=len(eligible),
        eligible_games=eligible.nhl_game_id.nunique(),official_games=len(boxes),quarantined_games=sorted(bad),
        missing_shooter_ids=int(eligible.shooterPlayerId.isna().sum()),missing_positions=int(eligible.playerPositionThatDidEvent.isna().sum()),
        unresolved_positions=int(eligible.resolved_position.isna().sum()),
        position_fallback='same-game official NHL boxscore position for missing MoneyPuck positions only',
        missing_official_games=sorted(set(boxes)-set(eligible.nhl_game_id)),
        min_xg=float(eligible.xGoal.min()),max_xg=float(eligible.xGoal.max()),
        limitations=['Blocked attempts absent by source design.', 'Corrected downloaded xG is not a historical as-of model score.',
            'No same-event outcome/future-event columns used as predictors; no forecast coefficient fitted.'])
    (raw/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    meta['files']={p.name:sha(p) for p in out.glob('*.csv')}
    (out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('MoneyPuck shots output:',out)
    print('Eligible games:',eligible.nhl_game_id.nunique(),'Unblocked shots:',len(eligible),'Quarantined games:',len(bad))


if __name__=='__main__': main()
