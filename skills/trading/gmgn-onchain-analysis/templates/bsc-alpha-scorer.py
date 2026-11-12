#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BSC 单链 Alpha 简报 — 评分器（templates/bsc-alpha-scorer.py）

用途：从 `gmgn-cli market trending --chain bsc --interval 6h --limit 30 --raw` 的落盘
JSON 直接算出：①成交量 TOP5 ②75分制 (A/B/C/D) ③11项评分 ④合成/证券盘剔除 ⑤总分排序。
零额外 API 请求（11项判据全在 trending raw 字段里，见 references/bsc-only-alpha-report.md）。

用法：
  1) 抓数据：
     HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
       gmgn-cli market trending --chain bsc --interval 6h --limit 30 --raw > /tmp/bsc_tr_6h.json
  2) 跑：
     cp templates/bsc-alpha-scorer.py /tmp/score_bsc_<ts>.py   # 避免 /tmp 同名覆盖
     python3 /tmp/score_bsc_<ts>.py /tmp/bsc_tr_6h.json
  3) E(叙事 0-8) 按下方 E_MAP 手填（默认 4）。只对最终入榜 2-3 个候选补 token info 取叙事。

⚠️ 评分档位表见 references/bsc-only-alpha-report.md「75分制 A/B/C/D 具体档位表」——
   A 档位必须宽松（SM>=30 即 18 分），否则全场无人达 60、报告发虚失真（2026-10-15 实测教训）。
"""
import json, sys, time

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/bsc_tr_6h.json"
now = time.time()

# 手填叙事分（symbol -> 0-8）；老梗主盘/CTO 6-7 / 有推特官网的实际梗 5-6 / 推广伪装新盘 3
E_MAP = {}

STOCK_SYMS = {"NVDAB", "QQQB", "pPOLY", "AAPLB", "BNCB", "GMEB", "BNC4", "FXIon", "SKHYB"}
COMPANY_HINTS = ["nvidia", "apple", "invesqo", "paimon polymarket", "cea industries",
                 "sk hynix", "ishares", "gamestop", "corp", "holdings", "industries", "etf", "spv"]


def f(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def usd(v):
    v = f(v)
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    if v >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def is_stock_like(d):
    nm = (d.get("name") or "").lower()
    if (d.get("symbol") or "").upper() in STOCK_SYMS:
        return True
    circ = f(d.get("total_supply"))
    plat = d.get("launchpad_platform") or ""
    if not plat and 0 < circ < 2e6 and any(h in nm for h in COMPANY_HINTS):
        return True
    return any(h in nm for h in COMPANY_HINTS)


def A_c(d):
    sm, kol = int(f(d.get("smart_degen_count"))), int(f(d.get("renowned_count")))
    b = 18 if sm >= 30 else 15 if sm >= 15 else 12 if sm >= 8 else 8 if sm >= 4 else 4 if sm >= 1 else 0
    k = 7 if kol >= 30 else 6 if kol >= 15 else 5 if kol >= 8 else 3 if kol >= 4 else 1 if kol >= 1 else 0
    return min(25, b + k)


def B_h(d):
    b, rug, bun, t = 20, f(d.get("rug_ratio")), f(d.get("bundler_rate")), f(d.get("top_10_holder_rate"))
    b -= 12 if rug > 0.3 else 5 if rug > 0.1 else 0
    b -= 10 if bun > 0.3 else 5 if bun > 0.15 else 0
    b -= 8 if t > 0.7 else 5 if t > 0.5 else 3 if t > 0.2 else 0
    if d.get("is_wash_trading") is True:
        b -= 8
    return max(0, b)


def C_s(d):
    mc, lp, v = f(d.get("market_cap")), f(d.get("liquidity")), f(d.get("volume"))
    s = 5 if mc >= 20e6 else 4.5 if mc >= 10e6 else 4 if mc >= 5e6 else 3 if mc >= 2e6 else 2.5 if mc >= 1e6 else 2 if mc >= 0.5e6 else 1
    s += 4 if lp >= 1e6 else 3.5 if lp >= 500e3 else 3 if lp >= 200e3 else 2 if lp >= 50e3 else 1.5 if lp >= 30e3 else 0.5
    s += 3 if v >= 1e6 else 2.5 if v >= 500e3 else 2 if v >= 200e3 else 1.5 if v >= 50e3 else 1
    return min(12, s)


def D_m(d):
    c6, c1 = f(d.get("price_change_percent")), f(d.get("price_change_percent1h"))
    if c1 <= -20:
        return 2
    if c6 >= 40 and c1 >= 0:
        return 10
    if c6 >= 20:
        return 8
    if c6 >= 5:
        return 6
    if c6 >= 0:
        return 5
    if c6 >= -10:
        return 4
    if c6 >= -25:
        return 2
    return 0


def eleven(d):
    c = [
        f(d.get("liquidity")) > 30000,
        f(d.get("lock_percent")) >= 0.5 or str(d.get("burn_status") or "").lower() in ("yes", "burn", "burned"),
        (lambda r: r == 1 or (isinstance(r, str) and r in ("1", "yes")))(d.get("is_renounced")),
        True,
        f(d.get("top_10_holder_rate")) < 0.20,
        f(d.get("bundler_rate")) < 0.15,
        str(d.get("creator_token_status")) == "creator_close",
        (now - f(d.get("creation_timestamp")))/3600 > 168 and bool(d.get("twitter_username") or d.get("website")),
        False,
        False,
        (f(d.get("volume")) / f(d.get("liquidity")) if f(d.get("liquidity")) else 0) >= 0.5,
    ]
    return sum(1 for x in c if x)


with open(path) as fh:
    raw = json.load(fh)
rank = raw.get("data", {}).get("rank") if isinstance(raw, dict) else raw
if rank is None:
    rank = raw if isinstance(raw, list) else []
print(f"ITEMS={len(rank)}  file={path}")

by_vol = sorted(rank, key=lambda x: f(x.get("volume")), reverse=True)
print("\n=== TOP5 by volume (禁输出 CA) ===")
for i, d in enumerate(by_vol[:5], 1):
    tag = " [合成/证券-非meme]" if is_stock_like(d) else ""
    print(f"{i}. {d.get('symbol')} | MC {usd(d.get('market_cap'))} | LP {usd(d.get('liquidity'))} | 6h {f(d.get('price_change_percent')):+.1f}% | 量 {usd(d.get('volume'))}{tag}")

rows = []
for d in rank:
    s = d.get("symbol") or "?"
    A, B, C, D = A_c(d), B_h(d), C_s(d), D_m(d)
    e = E_MAP.get(s, 4)
    rows.append((A + B + C + D + e, s, A, B, C, D, e, eleven(d), is_stock_like(d), d))
rows.sort(key=lambda x: -x[0])
print("\n=== SCORED (75分制 + 11项；双门槛=总分>=60 且 11项>=6) ===")
for total, s, A, B, C, D, e, el, stk, d in rows:
    flag = "STOCK-剔除" if stk else ("达标" if (total >= 60 and el >= 6) else "")
    print(f"{total:.0f} | {s} | A{A} B{B} C{C} D{D} E{e} | 11项={el} | MC {usd(d.get('market_cap'))} | vol {usd(d.get('volume'))} | "
          f"6h {f(d.get('price_change_percent')):+.1f}% 1h {f(d.get('price_change_percent1h')):+.1f}% | "
          f"SM{int(f(d.get('smart_degen_count')))} KOL{int(f(d.get('renowned_count')))} t10{f(d.get('top_10_holder_rate'))} b{f(d.get('bundler_rate'))} "
          f"| {d.get('address')} | {flag}")
