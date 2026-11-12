#!/usr/bin/env python3
"""K线站上全部均线告警（SMA20/60/120 + EMA20/60/120）。

只在「未站上 -> 站上」翻转时输出一次（状态存 state/ma_watch.json），适合 no_agent cron。
用法：
  python3 ma-watch.py --inst USELESS-USDT-SWAP --bars 1H,4H
  python3 ma-watch.py --inst BTC-USDT-SWAP --force
"""
import argparse
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

PROXY = os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7890")
CST = timezone(timedelta(hours=8))
STATE = os.path.expanduser("~/.hermes/cron/state/ma_watch.json")
API = "https://www.okx.com/api/v5/market/candles?instId=%s&bar=%s&limit=200"


def fetch(inst, bar):
    req = urllib.request.Request(API % (inst, bar), headers={"User-Agent": "Mozilla/5.0"})
    op = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=30) as r:
        return json.loads(r.read().decode())["data"]


def sma(vals, n):
    return sum(vals[-n:]) / n


def ema_series(vals, n):
    k = 2.0 / (n + 1)
    e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f)


def check(inst, bar):
    rows = fetch(inst, bar)
    closes = [float(r[4]) for r in reversed(rows)]
    if len(closes) < 130:
        return None
    px = closes[-1]
    mas = {
        "SMA20": sma(closes, 20), "SMA60": sma(closes, 60), "SMA120": sma(closes, 120),
        "EMA20": ema_series(closes, 20), "EMA60": ema_series(closes, 60),
        "EMA120": ema_series(closes, 120),
    }
    above = all(px > v for v in mas.values())
    bull = (mas["SMA20"] > mas["SMA60"] > mas["SMA120"]
            and mas["EMA20"] > mas["EMA60"] > mas["EMA120"])
    spread = (max(mas.values()) - min(mas.values())) / px * 100
    return px, mas, above, bull, spread


def fmt(inst, bar, px, mas, bull, spread, above):
    return "\n".join([
        "%s | %s %s" % ("✅ K线站上全部均线" if above else "⏸ 仍在均线下方", inst, bar),
        "价 %.6g" % px,
        "SMA20 %.6g | SMA60 %.6g | SMA120 %.6g" % (mas["SMA20"], mas["SMA60"], mas["SMA120"]),
        "EMA20 %.6g | EMA60 %.6g | EMA120 %.6g" % (mas["EMA20"], mas["EMA60"], mas["EMA120"]),
        "排列 %s | 发散度 %.1f%% | 距SMA20 %+.1f%%"
        % ("多头" if bull else "非多头", spread, (px / mas["SMA20"] - 1) * 100),
        "时间 %s" % datetime.now(CST).strftime("%m-%d %H:%M"),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", default="USELESS-USDT-SWAP")
    ap.add_argument("--bars", default="1H,4H")
    ap.add_argument("--force", action="store_true", help="忽略状态，直接打印当前情况")
    a = ap.parse_args()
    st = load_state()
    for bar in [b.strip() for b in a.bars.split(",") if b.strip()]:
        r = check(a.inst, bar)
        if not r:
            continue
        px, mas, above, bull, spread = r
        prev = st.get("%s:%s" % (a.inst, bar), {}).get("above", False)
        if a.force or (above and not prev):
            print(fmt(a.inst, bar, px, mas, bull, spread, above))
            print()
        st["%s:%s" % (a.inst, bar)] = {"above": above, "px": px}
    save_state(st)


if __name__ == "__main__":
    main()
