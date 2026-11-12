#!/usr/bin/env python3
"""X 监控 + 链上热度榜交叉验证（no_agent cron 用，零 LLM 成本）。

三条能力：
  1) 名人/KOL 推文监控（x_watchlist.json 的 accounts）—— 命中才推，否则静默
  2) 推文 → 链上热度榜交叉验证：推文正文与「GMGN 热搜榜」代币做词级匹配，
     命中就附上 MC / 涨跌 / 量 / CA
  3) --feed 模式：扫你的首页时间线（≈你刷到的东西）→ 与热搜榜交叉 → 输出
     「X 热议 ↔ 链上热度标的」

热度榜数据源：GMGN hot-searches（搜索热度口径）。
  ⚠️ fomo.family 官方热度榜需登录，落地页无 API 暴露，故用 GMGN 热搜榜替代
     （实测 6h 热搜第 1 名 = FTR，与 X 上特斯拉超跑发布会叙事吻合）。

用法：
  python3 x_watch.py                 # 正常跑（cron 用）
  python3 x_watch.py --test          # 忽略去重，打印所有命中
  python3 x_watch.py --all           # 忽略过滤，每账号最新一条
  python3 x_watch.py --feed          # X 热议 ↔ 链上热度榜
  python3 x_watch.py --hot           # 只看当前热搜榜 TOP5
"""
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
COOKIE_ENV = os.path.join(HOME, ".hermes/secrets/x_cookies.env")
CONFIG = os.path.join(HOME, ".hermes/cron/x_watchlist.json")
STATE = os.path.join(HOME, ".hermes/cron/state/x_watch.json")
HOT_CACHE = os.path.join(HOME, ".hermes/cron/state/x_hot_cache.json")
PROXY = "http://127.0.0.1:7890"
TWITTER_BIN = os.path.join(HOME, ".local/bin/twitter")
GMGN_BIN = os.path.join(HOME, ".local/bin/gmgn-cli")

STATE_KEEP = 40       # 每账号保留最近多少条已见 ID
MAX_BLOCKS = 8        # 单次最多推几条
HOT_TOP = 5           # 热搜榜展示前 N
HOT_MATCH_POOL = 20   # 用于匹配的候选池大小（比展示的更宽）
HOT_CACHE_TTL = 20 * 60

# fomo.family 热门代币（需登录 cookie；POST /proxy/trendingTokens）
FOMO_COOKIES = os.path.join(HOME, ".hermes/secrets/fomo_cookies.json")
FOMO_TREND_URL = "https://prod-api.fomo.family/proxy/trendingTokens"
FOMO_CACHE = os.path.join(HOME, ".hermes/cron/state/fomo_trend_cache.json")
FOMO_MATCH_POOL = 20

CURL_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/155.0.0.0 Safari/537.36")

STOP = set("""The This That These Those And But With From They Them Their There Then What When
Where Why How Just Now New All For Not You Your Our His Her She Was Were Are Has Have Had
Will Would Can Could Should One Two Three More Most Some Any Get Got Make Made Like Look
Looks Good Great Best First Last Next Today Tomorrow Yesterday LATEST Breaking Update
After Before Over Under Into Out About Only Also Even Much Many Very Still Back Come Came
Said Says Say Who Whom Which While Here Him Man Men Day Days Week Month Year Time
Video Watch Read Full Story Source Via Photo Photos Image Clip Freedom Money Japan Tokyo
Story Part Big Cool Damn Must Seat Belts Coffee Cup Holders Track Mode Aero Features
Provide Passive Downforce Package Roll Car Cars World Real""".split())

# 名字里太通用、容易误匹配的词（品牌/叙事实体不在此列——它们是我们要匹配的目标）
NAME_STOP = set("""coin token the and for you new dog cat baby king queen moon star sun
space world real first last best good great big small love life time day night
with your this that from have will here there when what""".split())
NAME_MATCH_MIN_VOL = 300000  # 名称词匹配要求代币成交量达标，避免小盘噪音


