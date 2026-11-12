#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量 token info 解析 — 叙事核验 + 新币 creation_timestamp 核验。
用法：python3 parse-token-info-batch.py <JOB>
  JOB 由 fetch-token-info-batch.sh 末尾打印（如 alpha_12345），匹配 /tmp/ti_<JOB>_*.json。
只 glob 本次 JOB 前缀 → 旧会话残留的 ti_*.json 永不混入（实测踩过：裸 glob 混入约 30 条旧文件）。
输出字段：symbol/name、推算 MC、creation/open 时间（unix→本地）、holders、liquidity、
launchpad、dev 状态、desc/web/tw — 即 📋 叙事行所需字段 + 新币/重发判定所需时间戳。
"""
import json, glob, sys, time

def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        return {"ERR": str(e)}

def s(v):
    return "" if v is None else str(v)

def main():
    job = sys.argv[1] if len(sys.argv) > 1 else ""
    files = sorted(glob.glob(f"/tmp/ti_{job}_*.json")) if job else []
    if not files:
        print(f"NO FILES for prefix ti_{job}_ — 检查 JOB 值（应为 fetch 脚本末尾打印值）")
        return
    for p in files:
        label = p.split("/")[-1].replace(f"ti_{job}_", "").replace(".json", "")
        d = load(p)
        if "ERR" in d:
            print(f"== {label}: LOAD_ERR {d['ERR']}")
            continue
        name = d.get("name", "?")
        symbol = d.get("symbol", "?")
        created = d.get("creation_timestamp", 0)
        open_ts = d.get("open_timestamp", 0)
        holders = d.get("holder_count", "?")
        liq = d.get("liquidity", "?")
        launchpad = d.get("launchpad_platform", "")
        desc = s(d.get("link", {}).get("description", ""))[:180]
        website = s(d.get("link", {}).get("website", ""))[:100]
        twitter = s(d.get("link", {}).get("twitter_username", ""))[:80]
        dev_status = s(d.get("dev", {}).get("creator_token_status", ""))
        mc = "?"
        try:
            px = float(d.get("price", {}).get("price", 0) or 0)
            cs = float(d.get("circulating_supply", 0) or 0)
            mc = f"${px * cs / 1e6:.2f}M" if px * cs >= 1e6 else f"${px * cs / 1e3:.0f}K"
        except Exception:
            pass
        ct = time.strftime("%m-%d %H:%M", time.localtime(created)) if created else "0(未知)"
        ot = time.strftime("%m-%d %H:%M", time.localtime(open_ts)) if open_ts else "0"
        print(f"== {label} | {symbol} ({name}) | MC {mc} | created {ct} | open {ot} | holders {holders} | liq {liq} | launchpad {launchpad} | dev {dev_status}")
        print(f"   desc: {desc}")
        print(f"   web: {website} | tw: {twitter}")

if __name__ == "__main__":
    main()
