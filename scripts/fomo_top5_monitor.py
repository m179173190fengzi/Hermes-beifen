#!/usr/bin/env python3
"""FOMO (fomo.family) BSC wallet-follow monitor — v2, research-driven.

Design notes (from the 2026-10 research reports):
  * The GMGN "fomo" tag is a PLATFORM-USAGE tag, not a smart-money tag
    (42 of the top-100 holders of one token carried it) -> the tag only gives
    us a candidate pool; WALLET QUALITY FILTERS do the real work.
  * Ranking by absolute 30d realized profit is circular and rewards wash
    traders / luck. We now qualify wallets on 7d win rate, 7d trade count,
    7d AND 30d profitability (side-by-side stability), and holding period.
  * Consensus ">=2 wallets / 48h" is too loose for memes. Now:
      STRONG  = >=3 independent qualified wallets buying the same token
                within CONSENSUS_STRONG_WIN_H (60 min)  -> entry-grade
      OBSERVE = >=2 qualified wallets within 24h         -> watch only
    Independence = distinct funding sources (same-source = coordinated).
  * Follow the SELL side too: if a qualified wallet exits a token we alerted
    on, emit an exit warning.

Output (stdout, for the agent to enrich + deliver):
  NO_NEW_BUYS | DATA_UNAVAILABLE: ... | report block
"""
import json
import os
import subprocess
import sys
import time

PROXY = "http://127.0.0.1:7890"
STATE_DIR = os.path.expanduser("~/.hermes/cron/state")
STATE_PATH = os.path.join(STATE_DIR, "fomo_monitor.json")
CLI = "gmgn-cli"
CHAINS = ["bsc"]                 # BSC only
REPORT_CHAINS = {"bsc"}
LOOKBACK_H = 24

# ---- wallet quality gates (research-backed, tiered) ----
# A级 = stable in BOTH windows (research: "7天 vs 30天并排看")
# B级 = 30d proven but a red 7d (normal variance; 7d treated as score penalty)
MIN_WINRATE_7D_A = 0.50          # recommended band is 50-90%
MIN_WINRATE_7D_B = 0.45          # relax to 40-45% when no good wallets exist
MIN_TRADES_7D_A = 100            # separates real wallets from flukes
MIN_TRADES_7D_B = 50
MIN_HOLD_SEC = 60                # avoid second-level scalpers / phishing
MAX_STATS_PER_RUN = 40           # keep the script inside the cron time budget

# ---- consensus settings ----
CONSENSUS_STRONG_MIN = 3
CONSENSUS_STRONG_WIN_H = 1.0     # 60 minutes
CONSENSUS_OBSERVE_MIN = 2
CONSENSUS_OBSERVE_WIN_H = 24.0
MAX_STRONG_ROWS = 8
MAX_OBSERVE_ROWS = 6
MAX_EXIT_ROWS = 8

# ---- pool ----
POOL_CAP = 80
STATS_REFRESH_H = 20
TOP_RANKED = 12                  # how many qualified wallets we print
SEEN_KEEP_DAYS = 14
TRENDING_TOKENS_FOR_HARVEST = 12
HOLDERS_PER_TOKEN = 100          # mined from BSC trending token holders


def log(m):
    print(m, file=sys.stderr)


def run_cli(args, timeout=90):
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        p = subprocess.run([CLI] + args, capture_output=True, text=True,
                           env=env, timeout=timeout)
    except Exception as e:
        log("cli error %s (%s)" % (e, " ".join(args[:4])))
        return None
    if p.returncode != 0:
        log("cli rc=%s: %s" % (p.returncode, (p.stderr or "").strip()[:160]))
        return None
    try:
        return json.loads(p.stdout.strip())
    except Exception:
        log("bad json: %s" % " ".join(args[:4]))
        return None


def load_state():
    try:
        with open(STATE_PATH) as f:
            st = json.load(f)
    except Exception:
        st = {}
    for k in ("pool", "wallet", "seen", "token_buys", "alerted", "meta", "exit_seen"):
        st.setdefault(k, {})
    return st


def save_state(st):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_PATH)


