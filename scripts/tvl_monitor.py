#!/usr/bin/env python3
"""三链TVL监控: Solana / BSC / Robinhood Chain — DeFiLlama API"""
import json
import urllib.request
import sys

PROXY = "http://127.0.0.1:7890"
TARGETS = {"solana": "Solana", "bsc": "BSC", "robinhood chain": "RH"}

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def main():
    try:
        data = fetch("https://api.llama.fi/v2/chains")
    except Exception as e:
        # fallback without proxy
        try:
            req = urllib.request.Request("https://api.llama.fi/v2/chains", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e2:
            print(f"ERROR: {e} | {e2}")
            sys.exit(1)

    for c in data:
        name = c.get("name", "").lower()
        if name in TARGETS:
            tvl = c.get("tvl", 0) / 1e6
            chg7d = c.get("tvlChange7d", 0)
            chg1d = c.get("tvlChange1d", 0)
            print(f"{TARGETS[name]}: ${tvl:,.0f}M | 7d {chg7d:+.1f}% | 24h {chg1d:+.1f}%")

if __name__ == "__main__":
    main()