def load_env():
    env = dict(os.environ)
    env["HTTPS_PROXY"] = PROXY
    env["HTTP_PROXY"] = PROXY
    if os.path.exists(COOKIE_ENV):
        with open(COOKIE_ENV, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\s*export\s+([A-Z_]+)=(.*)", line.strip())
                if m:
                    env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    env["PATH"] = os.path.join(HOME, ".local/bin") + ":" + env.get("PATH", "")
    return env


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def twitter_json(args, env, timeout=150):
    """跑 twitter CLI 并解析 JSON（CLI 会在 JSON 前打印 WARNING 行）。"""
    try:
        p = subprocess.run([TWITTER_BIN, "--compact"] + args,
                           capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None, "超时"
    out = p.stdout or ""
    start = out.find("[")
    if start < 0:
        return None, (out.strip().splitlines() or ["无输出"])[-1][:80]
    try:
        return json.loads(out[start:]), None
    except json.JSONDecodeError as exc:
        return None, "JSON解析失败: %s" % exc


# ---------------- 链上热度榜 ----------------

def fetch_fomo(force=False):
    """fomo.family 热门代币榜（POST /proxy/trendingTokens，需登录 cookie）。"""
    cache = load_json(FOMO_CACHE, {})
    if not force and cache.get("ts") and time.time() - cache["ts"] < HOT_CACHE_TTL:
        return cache.get("tokens", [])
    if not os.path.exists(FOMO_COOKIES):
        return []
    try:
        cookie = json.load(open(FOMO_COOKIES, encoding="utf-8"))["header"]
    except (json.JSONDecodeError, KeyError, OSError):
        return []
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    cmd = ["curl", "-s", "--http2", "-X", "POST", "--max-time", "30",
           "-H", "Cookie: " + cookie, "-H", "User-Agent: " + CURL_UA,
           "-H", "Accept: application/json", "-H", "Content-Type: application/json",
           "-H", "Origin: https://fomo.family", "-H", "Referer: https://fomo.family/",
           "-d", "{}", FOMO_TREND_URL]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
        data = json.loads(p.stdout or "{}")
    except Exception:  # noqa: BLE001
        return cache.get("tokens", [])
    rows = data.get("responseObject") or []
    toks = []
    for i, r in enumerate(rows[:FOMO_MATCH_POOL]):
        tk = r.get("token") or {}
        chain = "sol" if tk.get("networkId") == 1399811149 else str(tk.get("networkId") or "?")
        toks.append({
            "sym": tk.get("symbol") or "?",
            "name": tk.get("name") or "",
            "chain": chain,
            "ca": tk.get("address") or "",
            "mc": float(r.get("marketCap") or 0),
            "vol": float(r.get("volume24") or 0),
            "chg": float(r.get("change24") or 0),
            "holders": r.get("holders") or 0,
            "t10": 0,
            "rank": i + 1,
            "src": "fomo",
        })
    if toks:
        save_json(FOMO_CACHE, {"ts": time.time(), "tokens": toks})
    return toks


def fetch_hot(force=False):
    """GMGN 热搜榜（sol + bsc）→ [{sym,name,chain,ca,mc,vol,chg,holders,t10}]"""
    cache = load_json(HOT_CACHE, {})
    if not force and cache.get("ts") and time.time() - cache["ts"] < HOT_CACHE_TTL:
        return cache.get("tokens", []), cache.get("ts")
    env = load_env()
    toks, ts = [], time.time()
    for chain in ("sol", "bsc"):
        try:
            p = subprocess.run([GMGN_BIN, "market", "hot-searches", "--chain", chain,
                                "--interval", "6h", "--limit", str(HOT_MATCH_POOL), "--raw"],
                               capture_output=True, text=True, timeout=120, env=env)
            for item in json.loads(p.stdout):
                for i, t in enumerate(item.get("tokens", [])):
                    toks.append({
                        "sym": t.get("symbol") or "?",
                        "name": t.get("name") or "",
                        "chain": t.get("chain") or chain,
                        "ca": t.get("address") or "",
                        "mc": t.get("market_cap") or 0,
                        "vol": t.get("volume") or 0,
                        "chg": t.get("price_change_percent") or 0,
                        "holders": t.get("holder_count") or 0,
                        "t10": t.get("top_10_holder_rate") or 0,
                        "rank": i + 1,
                        "src": "gmgn",
                    })
        except Exception:  # noqa: BLE001
            continue
    if toks:
        save_json(HOT_CACHE, {"ts": ts, "tokens": toks})
    return toks, ts


def match_hot(text, hots):
    """推文正文 ↔ 热搜榜代币 词级匹配。返回命中的 token 列表。"""
    low = " " + re.sub(r"https?://\S+|@\w+", " ", (text or "").lower()) + " "
    out, seen = [], set()
    for t in hots:
        sym = (t["sym"] or "").lower()
        hit = False
        if len(sym) >= 3 and re.search(r"\b" + re.escape(sym) + r"\b", low):
            hit = True
        if not hit:
            for w in re.split(r"[^a-z0-9\u4e00-\u9fff]+", (t["name"] or "").lower()):
                if (len(w) >= 5 and w not in NAME_STOP
                        and (t["vol"] or 0) >= NAME_MATCH_MIN_VOL
                        and re.search(r"\b" + re.escape(w) + r"\b", low)):
                    hit = True
                    break
        key = (t["sym"], t["ca"])
        if hit and key not in seen:
            seen.add(key)
            out.append(t)
    out.sort(key=lambda x: x["vol"], reverse=True)
    return out[:3]


def fmt_hot(t):
    tag = "fomo热门" if t.get("src") == "fomo" else "GMGN热搜"
    extra = (" | Top10 %.1f%%" % ((t["t10"] or 0) * 100)) if t.get("t10") else ""
    return ("  • %s (%s) %s#%s | MC $%s | %s%% | 量 $%s | 持币 %s%s\n    CA: %s"
            % (t["sym"], t["chain"], tag, t["rank"], f"{t['mc']:,.0f}", f"{t['chg']:+.1f}",
               f"{t['vol']:,.0f}", f"{t['holders']:,}", extra, t["ca"]))


def dedupe_pool(*pools):
    """按 CA 去重，fomo 源优先。"""
    seen, out = set(), []
    for pool in pools:
        for t in pool:
            if t["ca"] and t["ca"] in seen:
                continue
            seen.add(t["ca"])
            out.append(t)
    return out


# ---------------- 过滤逻辑 ----------------

def kw_regex(keywords):
    parts = []
    for k in keywords:
        esc = re.escape(k)
        parts.append(r"\b%s\b" % esc if k.isascii() else esc)
    return re.compile("|".join(parts), re.IGNORECASE) if parts else None


def hit(tw, acc, kw_pat):
    text = tw.get("text") or ""
    m = kw_pat.search(text) if kw_pat else None
    kw_hit = m.group(0) if m else None
    likes = tw.get("likes") or 0
    viral = likes >= (acc.get("min_likes") or 0)
    mode = acc.get("mode", "keyword")
    if mode == "all":
        return True, "全部模式"
    if kw_hit:
        return True, "关键词「%s」" % kw_hit
    if viral:
        return True, "高互动 %s赞" % f"{likes:,}"
    return False, None


def main():
    argv = set(sys.argv[1:])
    test = "--test" in argv
    show_all = "--all" in argv
    feed_mode = "--feed" in argv
    hot_only = "--hot" in argv

    cfg = load_json(CONFIG, {"accounts": [], "keywords": []})
    kw_pat = kw_regex(cfg.get("keywords", []))
    env = load_env()
    fomo_toks = fetch_fomo()
    gmgn_toks, _ = fetch_hot()
    hots = dedupe_pool(fomo_toks, gmgn_toks)
    output = []
    errors = []

    if hot_only:
        print("🔥 热度榜（fomo 热门 + GMGN 热搜）")
        print("")
        if fomo_toks:
            print("【fomo.family 热门代币 TOP%d】" % HOT_TOP)
            for t in fomo_toks[:HOT_TOP]:
                print(fmt_hot(t))
            print("")
        else:
            print("⚠️ fomo 热门榜不可用（cookie 失效或接口变动）")
            print("")
        for ch in ("sol", "bsc"):
            sub = [t for t in gmgn_toks if t["chain"] == ch][:HOT_TOP]
            if not sub:
                continue
            print("【GMGN 热搜 %s TOP%d】" % (ch.upper(), HOT_TOP))
            for t in sub:
                print(fmt_hot(t))
            print("")
        return 0

    if feed_mode:
        tweets, err = twitter_json(["feed"], env)
        if tweets is None:
            print("⚠️ 首页时间线抓取失败: %s" % err)
            return 1
        lines, used = [], set()
        for tw in tweets:
            text = tw.get("text") or ""
            for t in match_hot(text, hots):
                key = (t["sym"], t["ca"])
                if key in used:
                    continue
                used.add(key)
                lines.append(fmt_hot(t) + "\n    ↳ 热议来源: @%s %s"
                             % ((tw.get("author") or "?").lstrip("@"), (tw.get("time") or "?")))
        if lines or fomo_toks or gmgn_toks:
            output.append("🔥 X 热议 ↔ 链上热度榜（首页 %d 条）" % len(tweets))
            output.append("")
            if lines:
                output.append("⚡ 交叉命中（X 有讨论 + 链上在热）:")
                output.extend(lines)
                output.append("")
            if fomo_toks:
                output.append("📊 fomo.family 热门代币 TOP%d:" % HOT_TOP)
                for t in fomo_toks[:HOT_TOP]:
                    output.append(fmt_hot(t))
                output.append("")
            for ch in ("sol", "bsc"):
                sub = [t for t in gmgn_toks if t["chain"] == ch][:HOT_TOP]
                if not sub:
                    continue
                output.append("📊 GMGN 热搜 %s TOP%d:" % (ch.upper(), HOT_TOP))
                for t in sub:
                    output.append(fmt_hot(t))
                output.append("")
        print("\n".join(output))
        return 0

    # ---- 账号监控 ----
    state = load_json(STATE, {})
    hits = []
    for acc in cfg.get("accounts", []):
        handle = acc["handle"]
        label = acc.get("label", handle)
        args = ["user-posts", handle, "-n", str(cfg.get("max_per_account", 10)), "--json"]
        tweets, err = twitter_json(args, env)
        if tweets is None:  # X 侧偶发抽风，重试一次
            time.sleep(8)
            tweets, err = twitter_json(args, env)
        if tweets is None:
            errors.append("%s(@%s): %s" % (label, handle, err))
            continue
        seen = state.get(handle, [])
        new_ids = []
        for tw in tweets:
            tid = str(tw.get("id"))
            if tid in new_ids:
                continue
            new_ids.append(tid)
            if not show_all and not test and tid in seen:
                continue
            ok, why = hit(tw, acc, kw_pat)
            if show_all or ok:
                text = (tw.get("text") or "").strip() or "(仅图片/视频，无正文)"
                block = ("🔥 %s @%s%s\n%s\n❤️ %s赞 | 🔁 %s转 | 🕐 %s\nhttps://x.com/%s/status/%s"
                         % (label, handle, "" if show_all else " — %s" % why, text,
                            f"{tw.get('likes', 0):,}", f"{tw.get('rts', 0):,}",
                            tw.get("time", "?"), handle, tid))
                if not show_all:
                    m = match_hot(text, hots)
                    if m:
                        block += "\n🪙 链上热度匹配:\n" + "\n".join(fmt_hot(x) for x in m)
                hits.append((tw.get("likes") or 0, block))
        merged = new_ids + [i for i in state.get(handle, []) if i not in new_ids]
        state[handle] = merged[:STATE_KEEP]
        if not test:
            save_json(STATE, state)

    hits.sort(key=lambda x: x[0], reverse=True)
    blocks = [b for _, b in hits[:MAX_BLOCKS]]
    if blocks:
        header = "📡 X 监控 — %d 条新动态" % len(blocks)
        if len(hits) > MAX_BLOCKS:
            header += "（共 %d 条，已推热度前 %d）" % (len(hits), MAX_BLOCKS)
        output.append(header)
        output.append("")
        output.extend(blocks)
    if errors:
        output.append("")
        output.append("⚠️ 抓取失败: " + " | ".join(errors))
    if output:
        print("\n".join(output))
    elif errors and not test:
        print("⚠️ X 监控异常: " + " | ".join(errors))
    return 0


if __name__ == "__main__":
    sys.exit(main())