def add_wallet(st, addr, chain, now, src):
    rec = st["pool"].get(addr)
    if rec is None:
        st["pool"][addr] = {"chain": chain, "first_seen": now, "last_seen": now, "src": src}
        return 1
    rec["last_seen"] = now
    return 0


def harvest(st, now):
    """Candidate pool = smart-money stream (fomo-tagged) + BSC trending holders."""
    added = 0
    for chain in CHAINS:
        data = run_cli(["track", "smartmoney", "--chain", chain, "--limit", "200", "--raw"])
        if data:
            for it in (data.get("list") or []):
                mi = it.get("maker_info") or {}
                addr = it.get("maker") or mi.get("address")
                if addr and "fomo" in (mi.get("tags") or []):
                    added += add_wallet(st, addr, chain, now, "smartmoney")

    trend = run_cli(["market", "trending", "--chain", "bsc", "--interval", "6h",
                     "--limit", str(TRENDING_TOKENS_FOR_HARVEST), "--raw"])
    cas = []
    if trend:
        for row in (trend.get("data", {}).get("rank") or trend.get("rank") or []):
            a = row.get("address")
            if a:
                cas.append(a)
    for ca in cas:
        h = run_cli(["token", "holders", "--chain", "bsc", "--address", ca,
                     "--limit", str(HOLDERS_PER_TOKEN), "--raw"])
        time.sleep(0.3)
        if not h:
            continue
        for it in (h.get("list") or []):
            tags = it.get("tags") or []
            addr = it.get("address")
            if addr and "fomo" in tags:
                added += add_wallet(st, addr, "bsc", now, "holders")

    if len(st["pool"]) > POOL_CAP:
        items = sorted(st["pool"].items(), key=lambda kv: kv[1].get("last_seen", 0), reverse=True)
        st["pool"] = dict(items[:POOL_CAP])
    log("harvest: +%d, pool=%d (mined %d tokens)" % (added, len(st["pool"]), len(cas)))
    return added


