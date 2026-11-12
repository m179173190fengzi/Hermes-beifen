#!/usr/bin/env python3
"""
Cron Report Parser Template
============================
Reads GMGN CLI JSON files saved to /tmp/ (via the two-pass data-fetch pattern)
and generates a formatted on-chain report in Telegram-compatible format.

TWO-PASS USAGE (outside execute_code):

  Batch 1:
    terminal("curl -s --max-time 10 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT' > /tmp/btc_price.json")
    terminal("curl -s --max-time 10 'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT' > /tmp/btc_24h.json")
    terminal("curl -s --max-time 10 'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT' > /tmp/eth_price.json")
    terminal("curl -s --max-time 10 'https://api.alternative.me/fng/?limit=1' > /tmp/fng.json")
    terminal("gmgn-cli market trending --chain sol --interval 5m --order-by volume --limit 20 --raw > /tmp/sol_5m.json")
    terminal("gmgn-cli market trending --chain sol --interval 1h --order-by volume --limit 20 --raw > /tmp/sol_1h.json")
    terminal("gmgn-cli market trending --chain robinhood --interval 5m --order-by volume --limit 20 --raw > /tmp/rh_5m.json")
    terminal("gmgn-cli market trending --chain robinhood --interval 1h --order-by volume --limit 20 --raw > /tmp/rh_1h.json")

  Batch 2 (after Batch 1 completes):
    terminal("gmgn-cli market signal --chain sol --signal-type 12 --raw > /tmp/sol_signal.json")
    terminal("gmgn-cli market hot-searches --chain sol --chain robinhood --interval 1h --limit 20 --raw > /tmp/hot_searches.json")

  Batch 3 (generate report):
    write_file("/tmp/cron-report-parser.py", THIS_FILE)
    terminal("python3 /tmp/cron-report-parser.py")

CONFIGURATION — edit these for each report:
"""
import json, datetime, os, subprocess

# ── Config ──────────────────────────────────────────────────────────────────
CHAINS = ["sol", "robinhood"]         # chains to report on
TRENDING_LIMITS = {"sol": 8, "robinhood": 5}
SIGNAL_LIMIT = 12
HIGH_SM_THRESHOLD = 24                # minimum SM count for "精选高SM" highlight
RISK_RUG_THRESHOLD = 0.3
RISK_TOP10_THRESHOLD = 0.5
RECKLESS_RUG_THRESHOLD = 0.8          # rug above this = "skip entirely" warning

# Report date override (or None to use today)
REPORT_DATE = None  # "2026-07-30"

# ── Helpers ─────────────────────────────────────────────────────────────────

def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return None

def fmt_mc(v):
    """Format market cap/volume/liquidity: $1.2B / $45M / $320K / $500."""
    if not v: return "$0"
    v = float(v)
    if v >= 1e9:  return f"${v/1e9:.2f}B"
    if v >= 1e6:  return f"${v/1e6:.1f}M"
    if v >= 1e3:  return f"${v/1e3:.0f}K"
    return f"${v:.0f}"

def fmt_chg(v):
    """Format price change percent with sign."""
    if v is None: return "0%"
    return f"{float(v):+.1f}%"

def quality_signal(t):
    """Return 🟢/🟡/🔴 based on token fields."""
    rug = float(t.get("rug_ratio", 0))
    wash = t.get("is_wash_trading", False)
    sm = t.get("smart_degen_count", 0)
    top10 = float(t.get("top_10_holder_rate", 0))
    if wash is True or (rug is not None and rug > RISK_RUG_THRESHOLD) or (top10 is not None and top10 > 0.8):
        return "🔴"
    # creator_close + SM>=3 = decent
    creator_close = t.get("creator_close", False)
    if creator_close and sm and sm >= 3:
        return "🟢"
    if sm and sm >= 3:
        return "🟢"
    if sm and sm >= 1:
        return "🟡"
    return "⚪"

def get_rank(data):
    """Extract rank array from GMGN trending response (handles raw vs styled)."""
    if not data:
        return []
    if isinstance(data, list):
        return data
    d = data.get("data", {})
    if isinstance(d, dict) and "rank" in d:
        return d["rank"]
    return []

def extract_ca_line(addr):
    """Return a single-line CA string: CA: `<addr>` (inline code, not fenced)."""
    return f"CA: `{addr}`"

# ── Narrative Detection ─────────────────────────────────────────────────────

