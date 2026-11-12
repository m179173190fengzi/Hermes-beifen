#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三链 TVL 7d/24h 实算 — DeFiLlama historicalChainTvl（代理内置）

为什么需要：tvl_monitor.py 对 Sol/BSC/RH 打印 +0.0% 是 DeFiLlama 数据缺口误导
（v2/chains 的 tvlChange1d/7d 返回 null；historical 数据点稀疏时 closest(now) 与
closest(now-86400) 命中同一点 → 24h 算成 +0.0%）。本脚本用 v2/historicalChainTvl
实算真实 7d 变化，并输出数据点间隔供判断 24h 是否可信。

用法: python3 tvl-7d-change.py
实测(2026-08-16 晚场): Sol $4,804M 7d -1.0% | BSC $4,887M 7d -0.3% | RH $545M 7d +15.7%
schema 注意: 数组元素字段是 {date: unix秒, tvl: float}，不是 timestamp/totalLiquidityUSD
"""
import json
import time
import urllib.request

PROXY = "http://127.0.0.1:7890"


def fetch(url):
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener.open(req, timeout=20) as r:
        return json.loads(r.read().decode())


now = int(time.time())
targets = {
    "Solana": "solana",
    "BSC": "bsc",
    "Robinhood Chain": "Robinhood%20Chain",  # RH slug 必须 URL 编码
}


def closest(points, ts):
    return min(points, key=lambda p: abs(p["date"] - ts))


for label, slug in targets.items():
    try:
        data = fetch(f"https://api.llama.fi/v2/historicalChainTvl/{slug}")
        cur = closest(data, now)
        d1 = closest(data, now - 86400)
        w1 = closest(data, now - 7 * 86400)
        chg24 = (cur["tvl"] / d1["tvl"] - 1) * 100 if d1["tvl"] else 0
        chg7 = (cur["tvl"] / w1["tvl"] - 1) * 100 if w1["tvl"] else 0
        gap24 = cur["date"] - d1["date"]  # ≈0 → 24h 数据缺失，以 7d 为准
        flag = " (24h 失真,以 7d 为准)" if gap24 < 3600 else ""
        print(
            f"{label}: TVL ${cur['tvl']/1e6:.0f}M | "
            f"24h {chg24:+.1f}% (gap {gap24}s){flag} | "
            f"7d {chg7:+.1f}% | points={len(data)}"
        )
    except Exception as e:
        print(f"{label}: FAIL {e}")
