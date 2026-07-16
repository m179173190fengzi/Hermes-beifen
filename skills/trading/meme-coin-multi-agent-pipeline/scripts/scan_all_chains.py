#!/usr/bin/env python3
"""
scan_all_chains.py — 链上打狗全自动扫描脚本

在 cron job 中直接执行，无需加载 LLM 技能。
内置：扫链 -> 6类过滤器 -> 评分 -> 输出 Telegram 格式报告。

使用方式（cron no_agent 模式）：
  cronjob action=create \\
    name='链上打狗多链扫描' \\
    schedule='0 6,8,10,12,14,16,18,20,22 * * *' \\
    script='~/.hermes/skills/trading/meme-coin-multi-agent-pipeline/scripts/scan_all_chains.py' \\
    no_agent=true

Manual: python3 ~/.hermes/skills/trading/meme-coin-multi-agent-pipeline/scripts/scan_all_chains.py

Requirements: gmgn-cli, GMGN_API_KEY configured.
"""
import sys, json, re, subprocess, os

KEYWORDS = {
    'chain_founder': [
        'cz','zhao','binance','vlad','tenev','hood','robinhood',
        'anatoly','sol','solana','vitalik','eth','ethereum',
        'jesse','base','coinbase','brian','he yi','heyibinance'
    ],
    'kol': [
        'ansem','murad','cobie','hsaka','pentoshi',
        'mooncarl','ashcrypto','blknoiz','doveywan',
        'kris','0xngmi','punk','pete','capo','lord','cryptocapo'
    ],
    'tech': [
        'elon','musk','altman','sama','satoshi',
        'jensen','nvidia','saylor','mstr','billgates','bezos','zuck'
    ],
    'political': [
        'trump','maga','biden','putin','xi','milei',
        'fed','powell','election','kamala','harris'
    ],
    'event': [
        'halving','etf','sec','war','space','superbowl','olympic','worldcup'
    ],
    'institution': [
        'a16z','paradigm','blackrock','wintermute','dwf',
        'microstrategy','vanguard','fidelity','grayscale'
    ]
}

CAT_CN = {
    'chain_founder': '链创始人', 'kol': 'KOL大V', 'tech': '科技领袖',
    'political': '政治人物', 'event': '社会事件', 'institution': '知名机构'
}

CHAIN_CONFIG = [
    ('Solana', 'sol', '6h'),
    ('BSC', 'bsc', '6h'),
    ('Robinhood', 'robinhood', '6h'),
]


def scan_chain(chain, interval='6h', limit=20):
    cmd = ['gmgn-cli', 'market', 'trending', '--chain', chain, '--interval', interval, '--limit', str(limit), '--raw']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if r.returncode != 0:
            return None, f"gmgn-cli failed: {r.stderr[:200]}"
        d = json.loads(r.stdout)
        return d.get('data', {}).get('rank', []), None
    except subprocess.TimeoutExpired:
        return None, "gmgn-cli timeout (25s)"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def matches(sym, name):
    sym = sym.lower()
    name = name.lower()
    cats = []
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            kwl = kw.lower()
            if sym.startswith(kwl):
                cats.append(cat); break
            if re.search(r'(?:^|[\s\-_/])' + re.escape(kwl) + r'(?:$|[\s\-_/])', sym):
                cats.append(cat); break
            if re.search(r'\b' + re.escape(kwl) + r'\b', name):
                cats.append(cat); break
    return list(set(cats))


def score_token(t, chain='sol'):
    cr = t.get('creator_token_status', '')
    sm = int(t.get('smart_degen_count', 0))
    top10 = float(t.get('top_10_holder_rate', 0))
    bot = float(t.get('bot_degen_rate', 0))
    liq = float(t.get('liquidity', 0))
    lock = float(t.get('lock_percent', 0) or 0)
    s = 0
    if chain == 'robinhood':
        s += 5  # RH链 creator_close 普遍状态，降权
    elif cr == 'creator_close':
        s += 15
    elif cr == 'creator_hold':
        s += 5
    s += 10 if sm >= 15 else (5 if sm >= 5 else 0)
    s += 15 if top10 < 0.2 else (8 if top10 < 0.4 else 0)
    s += 15 if bot < 0.2 else (8 if bot < 0.4 else 0)
    s += 10 if liq >= 50000 else (5 if liq >= 20000 else 0)
    s += 10 if lock >= 0.8 else (5 if lock >= 0.5 else 0)
    return s


