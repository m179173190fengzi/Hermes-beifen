#!/usr/bin/env python3
"""
链上打狗多链扫描自动过滤评分脚本 — 6类通用过滤器 + 评分

使用方式：
  1. gmgn-cli market trending --chain sol --interval 6h --limit 20 --raw > /tmp/sol_trending.json
  2. gmgn-cli market trending --chain bsc --interval 6h --limit 20 --raw > /tmp/bsc_trending.json
  3. gmgn-cli market trending --chain robinhood --interval 6h --limit 20 --raw > /tmp/rh_trending.json
  4. python3 scripts/filter_score_report.py

依赖：/tmp/sol_trending.json, /tmp/bsc_trending.json, /tmp/rh_trending.json
"""
import json, re
from datetime import datetime, timezone

# ─── 6大类别关键词字典 ───
CATEGORY_KEYWORDS = {
    "🔗链创始人": {
        "sol": ["sol", "anatoly", "yakovenko", "toly", "raj", "gokal"],
        "bnb,bsc,binance": ["bnb", "binance", "cz", "zhao", "changpeng"],
        "robinhood,hood": ["hood", "vlad", "tenev", "baiju", "bhatt", "rh", "robinhood"],
        "eth,ethereum": ["eth", "ethereum", "vitalik", "vbuterin", "buterin"],
        "base": ["base", "jesse", "pollak"],
        "arb,arbitrum": ["arb", "arbitrum"],
        "sui": ["sui", "adeniyi", "mysten"],
    },
    "📣KOL大V": {
        "ansem": ["ansem", "blknoiz"],
        "murad": ["murad", "mahn"],
        "cobie": ["cobie"],
        "hsaka": ["hsaka"],
        "ran": ["ran"],
        "flow": ["flow"],
        "pentoshi": ["pentoshi", "pentosh1"],
        "godjohn,cgj": ["godjohn", "cgj"],
        "bigbro,aussie": ["bigbro", "aussie"],
        "mooncarl": ["carl", "mooncarl"],
        "ashcrypto": ["ashcrypto"],
        "btcbao": ["btcbao", "bitcoinbo"],
    },
    "🔬科技领袖": {
        "elon_musk": ["elon", "musk", "xai", "tesla", "spacex", "doge"],
        "sam_altman": ["altman", "openai", "sama", "worldcoin", "wld"],
        "satoshi": ["satoshi", "nakamoto"],
        "cz": ["cz", "zhao", "binance"],
        "jensen": ["jensen", "nvidia"],
        "zuck": ["zuck", "meta"],
        "bezos": ["bezos", "amazon"],
        "tim_cook": ["cook", "apple"],
        "brian_armstrong": ["brian", "armstrong", "coinbase"],
        "justin_sun": ["justin", "sun", "tron"],
        "vitalik": ["vitalik"],
        "saylor": ["saylor", "microstrategy", "mstr"],
    },
    "🏛️政治人物": {
        "trump": ["trump", "donald", "maga"],
        "biden": ["biden", "joe"],
        "putin": ["putin", "russia"],
        "xi": ["xi", "china", "chinese"],
        "milei": ["milei", "argentina"],
        "modi": ["modi", "india"],
        "yoon": ["yoon", "korea"],
        "election": ["election", "vote", "president"],
        "fed": ["fed", "powell"],
    },
    "🌐社会事件": {
        "halving": ["halving"],
        "etf_sec": ["etf", "sec", "gary", "gensler"],
        "war": ["war", "ukraine", "israel", "palestine", "gaza"],
        "regulation": ["regulation", "ban"],
        "exchange_crash": ["ftx", "bankrupt", "collapse", "sbf"],
        "tech_launch": ["launch", "release"],
        "sports": ["worldcup", "superbowl", "olympic", "nba", "nfl"],
        "disaster": ["earthquake", "flood", "hurricane"],
        "space": ["spacex"],
    },
    "🏢知名机构": {
        "a16z": ["a16z"],
        "paradigm": ["paradigm"],
        "blackrock": ["blackrock"],
        "wintermute": ["wintermute"],
        "dwf": ["dwf"],
        "grayscale": ["grayscale", "gbtc"],
        "jump": ["jump"],
        "jupiter": ["jupiter"],
        "alameda": ["alameda"],
        "3ac": ["3ac", "threearrows"],
    },
}


