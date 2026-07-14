#!/usr/bin/env python3
"""V4 Bearish Alignment Strategy - OKX ATK Integration"""
import subprocess, json, sys, math
from collections import deque

def okx_cmd(args, demo=False):
    cmd = ['okx'] + args
    if demo:
        cmd.append('--demo')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    # Filter out warning lines
    lines = [l for l in r.stdout.split('\n') if 'Warning' not in l and 'UNDICI' not in l]
    return '\n'.join(lines).strip()

def fetch_candles(timeframe, limit=150):
    """Fetch OHLCV data, return list of [close, high, low]"""
    raw = okx_cmd(['market', 'candles', 'BTC-USDT-SWAP', '--bar', timeframe, '--limit', str(limit)])
    lines = [l for l in raw.split('\n') if l and not l.startswith('Environment') and not l.startswith('time') and not l.startswith('---')]
    
    candles = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 6:
            try:
                close = float(parts[4])
                high = float(parts[2])
                low = float(parts[3])
                candles.append({'close': close, 'high': high, 'low': low})
            except ValueError:
                continue
    return candles

def sma(data, period):
    if len(data) < period:
        return None
    return sum(data[-period:]) / period

def ema(data, period):
    if len(data) < period:
        return None
    multiplier = 2 / (period + 1)
    result = sma(data[:period], period)  # start with SMA
    for price in data[period:]:
        result = (price - result) * multiplier + result
    return result

def check_alignment(mas):
    """Check if MAs are in bearish alignment (shorter < longer)"""
    names = ['SMA20', 'SMA60', 'SMA120', 'EMA20', 'EMA60', 'EMA120']
    vals = [mas[n] for n in names if mas[n] is not None]
    if len(vals) < 4:
        return False, "Not enough MA data"
    
    # Check: shorter MAs should be below longer MAs
    if mas['SMA20'] >= mas['SMA60']:
        return False, "SMA20 above SMA60 - not bearish"
    if mas['SMA60'] >= mas['SMA120']:
        return False, "SMA60 above SMA120 - not bearish"
    if mas['EMA20'] >= mas['EMA60']:
        return False, "EMA20 above EMA60 - not bearish"
    if mas['EMA60'] >= mas['EMA120']:
        return False, "EMA60 above EMA120 - not bearish"
    if mas['EMA20'] >= mas['SMA20']:
        return False, "EMA20 above SMA20 - short-term momentum up"
    
    return True, "Bearish alignment confirmed"

def check_smooth_decline(candles, lookback=10):
    """Check for smooth decline: lower highs and lower lows"""
    if len(candles) < lookback:
        return False, "Not enough data"
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    # Check if overall trend is down
    if highs[-1] >= highs[0] * 0.98:  # didn't drop at least 2%
        return False, "No significant decline detected"
    
    # Check for smoothness (no huge spikes)
    avg_range = sum(c['high'] - c['low'] for c in recent) / lookback
    current_price = candles[-1]['close']
    if avg_range / current_price > 0.015:  # average candle range > 1.5%
        return False, "Too volatile, not a smooth decline"
    
    return True, "Smooth decline pattern detected"

def get_current_price():
    raw = okx_cmd(['market', 'ticker', 'BTC-USDT'])
    for line in raw.split('\n'):
        if line.startswith('last'):
            return float(line.split()[1])
    return None

# === MAIN ===
print("=" * 60)
print("V4 Bearish Alignment Strategy - BTC-USDT")
print("=" * 60)

price = get_current_price()
print(f"\n📊 Current BTC Price: ${price:,.2f}")

# Fetch multiple timeframes
for tf_name, tf_bar in [('4H', '4H'), ('1H', '1H'), ('15m', '15m')]:
    print(f"\n─── {tf_name} Timeframe ───")
    candles = fetch_candles(tf_bar, limit=150)
    if len(candles) < 130:
        print(f"  ⚠ Only {len(candles)} candles available")
        continue
    
    closes = [c['close'] for c in candles]
    
    mas = {
        'SMA20': sma(closes, 20),
        'SMA60': sma(closes, 60),
        'SMA120': sma(closes, 120) if len(closes) >= 120 else None,
        'EMA20': ema(closes, 20),
        'EMA60': ema(closes, 60),
        'EMA120': ema(closes, 120) if len(closes) >= 120 else None,
    }
    
    print(f"  Price: ${closes[-1]:,.2f}")
    print(f"  SMA20: ${mas['SMA20']:,.2f}" if mas['SMA20'] else "  SMA20: N/A")
    print(f"  SMA60: ${mas['SMA60']:,.2f}" if mas['SMA60'] else "  SMA60: N/A")
    print(f"  SMA120: ${mas['SMA120']:,.2f}" if mas['SMA120'] else "  SMA120: N/A")
    print(f"  EMA20: ${mas['EMA20']:,.2f}" if mas['EMA20'] else "  EMA20: N/A")
    print(f"  EMA60: ${mas['EMA60']:,.2f}" if mas['EMA60'] else "  EMA60: N/A")
    print(f"  EMA120: ${mas['EMA120']:,.2f}" if mas['EMA120'] else "  EMA120: N/A")
    
    aligned, msg = check_alignment(mas)
    print(f"  Alignment: {'✅ Bearish' if aligned else '❌ ' + msg}")
    
    if aligned:
        smooth, smsg = check_smooth_decline(candles)
        print(f"  Decline: {'✅ Smooth' if smooth else '❌ ' + smsg}")
    
    # Price vs MAs
    current = closes[-1]
    if mas['SMA20'] and current < mas['SMA20']:
        print(f"  ✅ Price below SMA20 (bearish signal)")
    else:
        print(f"  ⚠ Price at or above SMA20")

print("\n" + "=" * 60)
print("VERDICT:")
print("=" * 60)
