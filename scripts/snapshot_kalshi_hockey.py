#!/usr/bin/env python3
"""Read-only public hockey market benchmark acquisition; no account/API key.

Never calls trading endpoints. Prices are not mapped to NHL games or used by
forecasts. Current snapshots cannot supply historical pregame prices.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import time
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import pandas as pd
import truststore

BASE='https://external-api.kalshi.com/trade-api/v2'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--series',nargs='+',default=['KXNHLGAME','KXNHLTOTAL','KXNHLTEAMTOTAL','KXNHLSAVES','KXNHLAST','KXNHLPTS','KXNHLANYGOAL'])
    a=ap.parse_args(); started=datetime.now(timezone.utc)
    raw=Path('data/raw/kalshi/snapshots')/started.strftime('hockey_%Y%m%dT%H%M%S%fZ'); raw.mkdir(parents=True)
    rows=[]; sources=[]
    for series in a.series:
        cursor=''; seen=set(); page=0
        while True:
            params=dict(series_ticker=series,status='open',limit=1000)
            if cursor: params['cursor']=cursor
            url=BASE+'/markets?'+urlencode(params)
            for attempt in range(3):
                try:
                    with urlopen(Request(url,headers={'User-Agent':'Rink-Lab/0.1 research'}),context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=60) as r: payload=r.read()
                    break
                except Exception:
                    if attempt==2: raise
                    time.sleep(2**attempt)
            data=json.loads(payload); path=raw/f'{series}_{page}.json'; path.write_bytes(payload)
            sources.append(dict(file=path.name,url=url,sha256=hashlib.sha256(payload).hexdigest()))
            for m in data['markets']:
                bid=float(m.get('yes_bid_dollars') or 0); ask=float(m.get('yes_ask_dollars') or 0)
                valid=0<bid<=ask<1
                rows.append(dict(series=series,ticker=m['ticker'],event_ticker=m['event_ticker'],title=m['title'],
                    yes_bid=bid,yes_ask=ask,spread=ask-bid if valid else None,
                    quoted_midpoint=(ask+bid)/2 if valid else None,two_sided_quote=valid,
                    volume=float(m.get('volume_fp') or 0),open_interest=float(m.get('open_interest_fp') or 0),
                    close_time=m['close_time'],status=m['status'],
                    sampled_at_utc=datetime.now(timezone.utc).isoformat(),nhl_game_id=None,mapping_status='unmapped_do_not_use_in_forecast'))
            cursor=data.get('cursor') or ''
            if not cursor: break
            if cursor in seen: raise ValueError('Kalshi pagination cursor repeated')
            seen.add(cursor); page+=1
    f=pd.DataFrame(rows)
    if f.empty or f.ticker.duplicated().any(): raise ValueError('Empty/duplicate market acquisition')
    out=Path('data/processed/forecasts')/raw.name; out.mkdir(parents=True)
    f.to_csv(out/'markets.csv',index=False)
    summary=f.groupby('series').agg(markets=('ticker','size'),two_sided_quotes=('two_sided_quote','sum'),
        median_spread=('spread','median'),median_volume=('volume','median')).reindex(a.series).reset_index()
    summary.to_csv(out/'series_coverage.csv',index=False)
    meta=dict(started_at_utc=started.isoformat(),completed_at_utc=datetime.now(timezone.utc).isoformat(),
        raw_snapshot=str(raw),requested_series=a.series,sources=sources,pagination_complete=True,
        limitations=['Current public open-market snapshot only; no historical pregame claim.',
            'Contract close is not NHL game start. Explicit contract/player/game mapping and rules review required.',
            'Midpoint is a quoted price, not a validated probability. Inspect spread, volume, depth and last-trade time.',
            'No orders, account access, fees simulation or model input.'])
    (raw/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    meta['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}
    (out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Kalshi snapshot:',out); print(summary.to_string(index=False))


if __name__=='__main__': main()
