#!/usr/bin/env python3
"""Map timestamped public winner quotes to official fixtures; never place orders."""
import argparse
from datetime import datetime, timezone
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
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        snapshot=str(a.snapshot),snapshot_sha256=digest(a.snapshot/'manifest.json'),probabilities=str(a.probabilities),
        probabilities_sha256=digest(a.probabilities/'manifest.json'),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print('Mapped games:',out.game_id.nunique(),'Contracts:',len(out),'Median spread:',out.spread.median())


if __name__=='__main__':main()
