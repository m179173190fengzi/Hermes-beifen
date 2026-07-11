#!/usr/bin/env python3
"""
三链TVL对比监控脚本
用法: python3 tvl_monitor.py
输出: Solana / BNB Chain / Robinhood 三条链的TVL对比，带柱状图和比例
"""

import json, requests, datetime, sys

def fetch_tvl():
    try:
        r = requests.get('https://api.llama.fi/chains', timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f'Error fetching TVL data: {e}')
        sys.exit(1)

def get_tvl(chains, display_name, keywords):
    for c in chains:
        name = c.get('name', '')
        if any(k in name.lower() for k in keywords):
            return float(c.get('tvl', 0))
    return 0

def format_tvl(tvl):
    if tvl > 1e9:
        return tvl / 1e9, 'B'
    return tvl / 1e6, 'M'

def main():
    chains = fetch_tvl()

    target_map = {
        'Solana': ['solana'],
        'BNB Chain': ['bnb chain', 'binance'],
        'Robinhood': ['robinhood'],
    }

    results = {}
    for display_name, keywords in target_map.items():
        tvl = get_tvl(chains, display_name, keywords)
        results[display_name] = tvl

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f'TVL对比 -- {now}')
    print()

    for chain, tvl in sorted(results.items(), key=lambda x: -x[1]):
        v, unit = format_tvl(tvl)
        bar_len = min(int(v / 5) if tvl > 1e9 else int(v / 20), 50)
        bar = '#' * bar_len
        print(f'{chain:15s}  ${v:>8.2f}{unit}  {bar}')

    if results.get('Robinhood', 0) > 0:
        print()
        print(f'Solana / Robinhood = {results["Solana"] / results["Robinhood"]:.0f}x')
        print(f'BNB / Robinhood    = {results["BNB Chain"] / results["Robinhood"]:.0f}x')

if __name__ == '__main__':
    main()
