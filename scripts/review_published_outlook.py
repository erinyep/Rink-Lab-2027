#!/usr/bin/env python3
"""Evaluate published team/goalie exports when the full issued bundle is absent.

Keep declared issuance and conservative publication-time evidence separate.
Never fabricate the unpublished full player population or silently fuzzy-match IDs.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import digest,verify_manifest_files
from scripts.review_forecast_week import summarize
from scripts.evaluate_october_9 import table


def name_key(value):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['view','actuals','pbp','out']: ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args(); vm=json.loads((a.view/'manifest.json').read_text())
    if vm['date'] != '2026-10-17': raise ValueError('This recovery audit is specifically for the October 17 export')
    verify_manifest_files(a.actuals,[]); pm=verify_manifest_files(a.pbp,[])
    for filename in ['team_predictions.csv','goalie_scenarios.csv','outlook.json']:
        if digest(a.view/filename)!=vm['files'][filename]: raise ValueError('Changed published forecast: '+filename)
    sk=pd.read_csv(a.actuals/'skater_game_stats.csv'); gl=pd.read_csv(a.actuals/'goalie_game_stats.csv')
    t=pd.read_csv(a.view/'team_predictions.csv'); t['scope']='declared_pregame'
    t=t[t.issue_timing.eq('pregame') & (pd.to_datetime(t.start_time_utc,utc=True)>pd.Timestamp(vm['forecast_issued_utc']))]
    stats=sk[sk.toi_seconds.gt(0)].groupby(['game_id','team'])[['goals','assists','shots','hits','points','pp_points']].sum().add_prefix('actual_').reset_index()
    t=t.merge(stats,on=['game_id','team'],validate='many_to_one')
    t['publication_safe']=pd.to_datetime(t.start_time_utc,utc=True)>pd.Timestamp(vm['view_created_utc'])
    tm=[]
    for scope,z in [('declared_pregame',t),('publication_safe',t[t.publication_safe])]:
        for c in ['goals','assists','shots','hits','points','pp_points']:
            m=summarize(z,['model'],'expected_'+c,'actual_'+c); m['category']=c;m['scope']=scope;tm.append(m)
    # Name-to-ID resolution is constrained to official same-game goalie rosters.
    raw=Path(pm['raw_snapshot']); lookup={}
    for gid in set(t.game_id):
        game=json.loads((raw/f'play_by_play_{gid}.json').read_text())
        teams={game[k]['id']:game[k]['abbrev'] for k in ['homeTeam','awayTeam']}
        for p in game['rosterSpots']:
            if p['positionCode']!='G': continue
            key=(gid,teams[p['teamId']],name_key(p['firstName']['default']+' '+p['lastName']['default']))
            if key in lookup and lookup[key]!=p['playerId']: raise ValueError('Ambiguous official goalie name')
            lookup[key]=p['playerId']
    g=pd.read_csv(a.view/'goalie_scenarios.csv'); starts=t[['game_id','start_time_utc']].drop_duplicates()
    g=g[g.issue_timing.eq('pregame')].merge(starts,on='game_id',validate='many_to_one')
    g['player_id']=[lookup.get((r.game_id,r.team,name_key(r.player_name))) for r in g.itertuples()]
    g['mapping_status']=g.player_id.notna().map({True:'same_game_official_roster_name',False:'unresolved_not_scored'})
    g=g.merge(gl[['game_id','player_id','starter','saves','goals_against','count_identity_ok']],
        on=['game_id','player_id'],how='left',validate='many_to_one')
    g['publication_safe']=pd.to_datetime(g.start_time_utc,utc=True)>pd.Timestamp(vm['view_created_utc'])
    gm=[]
    for scope,z in [('declared_pregame',g),('publication_safe',g[g.publication_safe])]:
        z=z[z.starter.eq(True)&z.count_identity_ok.eq(True)]
        for c in ['saves','goals_against']:
            m=summarize(z,['model'],c+'_if_full_start',c); m['category']=c;m['scope']=scope;gm.append(m)
    a.out.mkdir(parents=True,exist_ok=True)
    if (a.out/'published_october_17_metrics.csv').exists(): raise ValueError('Published evaluation exists; preserve it')
    metrics=pd.concat(tm); goalie=pd.concat(gm)
    metrics.to_csv(a.out/'published_october_17_metrics.csv',index=False)
    goalie.to_csv(a.out/'published_october_17_goalie_metrics.csv',index=False)
    g.to_csv(a.out/'published_october_17_goalie_mapping.csv',index=False)
    notes=(f'# Additional October 17 evidence from the newer repository\n\n'
        f'The published export declares issuance at {vm["forecast_issued_utc"]}; the view was created at {vm["view_created_utc"]}. '
        f'It has {t.game_id.nunique()} declared pregame games, of which {t[t.publication_safe].game_id.nunique()} '
        'were still future when the exported view was created. One earlier game is explicitly late and excluded. '
        'The full raw October 17 bundle remains on the other machine; its source-manifest hash is recorded in the published manifest. '
        'The exported prediction CSV hashes verify, but we cannot independently inspect the absent bundle or recover every player forecast.\n\n'
        '## Team shots\n\n'+table(metrics[metrics.category.eq('shots')][['scope','model','rows','games','mae','bias']])+'\n\n'
        'Use publication_safe for conservative comparative evidence; declared_pregame depends on the saved issuance claim. '
        'Do not merge these exported team observations into the full-player sample. '
        'All six exported team categories are scored in [metrics](published_october_17_metrics.csv).\n\n'
        '## Goalies\n\n'+table(goalie[['scope','model','category','rows','games','mae','bias']])+'\n\n'
        f'{int(g.player_id.isna().sum())} goalie/model rows remain unresolved. IDs use exact normalized full names on '
        'the official same-game NHL PBP goalie roster. [Mapping and observed roles](published_october_17_goalie_mapping.csv) '
        'retain every candidate; headline counts use actual starters with valid count identities only. '
        'The public export contains saves and GA means, so no unexported per-player/SA forecast is invented.\n\n'
        'Next: transfer the immutable raw and processed October 17 forecast bundle to enable full player evaluation, '
        'fantasy subgroups and issue-time/source verification. The existing interactive matchup and category-report work is preserved.\n')
    (a.out/'published_october_17.md').write_text(notes)
    readme=a.out/'README.md'; readme.write_text(readme.read_text()+'\n## Newer repository evidence\n\n[October 17 published team and goalie evaluation](published_october_17.md) adds evidence beyond the locally restored bundles.\n')
    m=json.loads((a.out/'manifest.json').read_text());m['published_outlook_source']=dict(path=str(a.view),manifest_sha256=digest(a.view/'manifest.json'),forecast_issued_utc=vm['forecast_issued_utc'],view_created_utc=vm['view_created_utc'])
    m['files']={p.name:digest(p) for p in a.out.iterdir() if p.is_file() and p.name!='manifest.json'}
    (a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print('Published October 17 evaluation:',a.out/'published_october_17.md')


if __name__=='__main__':main()
