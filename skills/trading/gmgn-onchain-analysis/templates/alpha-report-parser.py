#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alpha daily report parser/scorer — 每日Alpha合成简报 cron 的已知可用解析+评分脚本。

前置（Batch 1+2 数据抓取，全部带代理前缀，重定向到 /tmp）:
  HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 \
    gmgn-cli market trending --chain sol --interval 6h --limit 30 --raw > /tmp/alpha_sol_6h.json   # 同理 bsc/robinhood
  gmgn-cli market hot-searches --chain sol --chain bsc --chain robinhood --interval 1h --limit 20 --raw > /tmp/alpha_hot_1h.json
  gmgn-cli market trenches --chain {sol|bsc|robinhood} --type new_creation \
    --min-marketcap 1000000 --max-created 1440m --sort-by usd_market_cap --limit 20 --raw > /tmp/alpha_{sol,bsc,rh}_tr.json
  python3 /home/wei/.hermes/scripts/tvl_monitor.py   # 仅供参考——它仍会打印 +0.0%（DeFiLlama null 坑），真实变化看下方 TVL 段

输出：三链评分表（A+B+C+D 子分，E 叙事由分析师补 0-8）、热搜跨链同名匹配、三链 trenches（>1e12 虚标过滤+VOL/MC 失配旗标）、TVL 实算。
评分规则（75分制，共识主导）:
  A 共识 0-25: SM≥20 或 KOL≥50→25 | SM 10-19 或 KOL 20-49→18 | SM 3-9 或 KOL 5-19→10 | 其余 3
  B 数据健康 0-20: rug<0.1 且 bundler<0.15 且 top10<0.20 且 !wash→20；1项超标14；2项8；rug>0.3 或 wash→0 剔除
  C 体量 0-12: MC≥$10M→12 | $2-10M→10 | $500K-2M→8 | $200-500K→5 | $100-200K→3 | $10-100K→1 | <$10K 剔除
  D 动量 0-10: 6h≥+40% 且 1h≥0→10 | 6h +15~40% 且 1h>-20%→8 | 6h 0~15%→5 | 6h<0 或 1h≤-20%→2 | 6h<-30%→0
  硬规则优先于分数: bundler>30% 不推、rug>0.3 剔除、top10>70% 标注高度控盘；RH 链 creator_close 不加减分
⚠️ 解析输出永远打印完整 address（CA 硬规则，禁止截断）。