def matches_category(symbol, name):
    """匹配6类过滤器，防假阳性（词边界匹配+符号开头匹配）"""
    matches = []
    sym_lower = symbol.lower()
    name_lower = name.lower()

    for cat, subcats in CATEGORY_KEYWORDS.items():
        for subcat, keywords in subcats.items():
            for kw in keywords:
                kw_lower = kw.lower()
                # 1. 符号开头匹配（CZBULL → cz ✓）
                if sym_lower.startswith(kw_lower):
                    matches.append((cat, subcat, kw))
                    break
                # 2. 符号独立词匹配（$VLAD → vlad ✓, $SHINYSUIT → sui ✗）
                if re.search(r'(?:^|[\s\-_/])' + re.escape(kw_lower) + r'(?:$|[\s\-_/])', sym_lower):
                    matches.append((cat, subcat, kw))
                    break
                # 3. 名称词边界匹配（"Binance bibi" → binance ✓, "astronaut" → tron ✗）
                if re.search(r'\b' + re.escape(kw_lower) + r'\b', name_lower):
                    matches.append((cat, subcat, kw))
                    break
    return matches


def exclusion_check(symbol, name, mc):
    """排除检查：欺诈词+低MC"""
    text = (symbol + " " + name).lower()
    if any(x in text for x in ["scam", "rug", "fake"]):
        return True, "⛔ 代币名含欺诈关键词"
    if mc < 10000:
        return True, "⛔ MC < $10K"
    return False, ""


def score_token(t, chain):
    """6维度加分制评分（0-75）"""
    score = 0

    # 创建者状态（在池+15，已撤池0）
    creator_close = bool(t.get('creator_close', False))
    creator_status = t.get('creator_token_status', '')
    if chain == 'robinhood':
        if creator_status == "creator_hold":
            score += 15
    else:
        if creator_close is False or creator_status == "creator_hold":
            score += 15

    # 聪明钱数量（>15个+10分）
    sm = int(t.get('smart_degen_count', 0) or 0)
    if sm > 15:      score += 10
    elif sm >= 5:    score += 5

    # 持币分散度（Top10<20%+15分）
    top10 = float(t.get('top_10_holder_rate', 1) or 1)
    if top10 < 0.2:     score += 15
    elif top10 < 0.4:   score += 10
    elif top10 < 0.6:   score += 5

    # 机器人率（<20%+15分）
    bot_rate = float(t.get('bot_degen_rate', 1) or 1)
    if bot_rate < 0.2:     score += 15
    elif bot_rate < 0.35:  score += 10
    elif bot_rate < 0.5:   score += 5

    # 流动性（>$50K+10分）
    liq = float(t.get('liquidity', 0) or 0)
    if liq > 50000:    score += 10
    elif liq > 20000:  score += 5

    # 锁仓率（>80%+10分）
    lock_pct = float(t.get('lock_percent', 0) or 0)
    if lock_pct >= 0.8: score += 10
    elif lock_pct >= 0.5: score += 5

    return min(score, 75), 75