def _num(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def refresh_wallet_stats(st, now):
    """7d + 30d stats for pool wallets; qualify them. Cached STATS_REFRESH_H."""
    checked = 0
    # refresh the stalest / never-checked wallets first, newest-seen first
    cand = []
    for addr, rec in st["pool"].items():
        chain = rec.get("chain", "bsc")
        if chain not in REPORT_CHAINS:
            continue
        prev = st["wallet"].get(addr) or {}
        if prev and "tier" in prev and now - prev.get("checked", 0) < STATS_REFRESH_H * 3600:
            continue
        cand.append((prev.get("checked", 0), -rec.get("last_seen", 0), addr, chain))
    cand.sort()
    for _ck, _ls, addr, chain in cand[:MAX_STATS_PER_RUN]:
        prev = st["wallet"].get(addr) or {}
        s7 = run_cli(["portfolio", "stats", "--chain", chain, "--period", "7d", "--raw",
                      "--wallet", addr])
        time.sleep(0.3)
        s30 = run_cli(["portfolio", "stats", "--chain", chain, "--period", "30d", "--raw",
                       "--wallet", addr])
        time.sleep(0.3)
        if not s30:
            continue
        p30 = s30.get("pnl_stat") or {}
        p7 = (s7 or {}).get("pnl_stat") or {}
        buy7 = int(_num((s7 or {}).get("buy")))
        sell7 = int(_num((s7 or {}).get("sell")))
        trades7 = buy7 + sell7
        win7 = _num(p7.get("winrate"))
        hold7 = _num(p7.get("avg_holding_period"))
        profit30 = _num(s30.get("realized_profit"))
        cost30 = _num(s30.get("total_cost"), 1.0) or 1.0
        pnl30_pct = profit30 / cost30 * 100.0
        profit7 = _num((s7 or {}).get("realized_profit"))
        common30 = s30.get("common") or {}
        common7 = (s7 or {}).get("common") or {}
        fund = common30.get("fund_from") or common7.get("fund_from") or ""
        tags = common30.get("tags") or common7.get("tags") or []

        reasons = []
        if win7 < MIN_WINRATE_7D_B:
            reasons.append("7d胜率%d%%<%d%%" % (int(win7 * 100), int(MIN_WINRATE_7D_B * 100)))
        if trades7 < MIN_TRADES_7D_B:
            reasons.append("7d交易%d笔<%d" % (trades7, MIN_TRADES_7D_B))
        if hold7 < MIN_HOLD_SEC:
            reasons.append("持仓<60s")
        if profit30 <= 0:
            reasons.append("30d亏损")

        tier = "none"
        if not reasons:
            if (win7 >= MIN_WINRATE_7D_A and trades7 >= MIN_TRADES_7D_A and profit7 > 0):
                tier = "A"
            else:
                tier = "B"
        qualified = tier != "none"
        # transparent composite: win rate dominates, then pnl%, then sample size
        score = (win7 * 100.0
                 + max(min(pnl30_pct, 200.0), -50.0) * 0.3
                 + min(trades7, 1000) * 0.05
                 + (10.0 if tier == "A" else 0.0))
        st["wallet"][addr] = {
            "chain": chain, "win7": win7, "trades7": trades7, "hold7": hold7,
            "profit7": profit7, "profit30": profit30, "pnl30_pct": pnl30_pct,
            "token_num30": int(_num(p30.get("token_num"))),
            "fund_from": fund, "tags": tags, "qualified": qualified,
            "tier": tier, "why": ";".join(reasons),
            "score": round(score, 2), "checked": now,
        }
        checked += 1
    log("stats: refreshed %d" % checked)


def ranked_wallets(st, qualified_only=True):
    rows = []
    for addr, w in st["wallet"].items():
        if addr not in st["pool"] or w.get("chain") not in REPORT_CHAINS:
            continue
        if qualified_only and not w.get("qualified"):
            continue
        rows.append((addr, w))
    rows.sort(key=lambda kv: kv[1].get("score", 0), reverse=True)
    return rows


def collect_activity(st, top, now):
    """Pull buys + sells for the ranked wallets (last LOOKBACK_H)."""
    buy_cut = now - LOOKBACK_H * 3600
    fresh_buys, fresh_sells = [], []
    for addr, w in top:
        chain = w.get("chain", "bsc")
        for typ, bucket in (("buy", fresh_buys), ("sell", fresh_sells)):
            data = run_cli(["portfolio", "activity", "--chain", chain, "--wallet", addr,
                            "--type", typ, "--limit", "50", "--raw"])
            time.sleep(0.3)
            if not data:
                continue
            for a in (data.get("activities") or []):
                ts = int(_num(a.get("timestamp")))
                if ts < buy_cut:
                    continue
                token = a.get("token") or {}
                ca = token.get("address") or ""
                if not ca:
                    continue
                key = "%s|%s" % (typ, a.get("tx_hash") or a.get("transaction_hash")
                                 or "%s:%s:%s" % (addr, ca, ts))
                if key in st["seen"]:
                    continue
                st["seen"][key] = now
                tkey = "%s:%s" % (chain, ca)
                meta = st["meta"].setdefault(tkey, {"symbol": token.get("symbol") or "?",
                                                    "usd_running": 0.0})
                meta["symbol"] = token.get("symbol") or meta.get("symbol") or "?"
                usd = _num(a.get("cost_usd"))
                if typ == "buy":
                    meta["usd_running"] = _num(meta.get("usd_running")) + usd
                bucket.append({"wallet": addr, "chain": chain, "ca": ca,
                               "symbol": meta["symbol"], "usd": usd, "ts": ts,
                               "score": w.get("score", 0), "fund": w.get("fund_from", "")})
    return fresh_buys, fresh_sells


def clusters(st, top, now):
    """Split tracked tokens into STRONG / OBSERVE consensus, with independence check."""
    top_addrs = {a for a, _ in top}
    strong, observe = [], []
    for tkey, wallets in st["token_buys"].items():
        buyers = [w for w in wallets if w in top_addrs]
        if not buyers:
            continue
        chain, ca = tkey.split(":", 1)
        meta = st["meta"].get(tkey) or {}
        ts_sorted = sorted(wallets[w] for w in buyers)
        first_ts = ts_sorted[0]
        # widest window containing CONSENSUS_STRONG_MIN buyers
        win_span = None
        if len(ts_sorted) >= CONSENSUS_STRONG_MIN:
            win_span = min(ts_sorted[i + CONSENSUS_STRONG_MIN - 1] - ts_sorted[i]
                           for i in range(len(ts_sorted) - CONSENSUS_STRONG_MIN + 1))
        funds = {st["wallet"].get(w, {}).get("fund_from") or w for w in buyers}
        a_cnt = sum(1 for w in buyers if (st["wallet"].get(w) or {}).get("tier") == "A")
        b_cnt = sum(1 for w in buyers if (st["wallet"].get(w) or {}).get("tier") == "B")
        item = {"chain": chain, "ca": ca, "symbol": meta.get("symbol") or "?",
                "n": len(buyers), "usd": _num(meta.get("usd_running")),
                "first_ts": first_ts, "buyers": buyers,
                "a_cnt": a_cnt, "b_cnt": b_cnt,
                "funds": fund_list(funds), "indep": len(funds) >= min(2, len(buyers)),
                "span_min": int(win_span / 60) if win_span is not None else None}
        # STRONG needs conviction AND independence of quality: either 2 A-level
        # wallets, or >=3 wallets with at least one A-level, all inside 60 min.
        is_strong = (
            win_span is not None and win_span <= CONSENSUS_STRONG_WIN_H * 3600
            and ((a_cnt >= 2) or (len(buyers) >= CONSENSUS_STRONG_MIN and a_cnt >= 1))
        )
        if is_strong:
            item["tier"] = "strong"
            strong.append(item)
        elif len(buyers) >= CONSENSUS_OBSERVE_MIN and now - first_ts <= CONSENSUS_OBSERVE_WIN_H * 3600:
            item["tier"] = "observe"
            observe.append(item)
    strong.sort(key=lambda x: (x["a_cnt"], x["n"], x["usd"]), reverse=True)
    observe.sort(key=lambda x: (x["n"], x["usd"]), reverse=True)
    return strong[:MAX_STRONG_ROWS], observe[:MAX_OBSERVE_ROWS]


def exits(st, sells, top, now):
    """Qualified wallet sold something we previously alerted on -> exit warning."""
    tracked = set(st["alerted"].keys())
    out = []
    for s in sells:
        tkey = "%s:%s" % (s["chain"], s["ca"])
        if tkey not in tracked:
            continue
        ekey = "%s|%s" % (tkey, s["wallet"])
        if ekey in st["exit_seen"] and now - st["exit_seen"][ekey] < 12 * 3600:
            continue
        st["exit_seen"][ekey] = now
        out.append(s)
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out[:MAX_EXIT_ROWS]


def fund_list(funds):
    return ", ".join(sorted(str(f)[:18] for f in funds if f))


def prune(st, now):
    st["seen"] = {k: v for k, v in st["seen"].items() if now - v <= SEEN_KEEP_DAYS * 86400}
    st["token_buys"] = {k: {w: t for w, t in v.items() if now - t <= CONSENSUS_OBSERVE_WIN_H * 3600}
                        for k, v in st["token_buys"].items()}
    st["token_buys"] = {k: v for k, v in st["token_buys"].items() if v}
    st["exit_seen"] = {k: v for k, v in st["exit_seen"].items() if now - v <= 7 * 86400}
    keep = set(st["token_buys"])
    st["meta"] = {k: v for k, v in st["meta"].items() if k in keep or k in st["alerted"]}


def main():
    now = int(time.time())
    st = load_state()
    added = harvest(st, now)
    if not st["pool"]:
        save_state(st)
        print("DATA_UNAVAILABLE: no fomo wallets harvested")
        return
    refresh_wallet_stats(st, now)
    qualified = ranked_wallets(st, True)
    all_rows = ranked_wallets(st, False)
    log("wallets: pool=%d qualified=%d" % (len(st["pool"]), len(qualified)))
    track = qualified[:TOP_RANKED]
    if not track:
        track = all_rows[:5]

    buys, sells = collect_activity(st, track, now)
    for b in buys:
        st["token_buys"].setdefault("%s:%s" % (b["chain"], b["ca"]), {})[b["wallet"]] = b["ts"]
    strong, observe = clusters(st, track, now)
    exit_rows = exits(st, sells, track, now)
    for c in strong + observe:
        st["alerted"]["%s:%s" % (c["chain"], c["ca"])] = now
    prune(st, now)
    save_state(st)

    if not strong and not observe and not exit_rows:
        print("NO_NEW_BUYS")
        return

    L = []
    L.append("FOMO平台BSC钱包监控 v2（研究驱动: 平台标签只做候选池, 质量门槛做筛选）")
    L.append("")
    L.append("=== 合格钱包排名 ===")
    L.append("A级=7d胜率>=%d%%+7d>=%d笔+7d和30d均盈利(双窗口稳定) | B级=7d胜率>=%d%%+7d>=%d笔+30d盈利(单周亏损属正常方差) | 均要求持仓>=%ds"
             % (int(MIN_WINRATE_7D_A * 100), MIN_TRADES_7D_A,
                int(MIN_WINRATE_7D_B * 100), MIN_TRADES_7D_B, MIN_HOLD_SEC))
    if qualified:
        for i, (addr, w) in enumerate(qualified[:TOP_RANKED], 1):
            L.append("%d. [%s级] %s | 7d胜率%d%% | 7d %d笔 | 30d PnL %+.1f%% ($%d) | 7d盈利%+d | 持仓%.0f分钟 | 评分%.0f | 资金源 %s"
                     % (i, w.get("tier", "?"), addr, int(w["win7"] * 100), w["trades7"],
                        w["pnl30_pct"], int(w["profit30"]), int(w["profit7"]),
                        w["hold7"] / 60.0, w["score"], w["fund_from"] or "未知"))
    else:
        L.append("(⚠️ 本轮无钱包通过质量门槛; 以下仅为候选池中评分最高者, 信号权重低)")
        for i, (addr, w) in enumerate(all_rows[:5], 1):
            L.append("%d. %s | 7d胜率%d%% | 7d %d笔 | 30d PnL %+.1f%% | 未通过: %s"
                     % (i, addr, int(w["win7"] * 100), w["trades7"], w["pnl30_pct"],
                        w.get("why") or "评分不足"))
    if added:
        L.append("(候选池新增 %d 个fomo钱包, 当前 %d 个)" % (added, len(st["pool"])))

    if strong:
        L.append("")
        L.append("=== 🔥 强共识 (>=%d个合格钱包, <=%d分钟内同买) — 入场级 ==="
                 % (CONSENSUS_STRONG_MIN, int(CONSENSUS_STRONG_WIN_H * 60)))
        for c in strong:
            L.append("- %s | %d个钱包(A级%d/B级%d) | 合计$%d | 窗口%d分钟 | 独立性: %s | CA %s"
                     % (c["symbol"], c["n"], c["a_cnt"], c["b_cnt"], int(c["usd"]), c["span_min"] or 0,
                        ("独立(%d个资金源: %s)" % (len(c["funds"].split(', ')), c["funds"]))
                        if c["indep"] else "⚠️资金源关联(可能协同)",
                        c["ca"]))
    if observe:
        L.append("")
        L.append("=== 👀 观察级 (>=%d个钱包, 24h内同买, 不入场仅观察) ==="
                 % CONSENSUS_OBSERVE_MIN)
        for c in observe:
            L.append("- %s | %d个钱包(A级%d/B级%d) | 合计$%d | 首次%d分钟前 | CA %s"
                     % (c["symbol"], c["n"], c["a_cnt"], c["b_cnt"], int(c["usd"]),
                        int((now - c["first_ts"]) // 60), c["ca"]))
    if exit_rows:
        L.append("")
        L.append("=== 🚪 退出警报 (合格钱包卖出了我们提示过的币) ===")
        for e in exit_rows:
            L.append("- %s | 钱包 %s 卖出 $%d | %d分钟前 | CA %s"
                     % (e["symbol"], e["wallet"][:10] + "…", int(e["usd"]),
                        int((now - e["ts"]) // 60), e["ca"]))
    print("\n".join(L))


if __name__ == "__main__":
    main()
