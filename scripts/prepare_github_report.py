#!/usr/bin/env python3
"""Package only displayed report fields for a static GitHub Pages snapshot."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=Path('docs/report'))
    args=parser.parse_args()
    manifest=json.loads((args.report/'manifest.json').read_text())
    for filename,expected in manifest['files'].items():
        if sha(args.report/filename)!=expected:raise ValueError('Report source hash mismatch: '+filename)
    data=json.loads((args.report/'report.json').read_text())
    means=['expected_'+c['model_event']+'_if_plays' for c in data['categories'] if c['model_event']]
    fields={
        'roster':['player_name','lineup_slot','injury_status','decision_state','start_local','is_goalie','has_game','locked','blocked']+means,
        'streamers':['player_name','primary_position','start_local','open_slot_fit','historical_gp','usable_starts_today','team','opponent']+means,
        'goalies':['player_name','lineup_slot','injury_status','start_share_provisional','saves_if_full_start','goals_against_if_full_start','save_percentage_projection'],
        'schedule':['player_name','date','opponent'],
        'future_roster':['player_name'],
    }
    for key,allowed in fields.items():
        data[key]=[{k:r.get(k) for k in allowed} for r in data[key]]
    args.out.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(data,separators=(',',':'),allow_nan=False)
    (args.out/'report.json').write_text(payload+'\n')
    template=Path('templates/fantasy_today.html').read_text()
    (args.out/'index.html').write_text(template.replace('__REPORT_DATA__',payload.replace('</','<\\/')))
    for key,filename in [('roster','roster.csv'),('streamers','streamer_watchlist.csv'),('goalies','goalies.csv'),('schedule','roster_schedule.csv'),('matchup','category_gaps.csv')]:
        rows=data[key]
        with (args.out/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['player_name'])
            writer.writeheader();writer.writerows(rows)
    (args.out/'manifest.json').write_text(json.dumps(dict(date=data['date'],report_created_at=data['created_at'],
        source_report_sha256=sha(args.report/'report.json'),scope='Displayed fantasy report fields only; no credentials, raw API snapshots or local filesystem paths.',
        files={p.name:sha(p) for p in args.out.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    print('Prepared Pages report:',args.out/'index.html')


if __name__=='__main__':main()
