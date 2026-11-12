#!/usr/bin/env python3
"""日报数据预消化（双链）—— 脚本干确定性活，agent 只写叙事。

原来日报要 36 次工具调用、每次 --raw 的完整 JSON 全进上下文（单次 ~144K tokens）。
现在：2 次 trenches + 2 次 trending + TVL，输出一份紧凑摘要（~60 行）。

用法：
  python3 daily_scan.py                # 默认：BSC + SOL
  python3 daily_scan.py --chain bsc    # 单链
  python3 daily_scan.py --min-score 60 # 调整候选门槛
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

HOME = os.path.expanduser("~")
GMGN = os.path.join(HOME, ".local/bin/gmgn-cli")
TVL = os.path.join(HOME, ".hermes/scripts/tvl_monitor.py")
PROXY = "http://127.0.0.1:7890"
CST = timezone(timedelta(hours=8))

MIN_SCORE = 60        # 优质标的候选门槛
MAX_PER_CHAIN = 5     # 每链最多输出几个候选
NEW_MC_MIN = 1_000_000
NEW_AGE_H = 24
TOP_TREND = 5
MIN_GAP = 6.0          # GMGN 两次调用之间最小间隔（秒），避免限流
_LAST_CALL = [0.0]


def fnum(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def gmgn(args, timeout=150, retries=4):
    """调 gmgn-cli，遇 429 限流按提示退避重试。"""
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    for attempt in range(retries):
        gap = MIN_GAP - (time.time() - _LAST_CALL[0])
        if gap > 0:
            time.sleep(gap)
        try:
            p = subprocess.run([GMGN] + args, capture_output=True, text=True,
                               env=env, timeout=timeout)
            _LAST_CALL[0] = time.time()
            if p.returncode == 0 and p.stdout.strip():
                try:
                    return json.loads(p.stdout)
                except json.JSONDecodeError:
                    return None
            msg = (p.stderr or "") + (p.stdout or "")
            if "429" in msg or "RATE_LIMIT" in msg:
                m = re.search(r"~(\d+)s remaining", msg)
                wait = (int(m.group(1)) + 12) if m else 45
                time.sleep(min(wait, 120))
                continue
            # 网络类错误（TLS/连接断开/超时）也重试
            if any(k in msg for k in ("fetch failed", "TLS", "socket", "timeout",
                                      "ECONNRESET", "ETIMEDOUT", "502", "503")):
                time.sleep(6)
                continue
            return None
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return None


# ---------------- 打分（0-100，对应 11 项检查） ----------------

def score_token(t):
    """从 trenches 的字段打分。返回 (score, 11项通过数, 可核查项数, 风险列表, 亮点列表)。"""
    mc = fnum(t.get("market_cap"))
    lp = fnum(t.get("liquidity"))
    hold = int(fnum(t.get("holder_count")))
    vol = fnum(t.get("volume_24h"))
    top10 = fnum(t.get("top_10_holder_rate"))
    bundle = fnum(t.get("bundler_trader_amount_rate"))
    entrap = fnum(t.get("entrapment_ratio"))
    rat = fnum(t.get("rat_trader_amount_rate"))
    sniper = fnum(t.get("top70_sniper_hold_rate"))
    dev_n = int(fnum(t.get("creator_created_count")))
    dev_status = (t.get("creator_token_status") or "").lower()
    burn = (t.get("burn_status") or "").lower()
    honey = t.get("is_honeypot")
    twitter = t.get("twitter") or t.get("twitter_handle")
    followers = int(fnum(t.get("x_user_follower")))
    created = fnum(t.get("created_timestamp"))
    age_h = ((time.time() - created) / 3600) if created else 0
    buy_tax = fnum(t.get("buy_tax"))
    sell_tax = fnum(t.get("sell_tax"))
    smart = int(fnum(t.get("smart_degen_count")))
    dex_boost = fnum(t.get("dexscr_boost_fee"))

    checks, risks, highs = [], [], []

    def chk(ok, label):
        checks.append(1 if ok else 0)
        if not ok:
            risks.append(label)

    chk(lp >= 30_000, "LP<$30K")
    chk(burn in ("yes", "y", "burned", "burn", "locked") or fnum(t.get("burn_ratio")) > 0.9, "LP未烧/未锁")
    chk(str(honey).lower() in ("no", "0", "false", "none", ""), "疑似蜜罐")
    chk(top10 <= 0.20, "Top10>20%%(%.0f%%)" % (top10 * 100))
    chk(bundle <= 0.15 and entrap <= 0.05, "关联盘(bundle%.0f%%/围猎%.0f%%)" % (bundle * 100, entrap * 100))
    chk(dev_n < 5, "dev连环发币%d次" % dev_n)
    chk(bool(twitter) and age_h >= 24, "社交缺失/过新")
    chk(not (buy_tax > 5 or sell_tax > 5), "税>5%%(%.0f%%/%.0f%%)" % (buy_tax, sell_tax))
    chk(hold >= 300, "持币<300(%d)" % hold)
    chk(lp > 0 and vol >= lp / 2, "成交量偏低")
    chk(not (sniper > 0.25 or rat > 0.15), "狙击/鼠仓高(sniper%.0f%%)" % (sniper * 100))

    passed = sum(checks)
    total = len(checks)
    # 评分：每过一项 +9，基础 1
    score = min(100, max(0, 1 + passed * 9))
    # 加分项
    if smart >= 5:
        score = min(100, score + 6)
        highs.append("聪明钱%d" % smart)
    if fnum(t.get("renowned_count")) >= 3:
        score = min(100, score + 4)
        highs.append("KOL%d" % int(fnum(t.get("renowned_count"))))
    if followers >= 5000:
        highs.append("推特粉丝%s" % f"{followers:,}")
    if fnum(t.get("net_buy_24h")) > 0:
        highs.append("24h净买入+$%.0fK" % (fnum(t.get("net_buy_24h")) / 1000))
    if dev_status in ("creator_hold", "creator_hold_all"):
        risks.append("dev仍持仓")
    if dex_boost > 0:
        highs.append("已买推广")
    return score, passed, total, risks, highs, age_h


def fmt(t, score, passed, total, risks, highs, age_h):
    mc = fnum(t.get("market_cap"))
    lp = fnum(t.get("liquidity"))
    hold = int(fnum(t.get("holder_count")))
    vol = fnum(t.get("volume_24h"))
    top10 = fnum(t.get("top_10_holder_rate"))
    dev_n = int(fnum(t.get("creator_created_count")))
    lp_name = (t.get("launchpad_platform") or t.get("launchpad") or "-")
    lines = ["%s | 评分%d | 11项 %d/%d(以此为准,勿复算) | MC $%s | LP $%s | 持币%d | Top10 %.0f%% | dev%d次 | 量$%s | 币龄%.1fh | %s"
             % (t.get("symbol") or "?", score, passed, total,
                f"{mc:,.0f}", f"{lp:,.0f}", hold, top10 * 100, dev_n,
                f"{vol:,.0f}", age_h, lp_name)]
    if highs:
        lines.append("   亮点: " + " · ".join(highs))
    if risks:
        lines.append("   风险: " + " · ".join(risks[:4]))
    lines.append("   CA: %s" % (t.get("address") or ""))
    return "\n".join(lines)


def gates(t):
    """硬门槛：任何一条不过直接淘汰（评分救不回来）。"""
    lp = fnum(t.get("liquidity"))
    hold = int(fnum(t.get("holder_count")))
    vol = fnum(t.get("volume_24h"))
    top10 = fnum(t.get("top_10_holder_rate"))
    entrap = fnum(t.get("entrapment_ratio"))
    bundle = fnum(t.get("bundler_trader_amount_rate"))
    g = []
    # 注：SOL 未迁移的 pump/flap 币 LP 天然很小，门槛设 $10K 而不是 $30K
    if lp < 10_000:
        g.append("LP<$10K")
    if top10 > 0.50:
        g.append("Top10>50%")
    if entrap > 0.30:
        g.append("围猎盘>30%")
    if bundle > 0.40:
        g.append("bundle>40%")
    if hold < 200:
        g.append("持币<200")
    if vol < 50_000:
        g.append("24h量<$50K")
    return g


# ---------------- 主流程 ----------------

def trenches(chain):
    d = gmgn(["market", "trenches", "--chain", chain,
              "--type", "new_creation", "--type", "near_completion", "--type", "completed",
              "--limit", "40", "--raw"])
    return d if isinstance(d, dict) else {}


def trending(chain):
    d = gmgn(["market", "trending", "--chain", chain, "--interval", "6h",
              "--limit", "30", "--order-by", "volume", "--raw"])
    if isinstance(d, dict):
        return (d.get("data") or {}).get("rank") or []
    return []


LLAMA = ("https://api.llama.fi/overview/%s/%s"
         "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")


def human(n):
    n = float(n or 0)
    if abs(n) >= 1e9:
        return "%.2fB" % (n / 1e9)
    if abs(n) >= 1e6:
        return "%.1fM" % (n / 1e6)
    if abs(n) >= 1e3:
        return "%.0fK" % (n / 1e3)
    return "%.0f" % n


def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with op.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def activity_lines():
    """链上活跃度：24h DEX 成交量 TOP5 + Fees（DefiLlama，走 chain_rank.py）。"""
    try:
        p = subprocess.run([sys.executable, os.path.join(HOME, ".hermes/scripts/chain_rank.py"),
                            "--top", "5"], capture_output=True, text=True, timeout=240)
        lines = [ln for ln in (p.stdout or "").splitlines()[1:] if ln.strip()]
        if lines:
            return lines
    except Exception:  # noqa: BLE001
        pass
    return ["数据获取失败"]


def gmgn_fee_lines():
    """GMGN 平台收入（fees）——链上打狗活跃度的温度计。"""
    try:
        d = fetch_json("https://api.llama.fi/summary/fees/gmgn?dataType=dailyFees")
    except Exception:  # noqa: BLE001
        return []
    chart = d.get("totalDataChart") or []
    if len(chart) < 3:
        return []
    # 近 3 日逐日对比
    threeday = chart[-3:]
    parts = []
    for ts, v in threeday:
        try:
            day = datetime.fromtimestamp(int(ts), CST).strftime("%m-%d")
        except (TypeError, ValueError, OSError):
            day = "?"
        parts.append("%s $%s" % (day, human(v)))
    v3 = [float(v) for _, v in threeday]
    chg3 = (v3[-1] - v3[0]) / v3[0] * 100 if v3[0] else 0
    # 7 日趋势（首尾对比 + 峰值）
    week = [float(v) for _, v in chart[-7:]]
    chg7 = (week[-1] - week[0]) / week[0] * 100 if week[0] else 0
    peak = max(week)
    trend = "↓" if chg7 < -5 else ("↑" if chg7 > 5 else "→")
    return ["GMGN 收入: %s（3日 %+.0f%%）| 7日趋势 %s%.0f%%（峰值 $%s）"
            % (" → ".join(parts), chg3, trend, abs(chg7), human(peak))]


def main():
    args = sys.argv[1:]
    chains = ["bsc", "sol", "robinhood"]
    global MIN_SCORE
    for i, a in enumerate(args):
        if a == "--chain" and i + 1 < len(args):
            chains = [args[i + 1]]
        if a == "--min-score" and i + 1 < len(args):
            MIN_SCORE = int(args[i + 1])

    out = []
    act = activity_lines()
    if act:
        out.append("━━━ 💰 链上活跃度（24h）━━━")
        out.extend(act)
        out.extend(gmgn_fee_lines())
        out.append("")

    new_coins, trend_summary = [], []

    for chain in chains:
        tr = trenches(chain)
        if not tr:
            out.append("━━━ ⚠️ %s 数据源失败（GMGN 限流或网络），本轮跳过 ━━━\n" % chain.upper())
            continue
        cands, gated = [], 0
        for cat in ("completed", "near_completion", "new_creation"):
            for t in (tr.get(cat) or []):
                s, p, tot, risks, highs, age_h = score_token(t)
                t["_meta"] = (s, p, tot, risks, highs, age_h)
                if gates(t):
                    gated += 1
                    continue
                cands.append(t)
                # 新币监控：1D 内 + MC≥$1M + 持币≥200 + 量≥$50K
                if (age_h and age_h <= NEW_AGE_H
                        and fnum(t.get("market_cap")) >= NEW_MC_MIN
                        and int(fnum(t.get("holder_count"))) >= 200
                        and fnum(t.get("volume_24h")) >= 50_000):
                    new_coins.append((chain, t, s, age_h))

        # 去重：同地址 + 同 symbol（同名仿盘只留评分最高的）
        seen, by_sym = set(), {}
        for t in cands:
            a = t.get("address")
            if not a or a in seen:
                continue
            seen.add(a)
            sym = (t.get("symbol") or "").upper()
            prev = by_sym.get(sym)
            if prev is None or t["_meta"][0] > prev["_meta"][0]:
                by_sym[sym] = t
        uniq = list(by_sym.values())
        uniq.sort(key=lambda x: x["_meta"][0], reverse=True)

        picks = [t for t in uniq if t["_meta"][0] >= MIN_SCORE][:MAX_PER_CHAIN]
        n_pass = len([t for t in uniq if t["_meta"][0] >= MIN_SCORE])
        out.append("━━━ 🔥 %s 候选（评分≥%d：%d 个｜硬门槛淘汰 %d｜去重后 %d）━━━"
                   % (chain.upper(), MIN_SCORE, n_pass, gated, len(uniq)))
        if not picks:
            out.append("本时段无过线标的")
        for t in picks:
            out.append(fmt(t, *t["_meta"]))
        out.append("")

        # 热度榜（叙事参考，不打分）
        td = trending(chain)
        if td:
            parts = []
            for r in td:
                if len(parts) >= TOP_TREND:
                    break
                mc = fnum(r.get("market_cap"))
                sym = (r.get("symbol") or "").strip()
                if not sym or mc < 100_000:
                    continue
                chg = fnum(r.get("price_change_percent1h"))
                parts.append("%s $%.1fM(1h%+.0f%%)" % (sym, mc / 1e6, chg))
            trend_summary.append("%s: %s" % (chain.upper(), " | ".join(parts)))

    if new_coins:
        out.append("━━━ 🆕 新币监控（1D 内 + MC≥$1M）━━━")
        for chain, t, s, age_h in sorted(new_coins, key=lambda x: -fnum(x[1].get("market_cap")))[:8]:
            out.append("%s [%s] MC $%s | 币龄%.1fh | 持币%d | Top10 %.0f%% | 量$%s | 评分%d | CA: %s"
                       % (t.get("symbol") or "?", chain, f"{fnum(t.get('market_cap')):,.0f}", age_h,
                          int(fnum(t.get("holder_count"))), fnum(t.get("top_10_holder_rate")) * 100,
                          f"{fnum(t.get('volume_24h')):,.0f}", s, t.get("address") or ""))
        out.append("")

    if trend_summary:
        out.append("━━━ 📈 热度榜（1h 变动，叙事参考）━━━")
        out.extend(trend_summary)

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
