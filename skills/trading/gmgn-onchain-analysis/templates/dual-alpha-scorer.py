#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BSC+SOL 双链 Alpha 简报 — 评分器（templates/dual-alpha-scorer.py）

与 templates/bsc-alpha-scorer.py 的唯一区别：**链名参数化**，一条脚本跑两条链。
评分档位（A/B/C/D）与 11 项判据与单链版完全一致，保证两链分数可横向比较排序。

用法：
  1) 抓数据（两条独立 terminal 调用，文件名用短标签 + 固定 TS）：
     TS=$(date +%s)
     HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
       gmgn-cli market trending --chain bsc --interval 6h --limit 30 --raw > /tmp/alpha_bsc_6h_$TS.json
     HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
       gmgn-cli market trending --chain sol --interval 6h --limit 30 --raw > /tmp/alpha_sol_6h_$TS.json
  2) 跑初版（E 全 4 占位）：
     cp templates/dual-alpha-scorer.py /tmp/score_dual_<ts>.py
     python3 /tmp/score_dual_<ts>.py /tmp/alpha_bsc_6h_$TS.json bsc
     python3 /tmp/score_dual_<ts>.py /tmp/alpha_sol_6h_$TS.json sol
  3) 对头部候选（base 分 ≥58 的）抓 token info 反推叙事，手填 E_MAP 复算。

⚠️ E（叙事 0-8）档位（不要为了凑 70 抬 E，实测教训 2026-10-18）：
   8 = 老梗主盘 / CTO 顶级叙事（Ansem、Murad、CZ 级人物 IP）
   6-7 = 有官网+推特+TG 的真实梗、CTO、强共识
   5-6 = 有推特官网的实际梗但非主盘
   3   = 推广推文伪装的新盘 / 匿名盘
   4   = 默认占位（未核叙事时）

⚠️ 输出说明：
   - TOP5 段按 volume 降序，BSC 常年合成/证券盘霸榜（已用 `合成/证券` 标注，禁输出 CA）
   - SCORED 段每行含完整 address（不截断）+ created age + 6h/1h/5m 三档涨幅
   - 报告只保留 ≥70；60-69 与 55-59 一律不输出（BSC+SOL 双链 cron 硬规则）
