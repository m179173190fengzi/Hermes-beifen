#!/usr/bin/env python3
"""价格阈值看门狗（no_agent cron 用，零 LLM 成本）。

盯若干代币，只在「越过阈值」时出声，其余时间完全静默。
条件解除后会自动重新武装（下次再越线还会报）。

配置：~/.hermes/cron/watch_prices.json
  [{"ca":"...","chain":"sol","sym":"SUPERCORE","note":"...",
    "rules":[{"type":"mc_below","value":300000,"msg":"..."},
             {"type":"mc_above","value":550000,"msg":"..."},
             {"type":"lp_below","value":40000,"msg":"..."}]}]

用法：
  python3 price_watch.py          # 正常跑（cron）
  python3 price_watch.py --test   # 强制打印当前快照（不推送）
"""
import json
import os
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".hermes/cron/watch_prices.json")
STATE = os.path.join(HOME, ".hermes/cron/state/watch_prices.json")
GMGN = os.path.join(HOME, ".local/bin/gmgn-cli")
PROXY = "http://127.0.0.1:7890"


def load(p, d):
    try:
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return d


def save(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fnum(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def snap(ca, chain):
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        out = subprocess.run([GMGN, "token", "info", "--chain", chain,
                              "--address", ca, "--raw"],
                             capture_output=True, text=True, timeout=120, env=env).stdout
        j = json.loads(out or "{}")
    except Exception:  # noqa: BLE001
        return None
    p = (j.get("price") or {})
    px = fnum(p.get("price"))
    supply = fnum(j.get("circulating_supply")) or fnum(j.get("total_supply"))

    def chg(ref_key):
        ref = fnum(p.get(ref_key))
        return ((px / ref - 1) * 100) if (px and ref) else 0.0

    return {
        "price": px,
        "mc": px * supply if (px and supply) else 0,
        "lp": fnum(j.get("liquidity")),
        "holders": j.get("holder_count") or 0,
        "vol24": fnum(p.get("volume_24h")),
        "chg1h": chg("price_1h"),
        "chg6h": chg("price_6h"),
        "chg24h": chg("price_24h"),
        "ath": fnum(j.get("ath_price")),
    }


def hit(rule, s):
    t, v = rule.get("type"), fnum(rule.get("value"))
    if t == "mc_below":
        return s["mc"] and s["mc"] < v
    if t == "mc_above":
        return s["mc"] and s["mc"] > v
    if t == "lp_below":
        return s["lp"] and s["lp"] < v
    if t == "lp_above":
        return s["lp"] and s["lp"] > v
    return False


def main():
    test = "--test" in sys.argv
    items = load(CONFIG, [])
    if not items:
        return 0
    state = load(STATE, {})
    out = []
    for it in items:
        ca, chain = it.get("ca"), it.get("chain", "sol")
        sym = it.get("sym") or "?"
        s = snap(ca, chain)
        key = ca
        st = state.setdefault(key, {"fired": {}})
        if not s:
            continue
        if test:
            out.append("%s 价格 $%.8f | MC $%s | LP $%s | 1h %+.1f%% | 6h %+.1f%% | 24h %+.1f%%"
                       % (sym, s["price"], f"{s['mc']:,.0f}", f"{s['lp']:,.0f}",
                          s["chg1h"], s["chg6h"], s["chg24h"]))
            continue
        for idx, rule in enumerate(it.get("rules") or []):
            rid = "%d" % idx
            active = hit(rule, s)
            if active and not st["fired"].get(rid):
                st["fired"][rid] = True
                out.append("🔔 %s (阈值: %s %s)\n当前 MC $%s | 价格 $%.8f | LP $%s | 1h %+.1f%% | 24h %+.1f%%\n%s\n🔗 CA: %s"
                           % (sym, rule.get("type"), f"{fnum(rule.get('value')):,.0f}",
                              f"{s['mc']:,.0f}", s["price"], f"{s['lp']:,.0f}",
                              s["chg1h"], s["chg24h"], rule.get("msg") or "", ca))
            elif not active and st["fired"].get(rid):
                st["fired"][rid] = False   # 条件解除 → 重新武装
        st["last"] = {"ts": time.time(), "mc": s["mc"], "price": s["price"]}
    save(STATE, state)
    if out:
        print("\n\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
