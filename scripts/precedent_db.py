#!/usr/bin/env python3
"""precedent_db.py — 叙事先例库（Dani 的"第 ⑤ 问：有先例吗"自动化）。

核心问题：一个新盘冒出来时，同类叙事的历史先例长什么样？
  峰值市值多少？见顶要多久？之后回撤多少？活下来的比例？

数据来源：gmgn-cli token info（含 ath_price / 供应 / 持币 / bundle / 围猎）
         gmgn-cli market kline（定位见顶时间）

用法：
  python3 precedent_db.py init
  python3 precedent_db.py add --ca <地址> --chain sol --narrative 猫meme
  python3 precedent_db.py refresh --all
  python3 precedent_db.py report
  python3 precedent_db.py report --narrative 猫meme
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

DB = os.path.expanduser("~/.hermes/data/precedent.db")
GMGN = "gmgn-cli"

SCHEMA = """
CREATE TABLE IF NOT EXISTS coins (
    address        TEXT PRIMARY KEY,
    chain          TEXT NOT NULL,
    symbol         TEXT,
    name           TEXT,
    narrative      TEXT,              -- 人工打的叙事标签
    launchpad      TEXT,
    created_at     INTEGER,           -- 币创建时间
    open_at        INTEGER,
    ath_price      REAL,
    ath_mc         REAL,              -- 历史峰值市值
    cur_price      REAL,
    cur_mc         REAL,
    lifetime_days  REAL,
    holder_count   INTEGER,
    top10_rate     REAL,
    bundle_rate    REAL,
    entrapment     REAL,
    bot_rate       REAL,
    smart_count    INTEGER,
    dev_status     TEXT,
    twitter        TEXT,
    website        TEXT,
    peak_at        INTEGER,           -- 见顶时间戳
    note           TEXT,
    first_seen     INTEGER,
    updated_at     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_narrative ON coins(narrative);
CREATE INDEX IF NOT EXISTS idx_chain ON coins(chain);
"""


def conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def run(cmd: list[str], timeout: int = 60) -> dict | None:
    env = dict(os.environ)
    env.setdefault("HTTPS_PROXY", "http://127.0.0.1:7890")
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout, env=env)
        if out.returncode != 0 or not out.stdout.strip():
            return None
        return json.loads(out.stdout)
    except Exception:
        return None


def fetch_info(chain: str, address: str) -> dict | None:
    return run([GMGN, "token", "info", "--chain", chain,
                "--address", address, "--raw"])


def fnum(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def peak_from_kline(chain: str, address: str, created: int) -> tuple[float, int]:
    """用 1h K 线找最高价与其时间戳。返回 (最高价, 时间戳)。"""
    data = run([GMGN, "market", "kline", "--chain", chain,
                "--address", address, "--resolution", "1h",
                "--from", str(max(created - 3600, 0)),
                "--to", str(int(time.time())), "--raw"], timeout=90)
    if not data:
        return 0.0, 0
    rows = data if isinstance(data, list) else data.get("list") or data.get("data") or []
    best_p, best_t = 0.0, 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        h = fnum(r.get("high") or r.get("h") or r.get("close") or r.get("c"))
        t = int(fnum(r.get("time") or r.get("t") or r.get("timestamp")))
        if t > 1e11:          # 毫秒 → 秒
            t //= 1000
        if h > best_p:
            best_p, best_t = h, t
    return best_p, best_t


def cmd_init(_args) -> int:
    with conn() as c:
        c.executescript(SCHEMA)
        # 老库迁移：补 peak_at 列
        cols = {r[1] for r in c.execute("PRAGMA table_info(coins)")}
        if "peak_at" not in cols:
            c.execute("ALTER TABLE coins ADD COLUMN peak_at INTEGER")
            print("已补列: peak_at")
    print(f"初始化完成: {DB}")
    return 0


def cmd_add(args) -> int:
    with conn() as c:
        c.executescript(SCHEMA)
        c.execute(
            "INSERT INTO coins(address, chain, narrative, note, first_seen) "
            "VALUES(?,?,?,?,?) ON CONFLICT(address) DO UPDATE SET "
            "narrative=COALESCE(excluded.narrative, narrative), "
            "note=COALESCE(excluded.note, note)",
            (args.ca, args.chain, args.narrative, args.note, int(time.time())))
    print(f"已加入: {args.ca[:12]}… [{args.chain}] 叙事={args.narrative or '-'}")
    return 0


def cmd_refresh(args) -> int:
    with conn() as c:
        c.executescript(SCHEMA)
        if args.ca:
            rows = c.execute("SELECT * FROM coins WHERE address=?", (args.ca,)).fetchall()
        else:
            rows = c.execute("SELECT * FROM coins ORDER BY updated_at NULLS FIRST").fetchall()

    if not rows:
        print("库里没有币，先 add")
        return 1

    ok = 0
    for r in rows:
        chain, addr = r["chain"], r["address"]
        info = fetch_info(chain, addr)
        if not info:
            print(f"  跳过 {r['symbol'] or addr[:8]}（取数失败）")
            continue
        stat = info.get("stat") or {}
        supply = fnum(info.get("total_supply")) or fnum(info.get("circulating_supply"))
        # price 是对象：{"price": "0.00016...", "price_1h": ...}；ath_price 是顶层标量
        price_obj = info.get("price")
        price = fnum(price_obj.get("price")) if isinstance(price_obj, dict) \
            else fnum(price_obj)
        ath_price = fnum(info.get("ath_price"))
        created = int(fnum(info.get("creation_timestamp")))
        cur_mc = price * supply
        ath_mc = ath_price * supply

        # 峰值时间：只在还没算过时用 K 线补（>1e11 是旧数据的毫秒值，视为无效）
        peak_ts = int(fnum(r["peak_at"])) if "peak_at" in r.keys() else 0
        if peak_ts > 1e11:
            peak_ts = 0
        if created and not peak_ts:
            best_p, best_t = peak_from_kline(chain, addr, created)
            if best_p > ath_price:
                ath_price = best_p
                ath_mc = best_p * supply
            peak_ts = best_t

        link = info.get("link") or {}
        dev = info.get("dev") or {}
        lifetime = (time.time() - created) / 86400 if created else 0

        with conn() as c:
            c.execute(
                "UPDATE coins SET symbol=?, name=?, launchpad=?, created_at=?, open_at=?, "
                "ath_price=?, ath_mc=?, cur_price=?, cur_mc=?, lifetime_days=?, "
                "holder_count=?, top10_rate=?, bundle_rate=?, entrapment=?, bot_rate=?, "
                "smart_count=?, dev_status=?, twitter=?, website=?, updated_at=?, "
                "peak_at=? WHERE address=?",
                (info.get("symbol"), info.get("name"),
                 info.get("launchpad_platform") or info.get("launchpad"),
                 created, int(fnum(info.get("open_timestamp"))),
                 ath_price, ath_mc, price, cur_mc, round(lifetime, 2),
                 int(fnum(info.get("holder_count"))),
                 fnum(stat.get("top_10_holder_rate")),
                 fnum(stat.get("top_bundler_trader_percentage")),
                 fnum(stat.get("top_entrapment_trader_percentage")),
                 fnum(stat.get("bot_degen_rate")),
                 int(fnum(stat.get("smart_degen_count"))),
                 dev.get("creator_token_status"),
                 link.get("twitter_username"), link.get("website"),
                 int(time.time()), peak_ts or None, addr))
        ok += 1
        dd = (1 - cur_mc / ath_mc) * 100 if ath_mc else 0
        print(f"  ✓ {info.get('symbol'):<12} MC ${cur_mc/1e6:.2f}M  ATH ${ath_mc/1e6:.2f}M  "
              f"回撤 {dd:.0f}%  币龄 {lifetime:.0f}d")
        time.sleep(0.4)

    print(f"\n刷新 {ok}/{len(rows)}")
    return 0


def pct(v: float) -> str:
    return f"{v*100:.1f}%" if v else "-"


def cmd_report(args) -> int:
    with conn() as c:
        c.executescript(SCHEMA)
        cols = {r[1] for r in c.execute("PRAGMA table_info(coins)")}
        if "peak_at" not in cols:
            c.execute("ALTER TABLE coins ADD COLUMN peak_at INTEGER")
        if args.narrative:
            rows = c.execute(
                "SELECT * FROM coins WHERE narrative LIKE ? AND ath_mc > 0 "
                "ORDER BY ath_mc DESC", (f"%{args.narrative}%",)).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM coins WHERE ath_mc > 0 ORDER BY ath_mc DESC").fetchall()

    if not rows:
        print("没有数据，先 refresh")
        return 1

    def peak_h(r) -> str:
        if r["peak_at"] and r["created_at"]:
            t = r["peak_at"]
            if t > 1e11:      # 兼容旧数据：毫秒
                t /= 1000
            return f"{(t - r['created_at'])/3600:.0f}"
        return "-"

    head = (f"{'币':<13}{'链':<5}{'叙事':<17}{'ATH市值':>10}{'现市值':>10}"
            f"{'回撤':>6}{'见顶h':>6}{'币龄':>5}{'bundle':>8}{'围猎':>7}")
    print(head)
    print("-" * 93)
    for r in rows:
        dd = (1 - r["cur_mc"] / r["ath_mc"]) * 100 if r["ath_mc"] else 0
        print(f"{(r['symbol'] or '-')[:12]:<13}{(r['chain'] or '-'):<5}"
              f"{(r['narrative'] or '-')[:16]:<17}"
              f"{r['ath_mc']/1e6:>9.2f}M{r['cur_mc']/1e6:>9.2f}M"
              f"{dd:>5.0f}%{peak_h(r):>6}{(r['lifetime_days'] or 0):>4.0f}d"
              f"{pct(r['bundle_rate']):>8}{pct(r['entrapment']):>7}")

    # 整体统计
    aths = [r["ath_mc"] / 1e6 for r in rows]
    dds = [(1 - r["cur_mc"] / r["ath_mc"]) * 100 for r in rows if r["ath_mc"]]
    alive = sum(1 for r in rows if r["cur_mc"] and r["ath_mc"]
                and r["cur_mc"] / r["ath_mc"] > 0.2)
    hours = [(r["peak_at"] - r["created_at"]) / 3600 for r in rows
             if r["peak_at"] and r["created_at"]]
    print("\n=== 整体 ===")
    print(f"  n={len(rows)}  "
          f"ATH 中位 ${statistics.median(aths):.2f}M（{min(aths):.2f}–{max(aths):.2f}M）  "
          f"回撤中位 {statistics.median(dds):.0f}%  "
          f"存活(>20%峰值) {alive}/{len(rows)}")
    if hours:
        print(f"  见顶用时中位 {statistics.median(hours):.0f}h"
              f"（{min(hours):.0f}–{max(hours):.0f}h）")

    # 分组统计（只有 n>=1 都列，提示样本量）
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["narrative"] or "未分类", []).append(r)
    print("\n=== 按叙事分组 ===")
    for name, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        g_ath = [x["ath_mc"] / 1e6 for x in items]
        g_dd = [(1 - x["cur_mc"] / x["ath_mc"]) * 100 for x in items if x["ath_mc"]]
        g_alive = sum(1 for x in items if x["cur_mc"] and x["ath_mc"]
                      and x["cur_mc"] / x["ath_mc"] > 0.2)
        flag = "" if len(items) >= 3 else "  ⚠样本不足"
        print(f"  {name[:18]:<20} n={len(items):<3} "
              f"峰值中位 ${statistics.median(g_ath):>6.2f}M  "
              f"回撤 {statistics.median(g_dd):>4.0f}%  "
              f"存活 {g_alive}/{len(items)}{flag}")
    return 0



def main() -> int:
    ap = argparse.ArgumentParser(description="叙事先例库")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)

    a = sub.add_parser("add")
    a.add_argument("--ca", required=True)
    a.add_argument("--chain", required=True)
    a.add_argument("--narrative", default=None)
    a.add_argument("--note", default=None)
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("refresh")
    r.add_argument("--ca", default=None)
    r.add_argument("--all", action="store_true")
    r.set_defaults(func=cmd_refresh)

    p = sub.add_parser("report")
    p.add_argument("--narrative", default=None)
    p.set_defaults(func=cmd_report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
