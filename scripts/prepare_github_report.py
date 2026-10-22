#!/usr/bin/env python3
"""Package only displayed report fields for a static GitHub Pages snapshot."""
import argparse
import csv
import hashlib
import json
from html import escape
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
        'goalies':['player_name','lineup_slot','injury_status','start_local','start_share_provisional','saves_if_full_start','goals_against_if_full_start','save_percentage_projection'],
        'schedule':['player_name','date','opponent'],
        'future_roster':['player_name'],
    }
    for key,allowed in fields.items():
        data[key]=[{k:r.get(k) for k in allowed} for r in data[key]]
    args.out.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(data,separators=(',',':'),allow_nan=False)
    (args.out/'report.json').write_text(payload+'\n')
    template=Path('templates/fantasy_today.html').read_text()
    rendered=template.replace('__REPORT_DATA__',payload.replace('</','<\\/'))
    rendered=rendered.replace('<body><main>','<body><main><nav><a href="../games/index.html">All NHL game predictions</a> · <strong>Your fantasy team</strong> · <a href="../evidence/">Feature evidence and player contributions</a> · <a href="../results/">Model results</a> · <a href="../history/model-priorities-2026-10-22.md">Performance-based model priorities</a></nav>',1)
    (args.out/'index.html').write_text(rendered)
    # Regenerate the README preview from the same snapshot as the interactive page.
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 {80+37*len(data["matchup"])}" font-family="system-ui,sans-serif" role="img" aria-label="Saved category comparison">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="18" y="28" font-size="18">Category comparison — {escape(data["date"])}</text>',
           '<text x="18" y="49" font-size="12" fill="#536874">You: teal · Opponent: gold · Saved standings, not forecasts</text>']
    for i, row in enumerate(data['matchup']):
        y = 78 + i*37
        if row['own'] is None or row['opponent'] is None:
            svg.append(f'<text x="18" y="{y+4}" font-size="13">{escape(row["category"])} · unavailable (no finite saved rate)</text>')
            continue
        low, high = min(0,row['own'],row['opponent']), max(1,row['own'],row['opponent'])
        x = lambda value: 115 + 240*(value-low)/(high-low)
        label = escape(row['category']) + (' ↓' if row['lower_is_better'] else '')
        svg += [f'<text x="18" y="{y+4}" font-size="13">{label}</text>',
                f'<line x1="115" x2="355" y1="{y}" y2="{y}" stroke="#d5e1e6"/>',
                f'<circle cx="{x(row["opponent"]):.2f}" cy="{y}" r="5" fill="#ce8722"/>',
                f'<circle cx="{x(row["own"]):.2f}" cy="{y}" r="5" fill="#087e83"/>',
                f'<text x="380" y="{y+4}" font-size="12">{row["own"]:.3f} / {row["opponent"]:.3f}</text>',
                f'<text x="565" y="{y+4}" font-size="12">{escape(row["status"])}</text>']
    (args.out/'category-gaps.svg').write_text('\n'.join(svg+['</svg>'])+'\n')
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