NARRATIVE_PATTERNS = [
    ("Ansem叙事", lambda s: s in ("ANSEM", "ANUSEM", "ANSWER") or "ANSEM" in s or "SULTAN" in s),
    ("疫情梗", lambda s: s in ("FAUCI", "FRAUDCI") or "FAUCI" in s or "FRAUD" in s or "CORONA" in s or "COVID" in s or "RATG13" in s),
    ("CZ叙事", lambda s: s == "CZ" or "CZ" in s or s in ("BINANCE", "HEYI")),
    ("猫狗类meme", lambda s: s in ("POPCAT", "MEW", "CATE", "CRYINGCAT", "VIBECAT", "CASHCAT", "PIPEDOG") or s.endswith("CAT") or s.endswith("DOG")),
    ("Trump叙事", lambda s: "TRUMP" in s or s in ("MAGA", "DONALD")),
    ("Tate叙事", lambda s: "TATE" in s or s in ("TOPG", "TOPGIRL")),
    ("Murad叙事", lambda s: "MURAD" in s),
    ("社区梗/反讽", lambda s: s in ("BITCH", "IQ", "DIP", "TIGHT", "AGENSIS", "BOOMER")),
    ("技术/生态", lambda s: s in ("AI", "TA", "RWA", "INDEX", "MEMES", "PONS")),
    ("Kabosu/Shib", lambda s: s in ("KABOSU", "SHIB", "KABO") or "KABOSU" in s),
]

def detect_narratives(tokens, label="Solana"):
    """Scan token symbols for known narrative patterns. Returns list of strings."""
    if not tokens:
        return []
    syms = [t.get("symbol", "").upper() for t in tokens[:30]]
    found = []
    for nname, matcher in NARRATIVE_PATTERNS:
        hits = [s for s in syms if matcher(s)]
        if hits:
            found.append(f"{nname}: {' '.join(hits[:3])}")
    return found

# ── Fallback: blockchain.info for BTC ───────────────────────────────────────

def fallback_btc_price():
    """Try blockchain.info when Binance fails."""
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "8", "https://blockchain.info/ticker"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            d = json.loads(r.stdout)
            return str(d.get("USD", {}).get("last", "?"))
    except Exception:
        pass
    return "?"

# ═══════════════════════════════════════════════════════════════════════════
# Section Builders
# ═══════════════════════════════════════════════════════════════════════════

# ── Section 1: Market Overview ─────────────────────────────────────────────

def build_market_section():
    """BTC/ETH prices from Binance. Fallback: blockchain.info for BTC."""
    btc_p = read_json("/tmp/btc_price.json")
    btc_24 = read_json("/tmp/btc_24h.json")
    eth_p = read_json("/tmp/eth_price.json")
    fng = read_json("/tmp/fng.json")

    btc_usd = (btc_p or {}).get("price")
    btc_chg = (btc_24 or {}).get("priceChangePercent")
    eth_usd = (eth_p or {}).get("price")

    # BTC fallback if Binance failed
    if not btc_usd:
        btc_usd = fallback_btc_price()
        btc_chg = "?"  # no 24h change from blockchain.info

    btc_line = f"**BTC:** ${btc_usd}" + (f" | 24h {btc_chg}%" if btc_chg is not None else "")
    eth_line = f"**ETH:** ${eth_usd}" if eth_usd else "**ETH:** 数据获取失败"

    fng_str = ""
    if fng and fng.get("data"):
        fng_score = fng["data"][0].get("value", "?")
        fng_label = fng["data"][0].get("value_classification", "?")
        fng_str = f" | 恐惧贪婪指数: {fng_score} ({fng_label})"

    return (
        "## 1️⃣ 市场概况\n"
        f"{btc_line}\n"
        f"{eth_line}{fng_str}\n"
        f"> 大盘情绪{'恐惧' if fng_score and int(fng_score) < 45 else '中性' if fng_score and int(fng_score) < 55 else '贪婪' if fng_score else '—'}区间，整体偏{'保守' if fng_score and int(fng_score) < 45 else '活跃'}\n"
    )

# ── Section 2: On-Chain Hotspots ───────────────────────────────────────────