"""
import json
import sys
import time

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/alpha_bsc_6h.json"
chain = sys.argv[2] if len(sys.argv) > 2 else "?"
now = time.time()

# 手填叙事分（symbol -> 0-8）；见文件头档位表
E_MAP = {}

STOCK_SYMS = {"NVDAB", "QQQB", "pPOLY", "AAPLB", "BNCB", "GMEB", "BNC4", "FXIon",
              "SKHYB", "SPCXB", "SPYB", "TSLAB", "GSTOCK"}
COMPANY_HINTS = ["nvidia", "apple", "invesqo", "paimon polymarket", "cea industries",
                 "sk hynix", "ishares", "gamestop", "corp", "holdings", "industries",
                 "etf", "spv", "nasdaq", "microstrategy"]


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
    """合成/证券/SPV 盘：非 meme 博弈标的，照列 TOP5 但不进优质标的/新币段。"""
    if (d.get("symbol") or "").upper() in STOCK_SYMS:
        return True
    nm = (d.get("name") or "").lower()
    return any(h in nm for h in COMPANY_HINTS)


def A_c(d):
    """共识 0-25：SM(0-18) + KOL(0-7)。档位必须宽松，否则全场无人达 60。"""
    sm, kol = int(f(d.get("smart_degen_count"))), int(f(d.get("renowned_count")))
    b = 18 if sm >= 30 else 15 if sm >= 15 else 12 if sm >= 8 else 8 if sm >= 4 else 4 if sm >= 1 else 0
    k = 7 if kol >= 30 else 6 if kol >= 15 else 5 if kol >= 8 else 3 if kol >= 4 else 1 if kol >= 1 else 0
    return min(25, b + k)


def B_h(d):
    """数据健康 0-20：rug / bundler / top10 / wash。"""
    b, rug, bun, t = 20, f(d.get("rug_ratio")), f(d.get("bundler_rate")), f(d.get("top_10_holder_rate"))
    b -= 12 if rug > 0.3 else 5 if rug > 0.1 else 0
    b -= 10 if bun > 0.3 else 5 if bun > 0.15 else 0
    b -= 8 if t > 0.7 else 5 if t > 0.5 else 3 if t > 0.2 else 0
    if d.get("is_wash_trading") is True:
        b -= 8
    return max(0, b)


def C_s(d):
    """体量 0-12：MC(0-5) + LP(0-4) + 6h 量(0-3)。⚠️ ≥70 需 C≥10 → MC≥$5M+LP≥$500K+vol≥$1M。"""
    mc, lp, v = f(d.get("market_cap")), f(d.get("liquidity")), f(d.get("volume"))
    s = 5 if mc >= 20e6 else 4.5 if mc >= 10e6 else 4 if mc >= 5e6 else 3 if mc >= 2e6 else 2.5 if mc >= 1e6 else 2 if mc >= 0.5e6 else 1
    s += 4 if lp >= 1e6 else 3.5 if lp >= 500e3 else 3 if lp >= 200e3 else 2 if lp >= 50e3 else 1.5 if lp >= 30e3 else 0.5
    s += 3 if v >= 1e6 else 2.5 if v >= 500e3 else 2 if v >= 200e3 else 1.5 if v >= 50e3 else 1
    return min(12, s)


def D_m(d):
    """动量 0-10。⚠️ 必须先取 1h：1h ≤ -20% 直接压到 2，6h 大涨 + 1h 深跌 = 出货。"""
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
    """11 项快评（trending 字段版）。⑨粉丝真实 / ⑩holders 增长 无法用 trending 验证，固定 False。
    实盘通常 7-9/11，8/11 已属良好——不要因未满分降级判断。"""
    c = [
        f(d.get("liquidity")) > 30000,                                          # ① LP>$30K
        f(d.get("lock_percent")) >= 0.5 or str(d.get("burn_status") or "").lower() in ("yes", "burn", "burned"),  # ② 锁定/销毁
        (lambda r: r == 1 or (isinstance(r, str) and r in ("1", "yes")))(d.get("is_renounced")),  # ③ 铸币权关（EVM 用 is_renounced）
        True,                                                                   # ④ 冻结权（SOL 需另查 security；EVM 不适用计过）
        f(d.get("top_10_holder_rate")) < 0.20,                                   # ⑤ top10<20%
        f(d.get("bundler_rate")) < 0.15,                                         # ⑥ 无关联/bundle
        str(d.get("creator_token_status")) == "creator_close",                   # ⑦ dev 无抛弃史
        (now - f(d.get("creation_timestamp"))) / 3600 > 168 and bool(d.get("twitter_username") or d.get("website")),  # ⑧ 社交>1周
        False,                                                                   # ⑨ 粉丝真实（不可验证）
        False,                                                                   # ⑩ holders 增长（不可验证）
        (f(d.get("volume")) / f(d.get("liquidity")) if f(d.get("liquidity")) else 0) >= 0.5,  # ⑪ vol/LP≥0.5
    ]
    return sum(1 for x in c if x)


with open(path) as fh:
    raw = json.load(fh)
rank = raw.get("data", {}).get("rank") if isinstance(raw, dict) else raw
if rank is None:
    rank = raw if isinstance(raw, list) else []
print(f"CHAIN={chain} ITEMS={len(rank)} file={path}")

by_vol = sorted(rank, key=lambda x: f(x.get("volume")), reverse=True)
print("\n=== TOP5 by volume (禁输出 CA) ===")
for i, d in enumerate(by_vol[:5], 1):
    tag = " [合成/证券-非meme]" if is_stock_like(d) else ""
    print(f"{i}. {d.get('symbol')} | MC {usd(d.get('market_cap'))} | LP {usd(d.get('liquidity'))} | "
          f"6h {f(d.get('price_change_percent')):+.1f}% | vol {usd(d.get('volume'))}{tag}")

rows = []
for d in rank:
    s = d.get("symbol") or "?"
    A, B, C, D = A_c(d), B_h(d), C_s(d), D_m(d)
    e = E_MAP.get(s, 4)
    rows.append((A + B + C + D + e, s, A, B, C, D, e, eleven(d), is_stock_like(d), d))
rows.sort(key=lambda x: -x[0])
print("\n=== SCORED (报告只取 >=70；60-69 / 55-59 不外发) ===")
for total, s, A, B, C, D, e, el, stk, d in rows:
    age_h = (now - f(d.get("creation_timestamp"))) / 3600
    print(f"{total:.1f} | {s} | A{A} B{B} C{C} D{D} E{e} | 11项={el} | "
          f"MC {usd(d.get('market_cap'))} hiMC {usd(d.get('history_highest_market_cap'))} | LP {usd(d.get('liquidity'))} | vol {usd(d.get('volume'))} | "
          f"6h {f(d.get('price_change_percent')):+.1f}% 1h {f(d.get('price_change_percent1h')):+.1f}% 5m {f(d.get('price_change_percent5m')):+.1f}% | "
          f"SM{int(f(d.get('smart_degen_count')))} KOL{int(f(d.get('renowned_count')))} "
          f"holders{int(f(d.get('holder_count')))} t10{f(d.get('top_10_holder_rate')):.3f} "
          f"b{f(d.get('bundler_rate')):.3f} rug{f(d.get('rug_ratio')):.3f} | "
          f"age{age_h:.1f}h | ct={d.get('creator_token_status')} | plat={d.get('launchpad_platform')} | "
          f"{d.get('address')} | {'STOCK' if stk else ''}")
