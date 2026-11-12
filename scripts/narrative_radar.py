#!/usr/bin/env python3
"""
narrative_radar.py — 叙事扩散计数器（零 LLM 成本）

原理：同一叙事在「几个独立来源」出现 = 扩散强度。
    1 个源  = 单一 KOL 喊单
    2-3 个源 = 开始扩散
    4+ 个源 = 已被市场确认

数据源（全部免费，无需 API key）：
  · RSS：The Block / Cointelegraph / Decrypt / Blockworks / CryptoSlate / CoinDesk
  · GDELT：全球新闻库关键词检索
  · Telegram：公开频道网页预览 (t.me/s/<channel>)

用法：
  python3 narrative_radar.py                    # 最近 24h
  python3 narrative_radar.py --hours 6          # 最近 6h
  python3 narrative_radar.py --md out.md        # 存 Markdown
  python3 narrative_radar.py --json out.json    # 存原始数据
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or ""
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

RSS_FEEDS = [
    ("theblock",    "https://www.theblock.co/rss.xml"),
    ("cointelegraph", "https://cointelegraph.com/rss"),
    ("decrypt",     "https://decrypt.co/feed"),
    ("blockworks",  "https://blockworks.co/feed"),
    ("cryptoslate", "https://cryptoslate.com/feed/"),
    ("coindesk",    "https://www.coindesk.com/arc/outboundfeeds/rss/"),
]

# Google News 关键词检索（免费 RSS）
GNEWS_QUERIES = [
    "meme coin",
    "solana ecosystem",
    "bnb chain",
    "ai agent crypto",
]

TELEGRAM_CHANNELS = [
    "binance_announcements",
    "cointelegraph",
    "solana",
]

# ── 叙事词典：同一概念的多种说法归并 ─────────────────────────
NARRATIVES = {
    "AI Agent":       ["ai agent", "agentic", "autonomous agent", "ai16z", "eliza", "ai agents"],
    "Meme 币":        ["meme coin", "memecoin", "meme token", "shitcoin", "meme币"],
    "Solana 生态":    ["solana", "sol ", "spl token", "jupiter", "raydium", "pump.fun", "pumpfun"],
    "BSC 生态":       ["bsc", "bnb chain", "binance smart chain", "pancakeswap", "four.meme", "flap"],
    "RWA 代币化":     ["rwa", "real world asset", "tokenized treasur", "tokenization"],
    "Perp DEX":       ["perp dex", "perpetual dex", "hyperliquid", "dydx", "gmx"],
    "Layer2":         ["layer 2", "layer2", "rollup", "arbitrum", "optimism", "base chain"],
    "DeFi 复苏":      ["defi", "lending protocol", "yield", "tvl"],
    "ETF/机构":       ["etf", "blackrock", "institutional", "treasury", "microstrategy"],
    "监管":           ["sec ", "regulation", "lawsuit", "settlement", "crackdown", "ban "],
    "稳定币":         ["stablecoin", "usdt", "usdc", "depeg"],
    "空投/积分":      ["airdrop", "points program", "quest", "incentive program"],
    "MCP/AI 基建":    ["mcp", "model context protocol", "llm", "inference"],
}

# 链/生态标签（单独统计，不参与叙事打分）
CHAIN_TAGS = {
    "SOL": ["solana", "sol "],
    "BSC": ["bsc", "bnb", "binance smart chain"],
    "BASE": ["base chain", "base network", "coinbase base"],
    "ETH": ["ethereum", "eth "],
    "RH": ["robinhood chain", "robinhood"],
}


def fetch(url: str, timeout: int = 20) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    handlers = []
    if PROXY:
        handlers.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def parse_date(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:len(fmt) + 6], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def strip_html(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", t or "")
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    return " ".join(t.split())


def parse_feed(raw: bytes, source: str) -> list[dict]:
    out: list[dict] = []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return out
    items = root.iter("item")
    tag = "item"
    if root.tag.endswith("feed"):  # Atom
        items = root.iter("{http://www.w3.org/2005/Atom}entry")
        tag = "atom"
    for it in items:
        def g(*names):
            for n in names:
                el = it.find(n)
                if el is not None and (el.text or "").strip():
                    return (el.text or "").strip()
            return ""
        if tag == "atom":
            title = g("{http://www.w3.org/2005/Atom}title")
            link_el = it.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
            date = g("{http://www.w3.org/2005/Atom}updated", "{http://www.w3.org/2005/Atom}published")
            desc = g("{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content")
        else:
            title = g("title")
            link = g("link")
            date = g("pubDate", "{http://purl.org/dc/elements/1.1/}date")
            desc = g("description", "{http://purl.org/rss/1.0/modules/content/}encoded")
            # Google News 的 <source> 是原始媒体名，用它当域名，否则一条通稿的多家转载
            # 会被算成同一个「来源」，独立事件数就失去意义。
            src_el = it.find("source")
            if src_el is not None and (src_el.text or "").strip():
                outlet = (src_el.text or "").strip()
                host = ""
                if src_el.get("url"):
                    host = urllib.parse.urlparse(src_el.get("url", "")).netloc
                source = f"newswire:{host or outlet}"
                # Google News 标题尾部带 " - 媒体名"，会把媒体名里的 crypto 字样
                # 混进正文匹配，先把后缀剥掉。
                title = re.sub(r"\s+-\s+[^-]{2,45}$", "", title)
        if not title:
            continue
        out.append({
            "source": source, "title": strip_html(title), "link": link,
            "text": (strip_html(title) + " " + strip_html(desc))[:1200],
            "dt": parse_date(date),
        })
    return out


def parse_gdelt(query: str, hours: int) -> list[dict]:
    q = urllib.parse.quote(f'"{query}"')
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}"
           f"&mode=artlist&maxrecords=60&timespan={hours}h&format=json&sort=datedesc")
    raw = fetch(url, timeout=25)
    if not raw:
        return []
    try:
        data = json.loads(raw.decode("utf-8", "ignore"))
    except Exception:
        return []
    out = []
    for a in (data.get("articles") or []):
        title = (a.get("title") or "").strip()
        if not title:
            continue
        dt = None
        sd = a.get("seendate") or ""
        if len(sd) >= 15:
            try:
                dt = datetime.strptime(sd[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            except Exception:
                dt = None
        out.append({
            "source": "gdelt:" + (a.get("domain") or "?"),
            "title": title, "link": a.get("url", ""),
            "text": title, "dt": dt,
        })
    return out


def parse_telegram(channel: str) -> list[dict]:
    raw = fetch(f"https://t.me/s/{channel}", timeout=20)
    if not raw:
        return []
    html = raw.decode("utf-8", "ignore")
    out = []
    for m in re.finditer(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', html, re.S
    ):
        txt = strip_html(m.group(1))
        if len(txt) < 40:
            continue
        out.append({
            "source": f"tg:{channel}", "title": txt[:120], "link": f"https://t.me/{channel}",
            "text": txt[:1200], "dt": datetime.now(timezone.utc),
        })
    return out


def collect(hours: int, quiet: bool = False) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items: list[dict] = []

    def say(msg: str) -> None:
        if not quiet:
            print(msg, file=sys.stderr)

    for name, url in RSS_FEEDS:
        raw = fetch(url)
        got = parse_feed(raw, name) if raw else []
        items.extend(got)
        say(f"  {name:<14} {len(got):>3} 条")

    for q in GNEWS_QUERIES:
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
               + "&hl=en-US&gl=US&ceid=US:en")
        raw = fetch(url)
        got = parse_feed(raw, f"gnews:{q}") if raw else []
        items.extend(got)
        say(f"  gnews:{q:<14} {len(got):>3} 条")

    for q in ("meme coin", "solana", "bnb chain"):
        got = parse_gdelt(q, hours)
        items.extend(got)
        say(f"  gdelt:{q:<12} {len(got):>3} 条")

    for ch in TELEGRAM_CHANNELS:
        got = parse_telegram(ch)
        items.extend(got)
        say(f"  tg:{ch:<16} {len(got):>3} 条")

    # 时间过滤 + 去重（同一标题只留一份）
    seen = set()
    kept = []
    for it in items:
        if it["dt"] and it["dt"] < cutoff:
            continue
        key = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", it["title"].lower())[:80]
        if not key or key in seen:
            continue
        seen.add(key)
        kept.append(it)
    return kept


PROMO_RE = re.compile(
    r"\b(referral|affiliate|earn up to|launchpool|trading competition|leaderboard|"
    r"invite friends|dual-star|yield arena|giveaway|bonus|airdrop campaign|"
    r"will support .* stock split|dual investment|price today|price prediction|"
    r"how to buy|here.s what happened in crypto today|top .* to watch)\b", re.I)

STOP = set("the a an and or of to in on for with at by from as is are was were be been "
           "this that these those it its into over after before about new says say said "
           "report reports will has have had not you your we our they their".split())


def title_tokens(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{3,}", (t or "").lower()) if w not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def collapse(items: list[dict]) -> list[dict]:
    """把「同一篇稿被多家转载」折叠成一个独立事件，同时记录转载域名数。

    没有这一步，Google News 上一次通稿会让「独立来源数」虚高 5-10 倍。
    """
    clusters: list[dict] = []
    for it in items:
        toks = title_tokens(it["title"])
        for c in clusters:
            if jaccard(toks, c["tokens"]) >= 0.55:
                c["domains"].add(it["source"])
                c["items"].append(it)
                break
        else:
            clusters.append({"rep": it, "tokens": toks,
                             "domains": {it["source"]}, "items": [it]})
    return clusters


GENERIC_NARRATIVES = {"AI Agent", "监管", "DeFi 复苏", "Layer2", "MCP/AI 基建", "ETF/机构"}

CRYPTO_HINT = (
    "crypto", "token", "coin", "chain", "defi", "web3", "blockchain", "solana", "bsc",
    "binance", "ethereum", "wallet", "onchain", "on-chain", "meme", "nft", "stablecoin",
    "dex", "airdrop", "bitcoin", "btc", "eth", "altcoin", "hyperliquid", "uniswap",
    "perpetual", "validator", "staking", "liquidity", "protocol",
)


def score(items: list[dict], min_events: int) -> list[dict]:
    """按「独立事件数」而非「条目数」计分：标题命中才算，正文提及不算。"""
    clean = [it for it in items if not PROMO_RE.search(it["title"])]
    clusters = collapse(clean)
    results = []
    for name, kws in NARRATIVES.items():
        hit = []
        for c in clusters:
            title = c["rep"]["title"].lower()
            if not any(k in title for k in kws):
                continue
            # 泛化叙事（AI Agent / 监管 / DeFi）必须带加密上下文，
            # 否则「美联航禁止第三方 AI 代理订票」这种新闻会被算成 crypto 叙事。
            if name in GENERIC_NARRATIVES and not any(h in title for h in CRYPTO_HINT):
                continue
            hit.append(c)
        if len(hit) < min_events:
            continue
        domains = set()
        for c in hit:
            domains |= c["domains"]
        blob = " ".join(c["rep"]["title"].lower() for c in hit)
        chains = [tag for tag, keys in CHAIN_TAGS.items() if any(k in blob for k in keys)]
        dated = [c["rep"]["dt"] for c in hit if c["rep"]["dt"]]
        results.append({
            "narrative": name,
            "events": len(hit),
            "domains": len(domains),
            "syndicated": sum(len(c["items"]) for c in hit),
            "chains": chains,
            "newest": max(dated).isoformat() if dated else None,
            "sources": sorted(domains)[:12],
            "headlines": [c["rep"]["title"][:120] for c in
                          sorted(hit, key=lambda c: c["rep"]["dt"] or
                                 datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:4]],
        })
    results.sort(key=lambda r: (r["events"], r["domains"]), reverse=True)
    return results


def brief_lines(results: list[dict], total: int, hours: int) -> list[str]:
    """--brief：固定 3 行（最强叙事 / 链 / 一句话读数），全部规则判定，不调模型。"""
    if not results:
        return [
            f"最强叙事  无（{hours}h 内没有多源共振，{total} 条素材）",
            "链        -",
            "读数     没有叙事在扩散，别硬找机会",
        ]

    top = results[0]
    events = {r["narrative"]: r["events"] for r in results}

    line1 = (f"最强叙事  {top['narrative']} · {top['events']} 事件 / "
             f"{top['domains']} 域名")

    chain_counts = Counter()
    for r in results:
        for c in r["chains"]:
            chain_counts[c] += 1
    chains = " ".join(f"{c}×{n}" for c, n in chain_counts.most_common(3))
    line2 = "链        " + (chains or "无明确链条指向")

    # ── 读数规则（按优先级叠加，最多两条）──────────────────
    parts = []
    if events.get("稳定币", 0) >= 4:
        parts.append("稳定币在收缩（链上子弹变少）")
    if events.get("Meme 币", 0) >= 7 and top["narrative"] != "Meme 币":
        parts.append("meme 已是共识区")
    n = top["events"]
    if n >= 7:
        parts.append("全市场共识 = 派发段，别追")
    elif n >= 4:
        parts.append("已被确认，可按叙事布局")
    elif n >= 2:
        parts.append("刚扩散，等 24h 确认再动")
    if not parts:
        parts.append("信号弱，观察")
    line3 = "读数     " + "；".join(parts[:2])

    return [line1, line2, line3]


def render_md(results: list[dict], total: int, hours: int) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# 叙事扩散计数 · 最近 {hours}h", "",
             f"去重后 {total} 条 | 生成 {now}", "",
             "**判定标准：独立事件数**（同一稿件被 N 家转载只算 1 件，转载家数单列）", ""]
    if not results:
        lines.append("**无叙事达到门槛**（当前没有多源共振的话题）")
        return "\n".join(lines)
    lines += ["| 叙事 | 独立事件 | 涉及域名 | 转载量 | 链 | 最新标题 |",
              "|---|---|---|---|---|---|"]
    for r in results:
        bar = "🟢" if r["events"] >= 3 else ("🟡" if r["events"] >= 2 else "⚪")
        title = (r["headlines"][0] if r["headlines"] else "")[:56].replace("|", "/")
        lines.append(f"| {bar} **{r['narrative']}** | {r['events']} | {r['domains']} | "
                     f"{r['syndicated']} | {','.join(r['chains']) or '-'} | {title} |")
    lines += ["", "---", ""]
    for r in results:
        if r["events"] < 2:
            continue
        lines.append(f"### {r['narrative']} — {r['events']} 个独立事件 / {r['domains']} 个域名")
        for h in r["headlines"]:
            lines.append(f"- {h}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--min-events", type=int, default=2)
    ap.add_argument("--brief", action="store_true", help="只输出 3 行：最强叙事 / 链 / 读数")
    ap.add_argument("--md", default="")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    t0 = time.time()
    if not args.brief:
        print(f"采集最近 {args.hours}h …", file=sys.stderr)
    items = collect(args.hours, quiet=args.brief)
    if not args.brief:
        print(f"\n去重后 {len(items)} 条，用时 {time.time()-t0:.1f}s\n", file=sys.stderr)

    results = score(items, args.min_events)

    if args.brief:
        print("\n".join(brief_lines(results, len(items), args.hours)))
        return 0

    md = render_md(results, len(items), args.hours)
    print(md)

    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n[已存 {args.md}]", file=sys.stderr)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"hours": args.hours, "total": len(items), "results": results,
                       "items": items}, f, ensure_ascii=False, indent=1, default=str)
        print(f"[已存 {args.json}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