def build_trending_block(path, label, limit=8):
    """Format a trending data block. Telegram-compatible: inline code for CA, lists for structure."""
    data = read_json(path)
    if not data:
        return f"**{label}** — 数据获取失败\n"
    rank = get_rank(data)
    if not rank:
        return f"**{label}** — 无数据\n"
    rank.sort(key=lambda t: float(t.get("volume", 0) or 0), reverse=True)

    lines = [f"**{label}**"]
    for i, t in enumerate(rank[:limit]):
        sym, addr = t.get("symbol", "?"), t.get("address", "?")
        mc = fmt_mc(t.get("market_cap", 0))
        vol = fmt_mc(t.get("volume", 0))
        chg = fmt_chg(t.get("price_change_percent"))
        sm = t.get("smart_degen_count", 0)
        rug = t.get("rug_ratio", 0)
        kol = t.get("renowned_count", 0)
        top10 = t.get("top_10_holder_rate", 0)
        sig = quality_signal(t)
        lines.append(f"{i+1}. **${sym}** {sig} — MC {mc} | Vol {vol} | {chg} | SM:{sm} | KOL:{kol} | Rug:{rug}")
        lines.append(f"   {extract_ca_line(addr)}")
        if top10:
            lines.append(f"   Top10:{top10*100:.0f}%")
    return "\n".join(lines)

def build_hotspots_section():
    """Combine Solana + Robinhood trending, narratives, cross-chain mirrors."""
    parts = ["## 2️⃣ 链上热点\n"]

    # ── Solana 5m ──
    parts.append(build_trending_block("/tmp/sol_5m.json", "🔥 Solana 5m 涨幅榜", TRENDING_LIMITS.get("sol", 8)))
    parts.append("")

    # ── Solana 1h for narrative detection ──
    sol_1h_data = read_json("/tmp/sol_1h.json")
    sol_1h_tokens = get_rank(sol_1h_data)
    sol_narr = detect_narratives(sol_1h_tokens)
    if sol_narr:
        parts.append(f"> **Solana叙事聚类:** {' | '.join(sol_narr)}")
        parts.append("")

    parts.append(build_trending_block("/tmp/sol_1h.json", "🔥 Solana 1h 趋势榜", TRENDING_LIMITS.get("sol", 8)))

    # ── Robinhood ──
    parts.append("---\n")
    parts.append(build_trending_block("/tmp/rh_5m.json", "🔥 Robinhood Chain 5m 涨幅榜", TRENDING_LIMITS.get("robinhood", 5)))
    parts.append("")
    parts.append(build_trending_block("/tmp/rh_1h.json", "🔥 Robinhood Chain 1h 趋势榜", TRENDING_LIMITS.get("robinhood", 5)))

    # ── Cross-chain mirror detection ──
    rh_1h_data = read_json("/tmp/rh_1h.json")
    rh_1h_tokens = get_rank(rh_1h_data)
    sol_syms = {t.get("symbol", "").upper() for t in sol_1h_tokens}
    rh_syms = {t.get("symbol", "").upper() for t in rh_1h_tokens}
    mirrors = sol_syms & rh_syms
    if mirrors:
        parts.append(f"\n> 🔗 跨链镜像: {'、'.join(sorted(mirrors)[:6])} 同时出现在Solana和RH趋势榜")

    # Also check hot-searches for cross-chain names
    hot_data = read_json("/tmp/hot_searches.json")
    if hot_data:
        blocks = hot_data if isinstance(hot_data, list) else hot_data.get("data", [])
        sol_hot_syms, rh_hot_syms = set(), set()
        for b in blocks:
            if isinstance(b, dict):
                if b.get("chain") == "sol":
                    sol_hot_syms.update(t.get("symbol", "").upper() for t in b.get("tokens", []))
                elif b.get("chain") == "robinhood":
                    rh_hot_syms.update(t.get("symbol", "").upper() for t in b.get("tokens", []))
        cross_hot = sol_hot_syms & rh_hot_syms
        if cross_hot and not mirrors:
            parts.append(f"\n> 🔗 跨链热搜重叠: {'、'.join(sorted(cross_hot)[:6])} — 集群叙事跨链迹象")

    return "\n".join(parts)

# ── Section 3: Smart Money ──────────────────────────────────────────────────

