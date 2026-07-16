#!/usr/bin/env python3
"""
链上打狗全自动扫描+6类过滤+评分 — 一键脚本（内置gmgn-cli调用）

无需预先准备JSON文件，直接跑即可扫三链+过滤+评分+输出报告。
适用于手动调用和 cron no_agent=true 模式。

使用方式:
  python3 scripts/scan_and_filter.py

输出: stdout（cron no_agent模式自动推送给用户）
"""
import sys, json, re, subprocess, time

# ─── 6大类别关键词 ───
KEYWORDS = {
    'chain_founder': ['cz','zhao','binance','vlad','tenev','hood','robinhood',
                      'anatoly','sol','solana','vitalik','eth','ethereum',
                      'jesse','base','coinbase','brian'],
    'kol': ['ansem','murad','cobie','hsaka','pentoshi','mooncarl',
            'ashcrypto','blknoiz','doveywan'],
    'tech': ['elon','musk','altman','sama','satoshi','jensen','nvidia',
             'saylor','mstr'],
    'political': ['trump','maga','biden','putin','xi','milei','fed','powell'],
    'event': ['halving','etf','sec','war','space','superbowl','olympic'],
    'institution': ['a16z','paradigm','blackrock','wintermute','dwf',
                    'microstrategy','vanguard','fidelity','grayscale']
}

CAT_EMOJI = {'chain_founder':'🔗','kol':'📣','tech':'🔬',
             'political':'🏛️','event':'🌐','institution':'🏢'}
CAT_CN = {'chain_founder':'链创始人','kol':'KOL大V','tech':'科技领袖',
          'political':'政治人物','event':'社会事件','institution':'知名机构'}


def scan_chain(chain, interval='6h', limit=20):
    """调用gmgn-cli扫链"""
    cmd = ['gmgn-cli', 'market', 'trending', '--chain', chain,
           '--interval', interval, '--limit', str(limit), '--raw']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return None, f"error: {r.stderr[:100]}"
    try:
        d = json.loads(r.stdout)
        return d.get('data', {}).get('rank', []), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def matches(sym, name):
    """6类过滤器（防假阳性：词边界+开头匹配）"""
    sym, name = sym.lower(), name.lower()
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


def score_token(t):
    """6维度加分制评分 0-75"""
    s = 0
    cr = t.get('creator_token_status','')
    sm = int(t.get('smart_degen_count',0) or 0)
    top10 = float(t.get('top_10_holder_rate',1) or 1)
    bot = float(t.get('bot_degen_rate',1) or 1)
    liq = float(t.get('liquidity',0) or 0)
    lock = float(t.get('lock_percent',0) or 0)
    if cr == 'creator_close': s += 15
    if sm >= 15: s += 10
    elif sm >= 5: s += 5
    if top10 < 0.2: s += 15
    elif top10 < 0.4: s += 8
    if bot < 0.2: s += 15
    elif bot < 0.35: s += 8
    if liq >= 50000: s += 10
    elif liq >= 20000: s += 5
    if lock >= 0.8: s += 10
    elif lock >= 0.5: s += 5
    return min(s, 75)


def format_token(t, cats, rank):
    sym = t.get('symbol','?')
    name = t.get('name','?')
    mc = float(t.get('market_cap',0))
    sm = int(t.get('smart_degen_count',0) or 0)
    vol = float(t.get('volume',0))
    top10 = float(t.get('top_10_holder_rate',0) or 0)
    b = int(t.get('buys',0))
    s = int(t.get('sells',0))
    h = int(t.get('holder_count',0) or 0)
    cr = t.get('creator_token_status','')
    twt = (t.get('twitter_username','') or '').strip()
    bundler = float(t.get('bundler_rate',0) or 0)
    bot = float(t.get('bot_degen_rate',0) or 0)
    liq = float(t.get('liquidity',0) or 0)
    addr = t.get('address','?')
    sc = score_token(t)
    tag_str = '|'.join(f"{CAT_EMOJI.get(c,'')}{CAT_CN.get(c,c)}" for c in cats)
    creator_str = '已撤池✅' if cr == 'creator_close' else '在池⚠️'
    twt_str = ''
    if twt:
        twt_clean = twt.replace('https://x.com/','').replace('https://twitter.com/','')
        twt_str = f"🐦 x.com/{twt_clean[:50]}"

    return (f"\n**#{rank} ${sym}** ({name})\n"
            f"🏷️ {tag_str}\n"
            f"💵 MC `${mc:,.0f}` | 评分 **{sc}/75** | 聪明钱 {sm} | 持币 {h}\n"
            f"📊 Vol `${vol:,.0f}` | Buy/Sell {b}/{s} | Top10 {top10:.1%}\n"
            f"🔒 Bundle {bundler:.1%} | 机器率 {bot:.1%} | 流动性 `${liq:,.0f}`\n"
            f"👤 创建者: {creator_str}\n"
            + (twt_str + '\n' if twt_str else '') +
            f"📝 `{addr[:8]}...{addr[-6:]}`\n"), sc


def analyze(chain_name, chain, interval):
    tokens, err = scan_chain(chain, interval)
    if err:
        return f"━━━ {chain_name} ━━━\n❌ 扫描失败: {err}\n", 0, 0
    matched = []
    for t in tokens:
        sym = t.get('symbol','')
        name = t.get('name','')
        mc = float(t.get('market_cap',0) or 0)
        if mc < 10000: continue
        if any(w in sym.lower() for w in ['scam','rug','fake']): continue
        cats = matches(sym, name)
        if cats: matched.append((t, cats))
    matched.sort(key=lambda x: score_token(x[0]), reverse=True)
    lines = [f"━━━ {chain_name} ({len(tokens)}个代币) ━━━"]
    if not matched:
        lines.append("⛔ 无匹配6类别的代币\n")
    else:
        for i, (t, cats) in enumerate(matched, 1):
            lines.append(format_token(t, cats, i)[0])
    filtered = len(tokens) - len(matched)
    lines.append(f"⛔ 过滤了 {filtered} 个不匹配的垃圾meme\n")
    return '\n'.join(lines), len(matched), filtered


def main():
    now = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()+28800))
    out = [f"🔍 **链上打狗扫描报告**",
           "━━━━━━━━━━━━━━━━━━━━━━",
           f"⏰ {now}\n"]
    for cn, c, iv in [('Solana','sol','6h'), ('BSC','bsc','6h'), ('Robinhood','robinhood','6h')]:
        section, _, _ = analyze(cn, c, iv)
        out.append(section)
    print('\n'.join(out))


if __name__ == '__main__':
    main()
