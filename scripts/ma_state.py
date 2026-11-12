#!/usr/bin/env python3
"""通用 6 均线状态查询（OKX）：python3 ma_state.py --inst AXIS-USDT-SWAP --bars 1m,5m,15m,1H"""
import argparse
import json
import urllib.request

PROXY = "http://127.0.0.1:7890"
API = "https://www.okx.com/api/v5/market/candles?instId=%s&bar=%s&limit=200"


def fetch(inst, bar):
    req = urllib.request.Request(API % (inst, bar), headers={"User-Agent": "Mozilla/5.0"})
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=30) as r:
        return json.loads(r.read().decode())["data"]


def sma(v, n):
    return sum(v[-n:]) / n


def ema(v, n):
    k = 2.0 / (n + 1)
    e = v[0]
    for x in v[1:]:
        e = x * k + e * (1 - k)
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", default="AXIS-USDT-SWAP")
    ap.add_argument("--bars", default="1m,5m,15m,1H")
    a = ap.parse_args()
    for bar in [b.strip() for b in a.bars.split(",") if b.strip()]:
        rows = fetch(a.inst, bar)
        c = [float(r[4]) for r in reversed(rows)]
        hi = max(float(r[2]) for r in rows[:30])
        lo = min(float(r[3]) for r in rows[:30])
        px = c[-1]
        m = [("SMA20", sma(c, 20)), ("SMA60", sma(c, 60)), ("SMA120", sma(c, 120)),
             ("EMA20", ema(c, 20)), ("EMA60", ema(c, 60)), ("EMA120", ema(c, 120))]
        above = all(px > v for _, v in m)
        below20 = px < dict(m)["EMA20"]
        spread = (max(v for _, v in m) - min(v for _, v in m)) / px * 100
        bull = dict(m)["SMA20"] > dict(m)["SMA60"] > dict(m)["SMA120"]
        print("%-5s 价 %.5g | %s | 密集度 %.1f%% | %s | 距EMA20 %+.2f%% | 近30根 高 %.5g 低 %.5g"
              % (bar, px, "站上全部" if above else ("跌破EMA20" if below20 else "均线之间"),
                 spread, "多头排列" if bull else "排列纠缠", (px / dict(m)["EMA20"] - 1) * 100, hi, lo))
        print("       " + " | ".join("%s %.5g" % (k, v) for k, v in m))


if __name__ == "__main__":
    main()
