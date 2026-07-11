#!/usr/bin/env python3
"""
Score all tokens from a gmgn-cli trending JSON dump.
Usage: python3 scripts/score_trending.py <chain> <json_file>
Output: scored report, sorted descending, >=75 highlighted.

Chain is used for display only (sol/bsc/robinhood).
Single token detail: cat token_info.json | python3 scripts/score_trending.py --detail
"""

import json, sys

CHAIN_EMOJI = {'sol': '\U0001f7e3', 'bsc': '\U0001f7e1', 'robinhood': '\U0001f7e2'}

def sf(v, default=0):
    if v is None: return default
    try: return float(v)
    except: return default
def si(v, default=0):
    if v is None: return default
    try: return int(v)
    except: return default

def s_bundler(v):
    v = sf(v)
    if v < 0.10: return 90
    if v < 0.20: return 70
    if v < 0.30: return 50
    return 20

def s_top10(v):
    v = sf(v)
    if v < 0.20: return 90
    if v < 0.40: return 70
    if v < 0.60: return 50
    return 20

def s_creator(v):
    return 90 if v == "creator_close" else 20

def s_renounced(v):
    if v is True or v == 1 or v == "1": return 80
    return 30

def s_smart(v):
    v = si(v)
    if v >= 10: return 95
    if v >= 5: return 80
    if v >= 2: return 60
    return 20

def s_renowned(v):
    v = si(v)
    if v >= 20: return 80
    if v >= 10: return 60
    return 30

def s_sniper(v):
    return 60 if si(v) >= 5 else 40

def s_liq(v):
    v = sf(v)
    if v > 50000: return 90
    if v > 20000: return 70
    if v > 10000: return 50
    return 20

def s_mcap(v):
    v = sf(v)
    if 50000 <= v <= 500000: return 80
    if v < 50000: return 60
    if v > 10000000: return 20
    if v > 1000000: return 40
    return 80

def s_lock(v):
    v = sf(v)
    if v >= 0.95: return 80
    if v >= 0.5: return 50
    return 20

def s_vol_mcap(vol, mcap):
    vol = sf(vol); mcap = sf(mcap)
    if mcap <= 0: return 30
    r = vol / mcap
    if r > 1.0: return 80
    if r > 0.3: return 60
    return 30

def s_bs(buys, sells):
    b = si(buys); s = si(sells)
    if s <= 0: return 80
    r = b / s
    if r > 1.5: return 80
    if r > 1.0: return 60
    return 30

def s_swaps(v):
    v = si(v)
    if v > 1000: return 80
    if v > 500: return 60
    if v > 100: return 40
    return 20

def s_holders(v):
    v = si(v)
    if v > 500: return 80
    if v > 200: return 60
    if v > 50: return 40
    return 20

def score(t):
    s1 = (s_bundler(t.get('bundler_rate')) + s_top10(t.get('top_10_holder_rate')) +
          s_creator(t.get('creator_token_status')) + s_renounced(t.get('renounced_mint'))) / 4
    s2 = (s_smart(t.get('smart_degen_count')) + s_renowned(t.get('renowned_count')) +
          s_sniper(t.get('sniper_count'))) / 3
    s3 = (s_liq(t.get('liquidity')) + s_mcap(t.get('market_cap')) +
          s_lock(t.get('lock_percent')) + s_vol_mcap(t.get('volume'), t.get('market_cap'))) / 4
    s4 = (s_bs(t.get('buys'), t.get('sells')) + s_swaps(t.get('swaps')) +
          s_holders(t.get('holder_count'))) / 3
    total = s1 * 0.30 + s2 * 0.25 + s3 * 0.25 + s4 * 0.20
    addr = t.get('address', '')
    return total, {
        'symbol': t.get('symbol', '?'),
        'addr_short': addr[:6] + '...' + addr[-4:] if len(addr) > 10 else addr,
        'deployer_score': round(s1, 1),
        'smart_score': round(s2, 1),
        'health_score': round(s3, 1),
        'activity_score': round(s4, 1),
        'total': round(total, 1),
        'mcap': sf(t.get('market_cap')),
        'liq': sf(t.get('liquidity')),
        'top10': sf(t.get('top_10_holder_rate')),
        'bundler': sf(t.get('bundler_rate')),
        'smart_count': si(t.get('smart_degen_count')),
        'renowned_count': si(t.get('renowned_count')),
        'holders': si(t.get('holder_count')),
        'swaps': si(t.get('swaps')),
        'buys': si(t.get('buys')),
        'sells': si(t.get('sells')),
        'full_address': addr,
    }