⚠️ 数据文件命名（08-05 晚场实测）：cron 实际抓取常用时间戳后缀
（`/tmp/alpha_sol_6h_<epoch>.json`，防同日早/晚场覆盖）。本模板硬编码
`/tmp/alpha_sol_6h.json` 会 FILE MISSING——所有 load 路径都过 `latest()`：
优先 glob `前缀*_<10位epoch>.json` 取最新时间戳文件，无则回落固定名。
"""
import json, time, urllib.request, ssl, glob, re

def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as e:
        print(f"LOAD_ERR {p}: {e}")
        return None

def latest(path):
    """取 /tmp 数据文件：优先最新时间戳后缀（`<前缀>_<10位epoch>.json`），
    无时间戳文件时回落固定名。防同日多次运行文件互相覆盖后解析到旧数据。
    08-07 修复: glob 必须用 path[:-5]+"*" (去掉 .json 后缀)——旧版 path+"*"
    (如 alpha_sol_6h.json*) 匹配不到 _<ts>.json 时间戳兄弟文件, 会静默
    回落固定名旧文件, 解析出上一场/隔日数据 (08-07 实测踩过: 输出含 FROGE
    +383% = 08-06 晚场残留, 而本次抓取的最新文件里 FROGE 已不在榜)。"""
    base = path[:-5] if path.endswith(".json") else path
    cands = [f for f in glob.glob(base + "*") if re.search(r"_(\d{10})\.json$", f)]
    if cands:
        return sorted(cands, key=lambda p: int(re.search(r"_(\d{10})\.json$", p).group(1)))[-1]
    if glob.glob(path):
        return path
    return None

def fmt_mc(v):
    if v is None: return "?"
    v = float(v)
    if v >= 1e9: return f"${v/1e9:.2f}B"
    if v >= 1e6: return f"${v/1e6:.2f}M"
    if v >= 1e3: return f"${v/1e3:.1f}K"
    return f"${v:.0f}"

def fmt_pct(v):
    if v is None: return "?"
    return f"{float(v):+.1f}%"

def parse_trending(path, chain):
    d = load(path)
    if not d: return []
    rank = d.get("data", {}).get("rank", []) if isinstance(d, dict) else []
    out = []
    for t in rank:
        out.append({
            "chain": chain, "symbol": t.get("symbol", "?"), "address": t.get("address", ""),
            "mc": t.get("market_cap"), "hi_mc": t.get("history_highest_market_cap"),
            "liq": t.get("liquidity"), "vol6h": t.get("volume"),
            "chg6h": t.get("price_change_percent"), "chg1h": t.get("price_change_percent1h"),
            "sm": t.get("smart_degen_count", 0), "kol": t.get("renowned_count", 0),
            "rug": t.get("rug_ratio"),
            "bundler": t.get("bundler_rate", t.get("bundler_trader_amount_rate")),
            "top10": t.get("top_10_holder_rate"), "wash": t.get("is_wash_trading"),
            "creator_status": t.get("creator_token_status", ""),
            "platform": t.get("launchpad_platform", ""), "holders": t.get("holder_count"),
            "twitter": t.get("twitter_username", ""),
        })
    return out

def score_token(t):
    sm = t["sm"] or 0; kol = t["kol"] or 0
    if sm >= 20 or kol >= 50: A = 25
    elif sm >= 10 or kol >= 20: A = 18
    elif sm >= 3 or kol >= 5: A = 10
    else: A = 3
    rug = t["rug"] or 0; bundler = t["bundler"] or 0; top10 = t["top10"] or 0; wash = t["wash"]
    if rug > 0.3 or wash: return (A, 0, None, None, "KILL_RUG")
    fails = sum([rug >= 0.1, bundler >= 0.15, top10 >= 0.20])
    B = {0: 20, 1: 14, 2: 8}.get(fails, 4)
    mc = t["mc"] or 0
    if mc >= 10e6: C = 12
    elif mc >= 2e6: C = 10
    elif mc >= 500e3: C = 8
    elif mc >= 200e3: C = 5
    elif mc >= 100e3: C = 3
    elif mc >= 10e3: C = 1
    else: C = -999
    c6 = t["chg6h"] or 0; c1 = t["chg1h"] or 0
    if c6 >= 40 and c1 >= 0: D = 10
    elif 15 <= c6 < 40 and c1 > -20: D = 8
    elif 0 <= c6 < 15: D = 5
    elif c6 < 0 or c1 <= -20: D = 2
    else: D = 5
    if c6 < -30: D = 0
    return (A, B, C, D, "OK")

def main():
    print("=" * 100); print("TRENDING 6h — SCORED (A+B+C+D max 67; E 叙事 by analyst +0-8)"); print("=" * 100)
    all_tokens = []
    for chain, path in [("SOL", "/tmp/alpha_sol_6h.json"), ("BSC", "/tmp/alpha_bsc_6h.json"), ("RH", "/tmp/alpha_rh_6h.json")]:
        tokens = parse_trending(latest(path), chain) if latest(path) else []
        all_tokens.extend(tokens)
        print(f"\n--- {chain}: {len(tokens)} tokens ---")
        rows = []
        for t in tokens:
            A, B, C, D, flag = score_token(t)
            if flag == "KILL_RUG": rows.append((t, -1, f"A{A} B0 RUG>0.3/WASH")); continue
            if C == -999: rows.append((t, -2, f"A{A} B{B} MC<$10K")); continue
            rows.append((t, A + B + C + D, f"A{A} B{B} C{C} D{D}"))
        for t, sub, s in sorted(rows, key=lambda x: x[1], reverse=True):
            fl = ""
            if t["bundler"] and t["bundler"] > 0.30: fl += " BUNDLER>30%!"
            if t["top10"] and t["top10"] > 0.70: fl += " TOP10>70%!"
            if t["top10"] and t["top10"] > 0.50: fl += " 高控盘"
            # 08-15 实测: hiMC 也能虚标——WALL(RH) hiMC $8.84B vs MC $3.53M (~2500x),
            # >1e12 过滤抓不到 (8.84e9 低于线)。hiMC/MC > 1000x 即虚标旗标
            if t["hi_mc"] and t["mc"] and t["hi_mc"] / t["mc"] > 1000: fl += " hiMC虚标!"
            print(f"[{s}] {t['symbol']:<12} MC {fmt_mc(t['mc']):>10} | 6h {fmt_pct(t['chg6h']):>8} 1h {fmt_pct(t['chg1h']):>8} | SM {t['sm']:>3} KOL {t['kol']:>3} | rug {t['rug']} bundler {t['bundler']} top10 {t['top10']} | wash {t['wash']} | {t['creator_status']} | {t['platform']} | holders {t['holders']} | vol6h {fmt_mc(t['vol6h'])} | hiMC {fmt_mc(t['hi_mc'])}{fl}")
            print(f"    CA: {t['address']} | tw: {t['twitter']}")
    print("\n" + "=" * 100); print("VOLUME TOP5 per chain (阶段0 — 按 volume 降序，含风险旗标)"); print("=" * 100)
    for chain, path in [("SOL", "/tmp/alpha_sol_6h.json"), ("BSC", "/tmp/alpha_bsc_6h.json"), ("RH", "/tmp/alpha_rh_6h.json")]:
        tokens = parse_trending(latest(path), chain) if latest(path) else []
        tokens.sort(key=lambda t: t["vol6h"] or 0, reverse=True)
        print(f"\n--- {chain} TOP5 by volume ---")
        for i, t in enumerate(tokens[:5], 1):
            fl = ""
            if (t["rug"] or 0) > 0.3: fl += " [RUG>0.3!]"
            if (t["bundler"] or 0) > 0.30: fl += " [BUNDLER>30%!]"
            if (t["top10"] or 0) > 0.50: fl += " [TOP10>50%!]"
            print(f"{i}. {t['symbol']:<10} | vol {fmt_mc(t['vol6h']):>9} | MC {fmt_mc(t['mc']):>9} | LP {fmt_mc(t['liq']):>8} | 6h {fmt_pct(t['chg6h']):>8} | SM {t['sm']:>3}{fl}")
            print(f"   CA: {t['address']}")
    print("=" * 100); print("HOT-SEARCHES 1h — cross-chain symbol matching"); print("=" * 100)
    hot = load(latest("/tmp/alpha_hot_1h.json")) if latest("/tmp/alpha_hot_1h.json") else None
    hot_blocks = (hot if isinstance(hot, list) else hot.get("data", [])) if hot else []
    sym_map = {}
    for blk in hot_blocks:
        ch = blk.get("chain", "?")
        print(f"\n--- hot {ch} ({blk.get('interval')}) top20 ---")
        for i, t in enumerate(blk.get("tokens", [])[:20], 1):
            sym = t.get("symbol", "?")
            sym_map.setdefault(sym.upper(), set()).add(ch)
            print(f"{i:>2}. {sym:<14} MC {fmt_mc(t.get('market_cap')):>10} visit {t.get('visiting_count')} SM {t.get('smart_degen_count',0)} | {t.get('address','')[:12]}...")
    print("\n--- CROSS-CHAIN SYMBOL MATCHES (hot) ---")
    for sym, chains in sorted(sym_map.items()):
        if len(chains) >= 2: print(f"  {sym}: {sorted(chains)}")
    trend_syms = {}
    for t in all_tokens: trend_syms.setdefault(t["symbol"].upper(), set()).add(t["chain"])
    print("\n--- TRENDING x HOT cross matches ---")
    for sym, chains in sorted(trend_syms.items()):
        if sym in sym_map and len(chains | sym_map[sym]) >= 2:
            print(f"  {sym}: trend[{sorted(chains)}] hot[{sorted(sym_map[sym])}]")
    print("=" * 100); print("TRENCHES new_creation (>=1M MC, 三链统一) — SM 数以 trending 实时值为准"); print("=" * 100)
    # >1e12 虚标过滤三链通用（08-06 起仅 RH 段内置；08-08 早场实测 SOL 同样返回 >1e12 垃圾：
    # CRK $2.9e15 / BTC $51.9B / RCAT $2B 全 holders<=6、vol<$600——此前 SOL/BSC 只 count 不过滤，逼手动复查）
    # ⚠️ 08-08 晚场新变体: 虚标不只在 >1e12 量级——SOL 批量 $74M 级假盘(MRPOM×9/PROOST×6/Nigger 等,
    # 同名多地址、holders=1、vol24h=$0、同日 13:41-15:20 创建)低于 1e12 过滤线能通过。
    # 判据补漏: (v24 or 0)/mc < 0.005 失配旗标(vol24h==0 也触发, 已修) + holders<10 旗标。
    # ⚠️ 08-20 午场实测: 抓取侧实际写 /tmp/alpha_tr_{chain}_<ts>.json (链名在 tr 后),
    # 与旧前缀 alpha_{chain}_tr 不一致 → latest() glob 匹配不到, 三链 trenches 段
    # 全部静默 "no data" (文件有内容但读不到, 逼手动重写解析脚本)。latest_any()
    # 双前缀兼容, 两种命名都认; 手写解析时按实际文件名路径直接解析, 勿信 "no data"。
    def latest_any(paths):
        for p in paths:
            f = latest(p)
            if f: return f
        return None
    for ch, label in [("sol", "SOL-trenches"), ("bsc", "BSC-trenches"), ("rh", "RH-trenches")]:
        p = latest_any([f"/tmp/alpha_{ch}_tr.json", f"/tmp/alpha_tr_{ch}.json"])
        tr = load(p) if p else None
        if not tr:
            print(f"{label}: no data")
            continue
        arr = tr.get("new_creation", []) if isinstance(tr, dict) else []
        raw_n = len(arr)
        arr = [t for t in arr if (t.get("usd_market_cap") or 0) <= 1e12]
        print(f"\n{label}: {raw_n} raw -> {len(arr)} after >1e12 虚标过滤  (空=该链无合格新币，直接写\"无\")")
        for t in arr[:20]:
            mc = t.get("usd_market_cap") or 0
            v24 = t.get("volume_24h") or 0
            flag = ""
            # ⚠️ 08-08 晚场修复: 旧版 `if v24 and mc and ...` 在 vol24h==0 时为 falsy,
            # 旗标永不触发——$74M 级批量假盘(MRPOM/PROOST, holders=1, vol24h=$0,
            # MC 低于 1e12 过滤线)全漏。改用 (v24 or 0) 使零量也触发失配旗标。
            if mc and ((v24 or 0) / mc) < 0.005: flag += " VOL/MC失配虚标!"
            if (t.get("holder_count") or 0) < 10: flag += " HOLDERS<10!"
            print(f"{t.get('symbol','?'):<12} MC {fmt_mc(mc):>10} | created {time.strftime('%m-%d %H:%M', time.localtime(t.get('created_timestamp',0)))} | SM {t.get('smart_degen_count',0)} | rug {t.get('rug_ratio')} bundler {t.get('bundler_trader_amount_rate')} top10 {t.get('top_10_holder_rate')} | vol24h {fmt_mc(v24)} | holders {t.get('holder_count')} | {t.get('creator_token_status')}{flag}")
            print(f"    CA: {t.get('address')}")
    print("\n" + "=" * 100); print("TVL historical (real change via historicalChainTvl, proxy built-in)"); print("=" * 100)
    ctx = ssl.create_default_context()
    proxy = urllib.request.ProxyHandler({"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"})
    opener = urllib.request.build_opener(proxy)
    now = int(time.time())
    for slug, label in [("Solana", "Solana"), ("BSC", "BSC"), ("Robinhood%20Chain", "RH")]:
        # 08-15 实测: historicalChainTvl 偶发 SSL UNEXPECTED_EOF (RH 单链, Sol/BSC 同刻成功)——
        # 单次 try 会整链缺失, 每链最多重试 3 次 (sleep 4), 与 gmgn TLS 抖动同模式
        for attempt in range(3):
            try:
                req = urllib.request.Request(f"https://api.llama.fi/v2/historicalChainTvl/{slug}", headers={"User-Agent": "Mozilla/5.0"})
                with opener.open(req, timeout=30) as r:
                    data = json.loads(r.read().decode())
                def closest(target): return min(data, key=lambda p: abs(p["date"] - target))["tvl"]
                cur, d1, d7 = closest(now), closest(now - 86400), closest(now - 7 * 86400)
                ch1 = (cur - d1) / d1 * 100 if d1 else 0
                ch7 = (cur - d7) / d7 * 100 if d7 else 0
                print(f"{label}: ${cur/1e6:.0f}M | 24h {ch1:+.1f}% | 7d {ch7:+.1f}%")
                break
            except Exception as e:
                print(f"{label}: attempt {attempt+1} ERR {e}")
                time.sleep(4)

if __name__ == "__main__":
    main()
