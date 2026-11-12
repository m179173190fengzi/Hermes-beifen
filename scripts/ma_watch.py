#!/usr/bin/env python3
"""BTC 锚定 + USELESS 双均线信号（1m/5m）。

逻辑：BTC 领先，用 BTC 定方向，用 USELESS 找入场。
  🟠 BTC 发动      : BTC 刚站上全部 6 均线 -> 提前预警，盯 USELESS
  ✅ 共振入场      : USELESS 刚站上全部 6 均线 + BTC 同级别在上面 -> 入场
  ⚠️ 逆势信号      : USELESS 站上但 BTC 在本级别未确认 -> 降级，别重仓
  ❌ 出场          : USELESS 跌破 EMA20 -> 走

用法：python3 ma_watch.py [--bars 1m,5m] [--force]
"""
import argparse
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

PROXY = "http://127.0.0.1:7890"
CST = timezone(timedelta(hours=8))
STATE = os.path.expanduser("~/.hermes/cron/state/ma_watch.json")
API = "https://www.okx.com/api/v5/market/candles?instId=%s&bar=%s&limit=200"
DENSE = 3.0
COMPRESSED = 1.0
BTC = "BTC-USDT-SWAP"
TGT = "USELESS-USDT-SWAP"


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


def load():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f)


def check(inst, bar):
    rows = fetch(inst, bar)
    c = [float(r[4]) for r in reversed(rows)]
    if len(c) < 130:
        return None
    px = c[-1]
    lo = float(rows[0][3])
    m = {"SMA20": sma(c, 20), "SMA60": sma(c, 60), "SMA120": sma(c, 120),
         "EMA20": ema(c, 20), "EMA60": ema(c, 60), "EMA120": ema(c, 120)}
    bull = m["SMA20"] > m["SMA60"] > m["SMA120"]
    # 第一次回踩 20 均线不破：多头排列 + 最低价触及 SMA20 附近 + 收盘仍在其上
    pull = bull and lo <= m["SMA20"] * 1.002 and px > m["SMA20"] and px < m["SMA20"] * 1.015
    return {
        "px": px, "lo": lo, "m": m, "pull": pull,
        "above": all(px > x for x in m.values()),
        "below20": px < m["EMA20"],
        "dense": (max(m.values()) - min(m.values())) / px * 100 < DENSE,
        "comp": (max(m.values()) - min(m.values())) / px * 100 < COMPRESSED,
        "spread": (max(m.values()) - min(m.values())) / px * 100,
        "bull": bull,
    }


def block(tag, inst, bar, r, extra=""):
    m = r["m"]
    return "\n".join([
        "%s | %s %s" % (tag, inst, bar),
        "价 %.6g | 密集度 %.1f%% | %s | 距EMA20 %+.2f%%"
        % (r["px"], r["spread"], "多头排列" if r["bull"] else "排列纠缠",
           (r["px"] / m["EMA20"] - 1) * 100),
        "SMA %.6g / %.6g / %.6g" % (m["SMA20"], m["SMA60"], m["SMA120"]),
        "EMA %.6g / %.6g / %.6g" % (m["EMA20"], m["EMA60"], m["EMA120"]),
    ] + ([extra] if extra else []) + [datetime.now(CST).strftime("%m-%d %H:%M")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default="1m,5m")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    st = load()
    out = []
    for bar in [b.strip() for b in a.bars.split(",") if b.strip()]:
        bk, tk = "BTC:" + bar, "TGT:" + bar
        b, t = check(BTC, bar), check(TGT, bar)
        if not b or not t:
            continue
        pb, pt = st.get(bk, {}), st.get(tk, {})
        if a.force:
            out.append(block("🟠 BTC", BTC, bar, b,
                             "状态 " + ("站上全部均线" if b["above"] else
                                        ("跌破EMA20" if b["below20"] else "均线间震荡"))))
            out.append(block("🎯 USELESS", TGT, bar, t,
                             "状态 " + ("站上全部均线" if t["above"] else
                                        ("跌破EMA20" if t["below20"] else "均线间震荡"))))
        else:
            if b["comp"] and not pb.get("comp"):
                out.append(block("🚨 BTC 极限压缩（准备）", BTC, bar, b,
                                 "→ 六均线粘合 <1%，方向一选就是一段行情"))
            if b["above"] and not pb.get("above"):
                out.append(block("🟠 BTC 发动（先手）", BTC, bar, b,
                                 "→ BTC 已站上全部均线，盯 USELESS 跟涨"))
            if t["comp"] and not pt.get("comp") and b["above"]:
                out.append(block("🚨 USELESS 极限压缩", TGT, bar, t,
                                 "→ 粘合 <1% 且 BTC 在上面，等它站上全部均线"))
            if t["pull"] and not pt.get("pull"):
                if b["above"]:
                    out.append(block("🎯 第一次回踩20均线不破（入场）", TGT, bar, t,
                                     "→ 多头排列，低点 %.6g 触及 SMA20 %.6g 后收在其上；止损放 SMA20 下方 3%%"
                                     % (t["lo"], t["m"]["SMA20"])))
                else:
                    out.append(block("🎯 回踩20均线不破（但 BTC 未确认）", TGT, bar, t,
                                     "→ 结构成立，仓位减半"))
            if t["above"] and not pt.get("above"):
                if b["above"]:
                    out.append(block("✅ 共振入场", TGT, bar, t,
                                     "BTC %s 已确认在上面，顺势做多" % bar))
                else:
                    out.append(block("⚠️ 逆势信号", TGT, bar, t,
                                     "BTC %s 未确认（%s）→ 减半仓或不做" %
                                     (bar, "跌破EMA20" if b["below20"] else "震荡")))
            if t["below20"] and not pt.get("below20") and pt.get("above"):
                out.append(block("❌ 出场", TGT, bar, t, "跌破 EMA20，趋势破坏"))
        st[bk] = {"above": b["above"], "below20": b["below20"],
                  "dense": b["dense"], "comp": b["comp"], "pull": b["pull"]}
        st[tk] = {"above": t["above"], "below20": t["below20"],
                  "dense": t["dense"], "comp": t["comp"], "pull": t["pull"]}
    save(st)
    if out:
        print(("\n" if a.force else "\n\n").join(out))


if __name__ == "__main__":
    main()