def report(chain_name, json_path):
    emoji = CHAIN_EMOJI.get(chain_name, '\U0001f535')
    with open(json_path) as f:
        data = json.load(f)
    tokens = data.get('data', {}).get('rank', [])
    if not tokens:
        print(f"\n{emoji} {chain_name.upper()} -- no data")
        return

    scored = [score(t) for t in tokens]
    scored.sort(key=lambda x: x[0], reverse=True)

    high = [r for r in scored if r[0] >= 75]
    med  = [r for r in scored if 60 <= r[0] < 75]
    low  = [r for r in scored if r[0] < 60]

    print(f"\n{emoji} {chain_name.upper()} ({len(tokens)} tokens)")
    print('-' * 50)

    if high:
        print(f"\n🔥 >=75 (RECOMMEND):")
        for total, d in high:
            _p(d, total)
    else:
        print(f"\nNo tokens >=75")

    if med:
        print(f"\nYellow 60-74:")
        for total, d in med[:5]:
            print(f"  {d['symbol']} ({d['addr_short']}) -- {d['total']}pts | MC:${d['mcap']:,.0f} | Bundle:{d['bundler']:.0%} | Smart:{d['smart_count']}")

    print(f"\n  Recommend:{len(high)}  Watch:{len(med)}  Skip:{len(low)}")

def _p(d, total):
    print(f"  {d['symbol']} ({d['addr_short']}) -- {d['total']}pts")
    print(f"    Deployer:{d['deployer_score']} | Smart:{d['smart_score']} | Health:{d['health_score']} | Activity:{d['activity_score']}")
    print(f"    MC:${d['mcap']:,.0f} | Liq:${d['liq']:,.0f} | T10:{d['top10']:.0%} | Bundle:{d['bundler']:.0%} | Smart:{d['smart_count']} | Holders:{d['holders']} | Swaps:{d['swaps']}")

def detail(t):
    total, d = score(t)
    lines = [
        f"Token: ${d['symbol']}",
        f"Address: {d['addr_short']}",
        f"",
        f"Deployer Quality: {d['deployer_score']}/100 (30%)",
        f"Smart Money: {d['smart_score']}/100 (25%)",
        f"Onchain Health: {d['health_score']}/100 (25%)",
        f"Trading Activity: {d['activity_score']}/100 (20%)",
        f"",
        f"Total Score: {d['total']}/100",
    ]
    if d['total'] >= 75:
        lines.append(f"Verdict: RECOMMEND")
    elif d['total'] >= 60:
        lines.append(f"Verdict: Watch")
    else:
        lines.append(f"Verdict: Skip")
    lines.extend([
        f"",
        f"MC: ${d['mcap']:,.0f} | Liq: ${d['liq']:,.0f}",
        f"Top10: {d['top10']:.0%} | Bundle: {d['bundler']:.0%}",
        f"Smart: {d['smart_count']} | Holders: {d['holders']} | Swaps: {d['swaps']}",
    ])
    return '\n'.join(lines)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        if len(sys.argv) > 1 and sys.argv[1] == '--detail':
            data = json.load(sys.stdin)
            print(detail(data))
        else:
            print("Usage:")
            print("  Batch:  python3 score_trending.py <chain> <json_file>")
            print("  Single: cat token_info.json | python3 score_trending.py --detail")
        sys.exit(1)

    chain_name = sys.argv[1]
    json_path = sys.argv[2]
    report(chain_name, json_path)
