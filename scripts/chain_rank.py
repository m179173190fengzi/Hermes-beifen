#!/usr/bin/env python3
"""链上成交量排行榜：按 24h DEX 成交量给链排序（附 Fees）。

用法：python3 chain_rank.py [--top 5]
"""
import json
import sys
import urllib.request

PROXY = "http://127.0.0.1:7890"
LLAMA = ("https://api.llama.fi/overview/%s/%s"
         "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
CORE = [("solana", "SOL"), ("bsc", "BSC"), ("robinhood", "RH")]
ALL = CORE + [("ethereum", "ETH"), ("base", "Base"), ("arbitrum", "Arb"),
              ("hyperliquid", "HL"), ("sui", "Sui"), ("ton", "TON"),
              ("tron", "Tron"), ("polygon", "Poly"), ("avax", "AVAX"),
              ("optimism", "OP"), ("aptos", "Aptos")]


def human(n):
    n = float(n or 0)
    if abs(n) >= 1e9:
        return "%.2fB" % (n / 1e9)
    if abs(n) >= 1e6:
        return "%.1fM" % (n / 1e6)
    if abs(n) >= 1e3:
        return "%.0fK" % (n / 1e3)
    return "%.0f" % n


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def main():
    top = 5
    if "--top" in sys.argv:
        try:
            top = int(sys.argv[sys.argv.index("--top") + 1])
        except (IndexError, ValueError):
            pass
    chains = ALL if "--all" in sys.argv else CORE

    # 第一遍：只拉成交量（快）
    vol = []
    for chain, label in chains:
        try:
            d = fetch(LLAMA % ("dexs", chain))
            v = float(d.get("total24h") or 0)
            if v > 0:
                vol.append((v, label, chain, float(d.get("change_1d") or 0)))
        except Exception:  # noqa: BLE001
            continue
    vol.sort(reverse=True)

    # 第二遍：只给前 N 名补 Fees（省请求）
    rows = []
    for v, label, chain, chg in vol[:top]:
        f = 0.0
        try:
            f = float(fetch(LLAMA % ("fees", chain)).get("total24h") or 0)
        except Exception:  # noqa: BLE001
            pass
        rows.append((v, label, chain, chg, f))

    print("链上 24h 成交量（%s）" % "/".join(l for _, l in chains))
    for i, (v, label, chain, chg, f) in enumerate(rows[:top], 1):
        ratio = (v / f) if f else 0
        print("%d. %-6s 成交 $%-8s (%+3.0f%%) | Fees $%-7s | 量/费 %.0fx"
              % (i, label, human(v), chg, human(f), ratio))


if __name__ == "__main__":
    main()