def build_smart_money_section():
    """SM signal events + high-SM token highlights from 1h trending."""
    parts = ["## 3️⃣ 聪明钱动向\n"]

    # SM signal events (type 12 = smart money buy)
    sig_data = read_json("/tmp/sol_signal.json")
    if sig_data and isinstance(sig_data, list):
        parts.append("**Solana — SM买入信号**\n")
        seen = {}
        for s in sig_data:
            addr = s.get("token_address", "")
            if addr not in seen:
                seen[addr] = s
            if len(seen) >= SIGNAL_LIMIT:
                break

        for addr, s in list(seen.items())[:SIGNAL_LIMIT]:
            mc = fmt_mc(s.get("trigger_mc", 0))
            times = s.get("signal_times", 0)
            sym = s.get("data", {}).get("symbol", "?")
            cur = s.get("cur_data", {})
            liq = fmt_mc(cur.get("liquidity", 0))
            holders = cur.get("holder_count", "?")
            parts.append(f"- **${sym}** | 触发MC:{mc} | 信号:{times}次 | 流动性:{liq} | Holders:{holders}")
            parts.append(f"  {extract_ca_line(addr)}")

        parts.append(f"\n> 共{len(seen)}条唯一代币SM买入信号\n")
    else:
        parts.append("> Solana SM信号数据获取失败或为空\n")

    # ── High-SM token highlights from 1h trending ──
    sol_1h = get_rank(read_json("/tmp/sol_1h.json"))
    high_sm = [
        t for t in sol_1h
        if t.get("smart_degen_count", 0) and t.get("smart_degen_count", 0) >= HIGH_SM_THRESHOLD
    ]
    high_sm.sort(key=lambda t: t.get("smart_degen_count", 0), reverse=True)
    if high_sm:
        parts.append("\n**精选高SM代币 (SM≥{})**\n".format(HIGH_SM_THRESHOLD))
        for t in high_sm[:5]:
            sym, addr = t.get("symbol", "?"), t.get("address", "?")
            sm = t.get("smart_degen_count", 0)
            kol = t.get("renowned_count", 0)
            mc = fmt_mc(t.get("market_cap", 0))
            vol = fmt_mc(t.get("volume", 0))
            rug = t.get("rug_ratio", 0)
            top10 = t.get("top_10_holder_rate", 0)
            # Extra inline note
            notes = []
            if rug and rug < 0.1: notes.append("✅低Rug")
            if rug and rug > 0.5: notes.append("🚫高Rug")
            if top10 and top10 < 0.2: notes.append("筹码分散")
            if top10 and top10 > 0.5: notes.append("筹码集中")
            note_str = f" | {' '.join(notes)}" if notes else ""
            parts.append(f"- **${sym}** — SM:{sm} | KOL:{kol} | MC {mc} | Vol {vol} | Rug:{rug}{note_str}")
            parts.append(f"  {extract_ca_line(addr)}")

    return "\n".join(parts)

# ── Section 4: New Tokens & Cross-Chain Clusters ────────────────────────────

def build_new_tokens_section():
    """Cross-chain cluster detection from hot-searches, plus fresh-token notes."""
    parts = ["## 4️⃣ 新币监控\n"]

    hot_data = read_json("/tmp/hot_searches.json")
    if hot_data:
        blocks = hot_data if isinstance(hot_data, list) else hot_data.get("data", [])
        sol_hot_syms, rh_hot_syms = set(), set()
        for b in blocks:
            if isinstance(b, dict):
                if b.get("chain") == "sol":
                    sol_hot_syms.update(t.get("symbol", "").upper() for t in b.get("tokens", []))
                elif b.get("chain") == "robinhood":
                    rh_hot_syms.update(t.get("symbol", "").upper() for t in b.get("tokens", []))

        cross = sol_hot_syms & rh_hot_syms
        if cross:
            parts.append(f"> 🔍 跨链集群信号: {'、'.join(sorted(cross)[:8])} 同时出现在Sol和RH热搜 — 叙事镜像中，关注是否跑出主盘\n")
        else:
            parts.append("> 当前无显著跨链集群信号\n")

    # Fresh tokens from 5m trending with SM interest
    for chain_label, file_path, max_mc, limit in [
        ("Solana", "/tmp/sol_5m.json", 100000, 3),
        ("Robinhood", "/tmp/rh_5m.json", None, 3),
    ]:
        data = read_json(file_path)
        tokens = get_rank(data)
        fresh = [
            t for t in tokens
            if t.get("smart_degen_count", 0) and t.get("smart_degen_count", 0) >= 1
            and (max_mc is None or (t.get("market_cap", 0) and float(t.get("market_cap", 0)) < max_mc))
        ]
        if fresh:
            parts.append(f"\n**{chain_label} — 新关注度代币 (SM≥1)**")
            for t in fresh[:limit]:
                sym, addr = t.get("symbol", "?"), t.get("address", "?")
                mc = fmt_mc(t.get("market_cap", 0))
                sm = t.get("smart_degen_count", 0)
                rug = t.get("rug_ratio", 0)
                ct = t.get("creator_token_status", "")
                parts.append(f"- **${sym}** | MC {mc} | SM:{sm} | Rug:{rug} | 创建者:{ct}")
                parts.append(f"  {extract_ca_line(addr)}")

    return "\n".join(parts)

