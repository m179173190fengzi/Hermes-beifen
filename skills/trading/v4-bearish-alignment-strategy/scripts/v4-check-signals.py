#!/usr/bin/env python3
"""V4 Bearish Alignment Strategy - OKX ATK CLI Integration
Checks BTC-USDT across 4H/1H/15m for V4 short conditions.
Safe: READ-ONLY, never places orders.
"""
import subprocess, sys

def okx(args):
    r = subprocess.run(['okx'] + args, capture_output=True, text=True, timeout=30)
    lines = [l for l in r.stdout.split('\n')
             if l and not l.startswith(('Environment','time','---','(node','(Use'))
             and 'Warning' not in l and 'UNDICI' not in l]
    return '\n'.join(lines).strip()

def fetch_candles(tf, limit=150):
    raw = okx(['market','candles','BTC-USDT-SWAP','--bar',tf,'--limit',str(limit)])
    candles = []
    for line in raw.split('\n'):
        parts = line.split()
        if len(parts) >= 6:
            try:
                candles.append({'c': float(parts[4]), 'h': float(parts[2]), 'l': float(parts[3])})
            except ValueError:
                continue
    return candles

def sma(d, p):
    return sum(d[-p:])/p if len(d)>=p else None

def ema(d, p):
    if len(d) < p: return None
    m, r = 2/(p+1), sma(d[:p], p)
    for x in d[p:]: r = (x-r)*m + r
    return r

def check_smooth_decline(candles, lookback=10):
    """Check for smooth decline pattern: lower highs/lows, no violent spikes"""
    if len(candles) < lookback:
        return False, "Not enough data"
    recent = candles[-lookback:]
    highs = [c['h'] for c in recent]
    lows = [c['l'] for c in recent]
    if highs[-1] >= highs[0] * 0.98:
        return False, "No significant decline"
    avg_range = sum(c['h'] - c['l'] for c in recent) / lookback
    if avg_range / candles[-1]['c'] > 0.015:
        return False, "Too volatile"
    return True, "Smooth decline"

def check(candles, tf_name):
    c = [x['c'] for x in candles]
    if len(c) < 120: return f"{tf_name}: insufficient data ({len(c)})"
    mas = {k: v for k,v in {
        'SMA20': sma(c,20),'SMA60': sma(c,60),'SMA120': sma(c,120),
        'EMA20': ema(c,20),'EMA60': ema(c,60),'EMA120': ema(c,120)
    }.items() if v is not None}
    p = c[-1]

    lines = [f"┌─ {tf_name} ─────────────────────"]
    lines.append(f"│ Price: ${p:,.2f}")
    for k in ['SMA20','SMA60','SMA120','EMA20','EMA60','EMA120']:
        if k in mas: lines.append(f"│ {k}: ${mas[k]:,.2f}")

    # Check alignment
    ok = True
    if mas.get('SMA20',999999) >= mas.get('SMA60',0): ok=False
    if mas.get('SMA60',999999) >= mas.get('SMA120',0): ok=False
    if mas.get('EMA20',999999) >= mas.get('EMA60',0): ok=False
    if mas.get('EMA60',999999) >= mas.get('EMA120',0): ok=False
    if mas.get('EMA20',999999) >= mas.get('SMA20',0): ok=False

    lines.append(f"│ Alignment: {'✅ BEARISH' if ok else '❌ NOT bearish'}")
    lines.append(f"│ Price vs SMA20: {'✅ Below' if mas.get('SMA20',0)>p else '⚠ At/above'}")
    
    if ok:
        smooth, smsg = check_smooth_decline(candles)
        lines.append(f"│ Decline: {'✅' if smooth else '❌'} {smsg}")
    
    lines.append('└─────────────────────────')
    return '\n'.join(lines)

def main():
    print("="*56)
    print("  V4 Bearish Alignment Check — BTC-USDT")
    print("="*56)
    price = okx(['market','ticker','BTC-USDT'])
    for l in price.split('\n'):
        if 'last' in l or l.startswith('6'):
            print(f"\n  Current: ${l.split()[1] if len(l.split())>1 else '?'}")
            break
    for tf in ['4H','1H','15m']:
        candles = fetch_candles(tf)
        if candles: print('\n'+check(candles, tf))
    print("\n"+"="*56)
    print("  Safe: READ-ONLY — no orders placed")
    print("="*56)

if __name__ == '__main__':
    main()
