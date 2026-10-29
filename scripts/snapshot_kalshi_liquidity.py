#!/usr/bin/env python3
"""Preserve public depth and paginated trades for mapped pregame winner markets.

This is a second observation after the quoted benchmark, never a replacement
for it. Only public GET endpoints are used; no account credentials are read.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import ssl
import sys
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import truststore

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import digest, verify_manifest_files

BASE = 'https://external-api.kalshi.com/trade-api/v2'


def summarize_book(payload):
    """YES ask is the complement of the best NO bid, with the same size."""
    book = payload['orderbook_fp']
    sides = {}
    for side in ['yes', 'no']:
        levels = [(float(p), float(q)) for p, q in (book[side + '_dollars'] or [])]
        if any(not np.isfinite([p, q]).all() or not 0 <= p <= 1 or q <= 0 for p, q in levels):
            raise ValueError('Invalid orderbook price/quantity')
        if len({p for p, _ in levels}) != len(levels):
            raise ValueError('Duplicate orderbook price level')
        sides[side] = sorted(levels, reverse=True)
    yes, no = sides['yes'], sides['no']
    bid = yes[0][0] if yes else None
    ask = 1 - no[0][0] if no else None
    return dict(depth_yes_bid=bid, depth_yes_ask=ask,
                best_yes_bid_quantity=yes[0][1] if yes else None,
                best_yes_ask_quantity=no[0][1] if no else None,
                yes_bid_levels=len(yes), no_bid_levels=len(no),
                total_yes_bid_quantity=sum(q for _, q in yes),
                total_no_bid_quantity=sum(q for _, q in no),
                depth_two_sided=bid is not None and ask is not None and 0 < bid <= ask < 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--benchmark', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise ValueError('Preserve previous observations')
    verify_manifest_files(a.benchmark, [])
    markets = pd.read_csv(a.benchmark / 'winner_benchmark.csv')
    if markets.empty or markets.ticker.duplicated().any():
        raise ValueError('Missing or duplicate mapped markets')
    started = datetime.now(timezone.utc)
    if (pd.to_datetime(markets.start_time_utc, utc=True) <= pd.Timestamp(started)).any():
        raise ValueError('Require entirely pregame observation')
    raw = Path('data/raw/kalshi/snapshots') / ('liquidity_' + started.strftime('%Y%m%dT%H%M%S%fZ'))
    raw.mkdir(parents=True)
    sources, rows = [], []

    def fetch(endpoint, filename):
        url = BASE + endpoint
        with urlopen(Request(url, headers={'User-Agent': 'Rink-Lab/0.1 research'}),
                     context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=60) as response:
            payload = response.read()
        path = raw / filename
        path.write_bytes(payload)
        sampled = datetime.now(timezone.utc).isoformat()
        sources.append(dict(file=filename, url=url, sha256=digest(path), sampled_at_utc=sampled))
        return json.loads(payload), sampled

    for market in markets.itertuples():
        row = dict(game_id=market.game_id, team=market.team, ticker=market.ticker,
                   start_time_utc=market.start_time_utc, benchmark_sampled_at_utc=market.sampled_at_utc,
                   last_trade_time=None, last_trade_age_minutes=None, trades_observed=None)
        try:
            payload, stamp = fetch('/markets/' + quote(market.ticker, safe='') + '/orderbook?depth=0',
                                   market.ticker + '_book.json')
            row.update(summarize_book(payload), depth_sampled_at_utc=stamp, depth_status='available')
        except HTTPError as error:
            # Public access differs by endpoint. Preserve explicit missingness.
            if error.code not in {401, 403, 404}:
                raise
            row.update(depth_status='http_' + str(error.code))
        trades, cursor, seen, page = [], '', set(), 0
        cutoff = datetime.now(timezone.utc)
        while True:
            params = dict(ticker=market.ticker, limit=1000, max_ts=int(cutoff.timestamp()))
            if cursor:
                params['cursor'] = cursor
            try:
                payload, stamp = fetch('/markets/trades?' + urlencode(params),
                                       market.ticker + f'_trades_{page}.json')
            except HTTPError as error:
                if error.code not in {401, 403, 404}:
                    raise
                row.update(trades_status='http_' + str(error.code), trade_pagination_complete=False)
                break
            trades.extend(payload['trades'])
            cursor = payload.get('cursor') or ''
            if not cursor:
                row.update(trades_status='available', trade_pagination_complete=True)
                break
            if cursor in seen:
                raise ValueError('Repeated trade pagination cursor')
            seen.add(cursor)
            page += 1
        if row['trade_pagination_complete']:
            if any(t['ticker'] != market.ticker for t in trades):
                raise ValueError('Trade ticker mismatch')
            if len({t['trade_id'] for t in trades}) != len(trades):
                raise ValueError('Duplicate trades')
            times = [pd.Timestamp(t['created_time']) for t in trades]
            if any(t > pd.Timestamp(cutoff) for t in times):
                raise ValueError('Future trade beyond request cutoff')
            last = max(times) if times else None
            row.update(trades_observed=len(trades), trade_cutoff_utc=cutoff.isoformat(),
                       last_trade_time=last.isoformat() if last is not None else None,
                       last_trade_age_minutes=(pd.Timestamp(cutoff)-last).total_seconds()/60 if last is not None else None)
        if pd.Timestamp(datetime.now(timezone.utc)) >= pd.Timestamp(market.start_time_utc):
            raise ValueError('Observation crossed puck drop')
        rows.append(row)
    a.out.mkdir(parents=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(a.out / 'winner_liquidity.csv', index=False)
    meta = dict(started_at_utc=started.isoformat(), completed_at_utc=datetime.now(timezone.utc).isoformat(),
                benchmark=str(a.benchmark), benchmark_sha256=digest(a.benchmark/'manifest.json'),
                raw_snapshot=str(raw), sources=sources, contracts=len(frame),
                limitations=['Depth and trades were sampled sequentially after the original quote benchmark.',
                             'Most recent available live-API trade; archived trades may be outside this endpoint.',
                             'No executable-price, fill, profitability, or calibrated-probability claim.'])
    (raw/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n')
    meta['files'] = {'winner_liquidity.csv': digest(a.out/'winner_liquidity.csv')}
    (a.out/'manifest.json').write_text(json.dumps(meta, indent=2)+'\n')
    print('Liquidity snapshot:', a.out)
    print(frame[['ticker', 'depth_status', 'trades_status', 'last_trade_age_minutes']].to_string(index=False))


if __name__ == '__main__':
    main()