# ── Section 5: Risk Warnings ────────────────────────────────────────────────

def build_risk_section():
    """Scan all trending data for risk flags."""
    parts = ["## 5️⃣ 风险提示\n"]
    warnings = []

    for chain_label, file_path in [
        ("Sol", "/tmp/sol_5m.json"),
        ("Sol(1h)", "/tmp/sol_1h.json"),
        ("RH", "/tmp/rh_5m.json"),
    ]:
        tokens = get_rank(read_json(file_path))
        for t in tokens:
            sym = t.get("symbol", "?")
            rug = t.get("rug_ratio", 0)
            top10 = t.get("top_10_holder_rate", 0)
            wash = t.get("is_wash_trading", False)
            bundler = t.get("bundler_rate", 0)
            if wash is True:
                warnings.append(f"🔴 Wash Trading: **${sym}** ({chain_label}) — 虚假交易量检测到")
            if rug is not None and rug > RECKLESS_RUG_THRESHOLD:
                warnings.append(f"🚫 极高Rug风险: **${sym}** ({chain_label}) — Rug={rug:.2f}，建议直接忽略")
            elif rug is not None and rug > RISK_RUG_THRESHOLD:
                warnings.append(f"⚠️ 高Rug风险: **${sym}** ({chain_label}) — Rug={rug:.2f}")
            if top10 is not None and top10 > RISK_TOP10_THRESHOLD:
                warnings.append(f"⚠️ 筹码集中: **${sym}** ({chain_label}) — Top10持有{top10*100:.0f}%")
            if bundler is not None and bundler > 0.4:
                warnings.append(f"⚠️ Bundler率偏高: **${sym}** ({chain_label}) — {bundler:.0%}")

    # Deduplicate warnings per token
    seen_tokens = set()
    deduped = []
    for w in warnings:
        key = w.split(":")[0] + w.split("**")[1] if "**" in w else w[:30]
        if key not in seen_tokens:
            seen_tokens.add(key)
            deduped.append(w)

    if deduped:
        parts.append("\n".join(deduped[:8]))
        parts.append(f"\n> 共检测到 {len(deduped)} 条风险提示，以上为前8条")
    else:
        parts.append("当前未检测到明显风险信号\n")

    return "\n".join(parts)

# ═══════════════════════════════════════════════════════════════════════════
# Assemble
# ═══════════════════════════════════════════════════════════════════════════

def get_narrative_summary():
    """Derive a one-line '今日核心叙事' from 1h Solana data."""
    sol_tokens = get_rank(read_json("/tmp/sol_1h.json"))
    rh_tokens = get_rank(read_json("/tmp/rh_1h.json"))
    narr = detect_narratives(sol_tokens)
    # Pick the most prominent narrative
    if narr:
        main_narr = narr[0].split(":")[0] if ":" in narr[0] else narr[0]
    else:
        main_narr = "无明显主导叙事"

    # Check FNG
    fng = read_json("/tmp/fng.json")
    fng_note = ""
    if fng and fng.get("data"):
        fng_score = fng["data"][0].get("value", "?")
        fng_label = fng["data"][0].get("value_classification", "?")
        fng_note = f" | 恐惧贪婪:{fng_score}({fng_label})"
    return f"**今日核心叙事：** {main_narr}{fng_note}"

def main():
    now = REPORT_DATE if REPORT_DATE else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = [
        f"📊 **链上综合日报 | {now}**",
        "",
        build_market_section(),
        "",
        build_hotspots_section(),
        "",
        build_smart_money_section(),
        "",
        build_new_tokens_section(),
        "",
        build_risk_section(),
        "",
        get_narrative_summary(),
    ]
    print("\n".join(sections))

if __name__ == "__main__":
    main()