def narrative_text(symbol, name, categories):
    """生成叙事描述"""
    cat_labels = [c[0] for c in categories]
    kw_hits = [c[2] for c in categories]

    if "CZ" in symbol.upper() or "binance" in name.lower():
        if "bull" in name.lower():
            return "CZ/赵长鹏公牛系列Meme — Binance创始人主题社区币"
        return "CZ/赵长鹏主题Meme — Binance创始人的社区叙事"
    if any(k in ("vlad", "tenev") for k in kw_hits) or "robinhood" in name.lower():
        return "Vlad Tenev (Robinhood CEO) 相关Meme — Robinhood链原生叙事"
    if "ansem" in symbol.lower():
        if "bull" in name.lower():
            return "Ansem (Solana圣经KOL) 主题Meme — 黑公牛叙事，Solana社区标志性KOL"
        return "Ansem主题Meme币 — Solana KOL社区文化币"
    if "heyi" in symbol.lower():
        return "合意 (HEYI) — CZ提出的BNB Chain合意概念，Binance生态叙事"
    if "wallet" in symbol.lower():
        return "Robinhood Wallet官方生态代币概念 — Robinhood链基础设施叙事"

    if "🔗链创始人" in cat_labels:
        return f"链创始人({','.join(kw_hits)})相关Meme — 链原生文化社区币"
    if "📣KOL大V" in cat_labels:
        return f"KOL {','.join(kw_hits)} 喊单相关的Meme币 — 大V叙事驱动"
    if "🔬科技领袖" in cat_labels:
        return f"科技领袖({','.join(kw_hits)})主题Meme — 科技叙事币"
    if "🏛️政治人物" in cat_labels:
        return "政治人物主题Meme币 — 时事热点驱动"
    if "🌐社会事件" in cat_labels:
        return "重大社会事件主题Meme币 — 事件驱动型叙事"
    if "🏢知名机构" in cat_labels:
        return "知名机构概念Meme币 — 机构背书叙事"
    return "社区驱动型Meme币"


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    chains_data = [
        ("Solana", "/tmp/sol_trending.json"),
        ("BSC", "/tmp/bsc_trending.json"),
        ("Robinhood", "/tmp/rh_trending.json"),
    ]

    all_passed = []
    all_filtered = {}

    for chain_label, path in chains_data:
        try:
            tokens = json.load(open(path))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            all_passed.append((chain_label, []))
            all_filtered[chain_label] = 0
            continue

        chain_key = chain_label.lower()
        passed = []
        filtered_count = 0

        for t in tokens:
            symbol = t.get('symbol', '?')
            name = t.get('name', '?')
            mc = float(t.get('market_cap', 0) or 0)
            categories = matches_category(symbol, name)
            should_filter, _ = exclusion_check(symbol, name, mc)

            if should_filter or not categories:
                filtered_count += 1
                continue

            raw_score, max_raw = score_token(t, chain_key)
            is_satirical = "scam" in symbol.lower() or "fake" in name.lower()

            passed.append({
                "symbol": symbol, "name": name, "address": t.get('address', ''),
                "mc": mc, "liq": float(t.get('liquidity', 0) or 0),
                "sm": int(t.get('smart_degen_count', 0) or 0),
                "holders": int(t.get('holder_count', 0) or 0),
                "ch1h": float(t.get('price_change_percent1h', 0) or 0),
                "creator_close": bool(t.get('creator_close', False)),
                "creator_status": t.get('creator_token_status', ''),
                "top10": float(t.get('top_10_holder_rate', 1) or 1),
                "bot_rate": float(t.get('bot_degen_rate', 1) or 1),
                "bundler": float(t.get('bundler_rate', 0) or 0),
                "lock_pct": float(t.get('lock_percent', 0) or 0),
                "renounced": bool(t.get('renounced_mint', False)),
                "swaps": int(t.get('swaps', 0) or 0),
                "buys": int(t.get('buys', 0) or 0),
                "sells": int(t.get('sells', 0) or 0),
                "twitter": t.get('twitter_username', '') or '',
                "categories": categories, "score": raw_score, "is_satirical": is_satirical,
                "narrative": narrative_text(symbol, name, categories),
            })

        passed.sort(key=lambda x: x['score'], reverse=True)
        all_passed.append((chain_label, passed))
        all_filtered[chain_label] = filtered_count

    # ─── 输出报告 ───
    print("🔍 链上打狗扫描报告")
    print("━━━━━━━━━━━━━━━━━━━━━━")
    print(f"⏰ {now}\n")

    for chain_label, tokens in all_passed:
        print(f"━━━ {chain_label} ━━━")
        if not tokens:
            print("  (无匹配的代币)\n")
            continue
        for i, t in enumerate(tokens, 1):
            cat_set = {}
            for cat, _, kw in t['categories']:
                cat_set.setdefault(cat, []).append(kw)
            cat_str = " | ".join(cat_set.keys())
            creator_str = "在池✅" if (not t['creator_close'] or t['creator_status'] == "creator_hold") else "已撤池⚠️"
            lock_str = f"锁仓{t['lock_pct']*100:.0f}%" if t['lock_pct'] > 0 else "未锁仓"
            renounced_str = "放弃铸币✅" if t['renounced'] else ""
            twitter_str = f"x.com/{t['twitter'].split('/')[-1]}" if t['twitter'] else "无推特"
            satirical_note = " ⚠️讽刺/恶搞类" if t['is_satirical'] else ""

            print(f"#{i} **${t['symbol']}** ({t['name']}){satirical_note}")
            print(f"📋 叙事: {t['narrative']}")
            print(f"🏷️ 类别: {cat_str}")
            print(f"💵 MC: ${t['mc']:,.0f} | 评分: {t['score']}/75")
            print(f"👥 持币{t['holders']:,} | 聪明钱{t['sm']} | 机器率{t['bot_rate']*100:.1f}% | Bundle{t['bundler']*100:.0f}%")
            print(f"📈 1h: {t['ch1h']:+.1f}% | 创建者: {creator_str} | {lock_str} | {renounced_str}")
            print(f"💱 买/卖: {t['buys']:,}/{t['sells']:,} | 交易{t['swaps']:,}笔")
            print(f"🐦 推特: {twitter_str}")
            print(f"💡 价值: {t['narrative']} — 评分{t['score']}/75")
            print(f"`CA: {t['address']}`\n")

    print("━━━━━━━━━━━━━━━━━━━━━━")
    for chain_label, count in all_filtered.items():
        print(f"⛔ {chain_label}: 过滤了{count}个垃圾meme")
    print()

    total_passed = sum(len(t) for _, t in all_passed)
    print("━━━ 市场概况 ━━━")
    print(f"三链共{total_passed}个代币通过6类过滤器进入评分")
    for chain_label, tokens in all_passed:
        if tokens:
            high = max(t['score'] for t in tokens)
            print(f"  {chain_label}: {len(tokens)}个代币，最高分{high}/75")
    print("\n📊 数据来源: GMGN Trending 6h | 评分系统: 6维度加分制(0-75分)")


if __name__ == "__main__":
    main()
