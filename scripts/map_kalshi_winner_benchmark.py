#!/usr/bin/env python3
"""Map timestamped public winner quotes to official fixtures; never place orders."""
import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['snapshot','probabilities','out']:ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve previous benchmarks')
    km=verify_manifest_files(a.snapshot,[]);pm=verify_manifest_files(a.probabilities,[])
    forecast=pd.read_csv(a.probabilities/'team_win_probabilities.csv')
    market=pd.read_csv(a.snapshot/'markets.csv');market=market[market.series.eq('KXNHLGAME')]
    raw=Path(km['raw_snapshot']);contracts={}
    for s in km['sources']:
        p=raw/s['file']
        if digest(p)!=s['sha256']:raise ValueError('Changed contract source')
        for m in json.loads(p.read_text())['markets']:contracts[m['ticker']]=m
    codes={'LAK':'LA','NJD':'NJ','SJS':'SJ','TBL':'TB'}
    rows=[]
    for f in forecast.itertuples():
        day=pd.Timestamp(f.date).strftime('%y%b%d').upper()
        home=codes.get(f.home,f.home);away=codes.get(f.away,f.away)
        # Explicit aliases, both official teams, and exact date; no fuzzy matching.
        events={f'KXNHLGAME-{day}{home}{away}',f'KXNHLGAME-{day}{away}{home}'}
        for team,code,prob in [(f.home,home,f.home_win_probability),(f.away,away,f.away_win_probability)]:
            candidates=market[market.event_ticker.isin(events)&market.ticker.str.endswith('-'+code)]
            if len(candidates)!=1:raise ValueError(f'Ambiguous/missing winner market: {f.game_id} {team}')
            q=candidates.iloc[0];c=contracts[q.ticker]
            if pd.Timestamp(q.sampled_at_utc)>=pd.Timestamp(f.start_time_utc):raise ValueError('Live quote cannot be pregame')
            if 'official final result' not in c.get('rules_secondary','').lower():
                raise ValueError('Settlement rules require review')
            rows.append(dict(game_id=f.game_id,date=f.date,start_time_utc=f.start_time_utc,team=team,
                ticker=q.ticker,contract_title=q.title,yes_sub_title=c.get('yes_sub_title'),
                sampled_at_utc=q.sampled_at_utc,model_issued_at_utc=f.issued_at_utc,
                model_probability=prob,yes_bid=q.yes_bid,yes_ask=q.yes_ask,quoted_midpoint=q.quoted_midpoint,
                spread=q.spread,volume=q.volume,open_interest=q.open_interest,two_sided_quote=q.two_sided_quote,
                rules_primary=c.get('rules_primary'),rules_secondary=c.get('rules_secondary'),
                market_updated_at=c.get('updated_time'),last_trade_time=None,orderbook_depth=None,
                status='pregame_quote_benchmark_not_model_input'))
    out=pd.DataFrame(rows)
    if out.duplicated(['game_id','team']).any():raise ValueError('Duplicate mapped contract')
    a.out.mkdir(parents=True);out.to_csv(a.out/'winner_benchmark.csv',index=False)
    (a.out/'README.md').write_text(f'''# Kalshi winner benchmark — {pm['date']}

Mapped {len(out)} contracts to {out.game_id.nunique()} official NHL games using exact dates,
team aliases and two-team fixture identities. Quotes were sampled before official game starts.
[Quotes, model probabilities, contract rules and source timestamps](winner_benchmark.csv).

This snapshot maps {out.game_id.nunique()} games and {len(out)} team contracts. Median quoted spread is {out.spread.median():.3f}; each row records its own sample time. Quotes are a same-day benchmark for review, not inputs to the NHL forecasts.

Contracts settle on official final winners, with postponement/cancellation provisions retained per row.
This benchmark assumes a normally completed fixture; void/fair-price resolutions must be excluded from
ordinary win/loss scoring. Raw contract text remains authoritative. Home/away quoted midpoints need not
sum to one. Midpoints are quoted prices, not calibrated probabilities or executable prices.
The model and market snapshots are close in time but not simultaneous. Order-book depth and last-trade
time are unavailable in this snapshot; market update time is not a trade timestamp. No blended forecast,
betting recommendation or historical pregame claim. Evaluate future model-only and market-only scores
on identical settled games before testing a blend with chronological training.

[Kalshi historical data documentation](https://docs.kalshi.com/getting_started/historical_data)
describes live/archive cutoffs. Backfill must use candles ending before an explicitly fixed NHL pregame
cutoff; final settlement prices cannot substitute for pregame probabilities.
''')
    display=['date','team','ticker','sampled_at_utc','model_probability','yes_bid','yes_ask','quoted_midpoint','spread','volume','open_interest']
    headings=''.join(f'<th>{escape(col.replace("_", " ").title())}</th>' for col in display)
    body=[]
    for row in out[display].itertuples(index=False,name=None):
        cells=[]
        for value in row:
            if pd.isna(value):shown='—'
            elif isinstance(value,(float,int)):shown=f'{value:.3f}'
            else:shown=str(value)
            cells.append(f'<td>{escape(shown)}</td>')
        body.append('<tr>'+''.join(cells)+'</tr>')
    (a.out/'index.html').write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Kalshi pregame quote benchmark</title><style>body{font:15px system-ui;color:#172c38;max-width:1280px;margin:28px auto;padding:20px;line-height:1.5}a{color:#08777c}h1{color:#087e83}main{overflow:auto}table{border-collapse:collapse;font-size:12px}th,td{padding:8px;border-bottom:1px solid #d5e1e6;text-align:right;white-space:nowrap}th{background:#f1f6f7}td:nth-child(3),td:nth-child(4){text-align:left}</style></head><body><main>'
        f'<p><a href="../../team-model/">Today’s NHL team model</a> · <a href="../november_model_review_2026-11-10/">November model review</a></p>'
        f'<h1>Kalshi winner quotes — {pm["date"]}</h1>'
        f'<p>{out.game_id.nunique()} games, {len(out)} team contracts, median spread {out.spread.median():.3f}. Quotes were sampled before puck drop and mapped by exact date and team fixture. They were not model inputs.</p>'
        '<p>A quoted midpoint is not a calibrated probability or executable price. These are same-day quotes, not historical pregame prices for earlier forecast dates. The source CSV preserves contract text, timestamps, volume and open interest.</p>'
        f'<p><a href="winner_benchmark.csv">Full mapped quotes and model probabilities</a> · <a href="README.md">Methods and limitations</a></p>'
        f'<table><thead><tr>{headings}</tr></thead><tbody>{"".join(body)}</tbody></table>'
        '</main></body></html>')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        snapshot=str(a.snapshot),snapshot_sha256=digest(a.snapshot/'manifest.json'),probabilities=str(a.probabilities),
        probabilities_sha256=digest(a.probabilities/'manifest.json'),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print('Mapped games:',out.game_id.nunique(),'Contracts:',len(out),'Median spread:',out.spread.median())


if __name__=='__main__':main()