def fmt_token(t, cats, rank, chain='sol'):
    sym, name = t.get('symbol', '?'), t.get('name', '?')
    mc = float(t.get('market_cap', 0))
    sm = int(t.get('smart_degen_count', 0))
    vol = float(t.get('volume', 0))
    top10 = float(t.get('top_10_holder_rate', 0))
    buys, sells = int(t.get('buys', 0)), int(t.get('sells', 0))
    holders = int(t.get('holder_count', 0))
    cr = t.get('creator_token_status', '')
    twt = (t.get('twitter_username', '') or '').replace('https://x.com/','').replace('https://twitter.com/','').replace('@','')
    bundler = float(t.get('bundler_rate', 0))
    bot = float(t.get('bot_degen_rate', 0))
    liq = float(t.get('liquidity', 0))
    addr = t.get('address', '?')
    score = score_token(t, chain)
    ch1h = float(t.get('price_change_percent1h', 0))

    tag_names = [CAT_CN.get(c, c) for c in cats]
    emoji_map = {'chain_founder': '🔗', 'kol': '📣', 'tech': '🔬',
                 'political': '🏛️', 'event': '🌐', 'institution': '🏢'}
    tags = ' | '.join([f"{emoji_map.get(c, '')}{n}" for c, n in zip(cats, tag_names)])
    rating = '⭐ 重点' if score >= 65 else ('👀 关注' if score >= 50 else '🔍 观察')

    ca_short = f"{addr[:8]}...{addr[-6:]}"
    return (f"\n**#{rank} ${sym}** ({name})  {rating}\n"
            f"🏷️ {tags}\n"
            f"💵 MC `${mc:,.0f}` | 评分 **{score}/75** | Vol `${vol:,.0f}`\n"
            f"👥 聪明钱{sm} | 持币{holders} | Top10 {top10:.1%}\n"
            f"📈 1h: {ch1h:+.1f}% | Bundle {bundler:.1%} | 机器率 {bot:.1%}\n"
            f"🔒 创建者: {'已撤池✅' if cr == 'creator_close' else '在池⚠️'} | 流动性 `${liq:,.0f}`\n"
            f"📝 `{ca_short}`"), score


def analyze_chain(chain_name, chain, interval='6h'):
    tokens, err = scan_chain(chain, interval)
    if err:
        return f"\n**{chain_name}** — ❌ 扫描失败: {err}\n", 0, 0
    matched = []
    for t in tokens:
        sym, name = t.get('symbol', ''), t.get('name', '')
        mc = float(t.get('market_cap', 0))
        if mc < 10000: continue
        if any(w in sym.lower() for w in ['scam', 'rug', 'fake']): continue
        cats = matches(sym, name)
        if cats: matched.append((t, cats))
    matched.sort(key=lambda x: score_token(x[0], chain), reverse=True)
    lines = [f"\n━━━ **{chain_name}** ({len(tokens)}个) ━━━"]
    if not matched:
        lines.append('\n⛔ 无匹配6类别的代币')
    else:
        for i, (t, cats) in enumerate(matched, 1):
            f, _ = fmt_token(t, cats, i, chain)
            lines.append(f)
    lines.append(f"\n⛔ 过滤 {len(tokens)-len(matched)} 个垃圾meme")
    return '\n'.join(lines), len(matched), len(tokens) - len(matched)


def main():
    import time
    now = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() + 28800))
    report = [f"🔍 **链上打狗扫描报告**\n━━━━━━━━━━━━━━━━━━━━━━\n⏰ {now}"]
    tm, tf = 0, 0
    for cn, c, iv in CHAIN_CONFIG:
        s, m, f = analyze_chain(cn, c, iv)
        report.append(s); tm += m; tf += f
    report.append(f"\n📊 **合计**: 匹配 {tm} | 过滤 {tf} 个垃圾meme")
    print('\n'.join(report))


if __name__ == '__main__':
    main()
