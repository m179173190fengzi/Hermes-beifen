#!/usr/bin/env python3
"""输出 fomo.family 热门代币 TOP5 的纯文本块（含叙事素材），供链上日报直接嵌入。

数据源：
  * POST https://prod-api.fomo.family/proxy/trendingTokens（cookie 认证）→ 榜单
  * gmgn-cli token info（带 6h 缓存）→ 补 name / twitter / 官网 / 发射台（叙事素材）

用法：
  python3 fomo_top5.py          # 打印日报块（默认 TOP5）
  python3 fomo_top5.py 8        # 打印前 8
  python3 fomo_top5.py --force  # 忽略缓存重新抓
"""
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
COOKIES = os.path.join(HOME, ".hermes/secrets/fomo_cookies.json")
CACHE = os.path.join(HOME, ".hermes/cron/state/fomo_trend_cache.json")
NARR_CACHE = os.path.join(HOME, ".hermes/cron/state/fomo_narr_cache.json")
URL = "https://prod-api.fomo.family/proxy/trendingTokens"
GMGN = os.path.join(HOME, ".local/bin/gmgn-cli")
TTL = 20 * 60
NARR_TTL = 6 * 3600
PROXY = "http://127.0.0.1:7890"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/155.0.0.0 Safari/537.36")
CHAIN = {1399811149: "sol", 56: "bsc", 1: "eth", 8453: "base"}

# 小黄人 = Unipcs（fomo 盈利榜 #1，PnL $5.74M，Fantom Troupe）
UNIPCS_ID = "36adb85a-c0fd-5fa8-916d-8fdc32fe4237"
UNIPCS_WALLET = "2heJbC32Tpfcb3nbUb5ER61K11FGZVfVGtVnDm6LDogF"  # 他的链上交易钱包
UNIPCS_NAME = "小黄人(Unipcs·fomo盈利榜#1)"
EXTRACTOR = os.path.join(HOME, ".hermes/scripts/fomo_cookie_extract.py")
VENV_PY = os.path.join(HOME, ".venvs/xmon/bin/python")
SWAPS_URL = "https://prod-api.fomo.family/v2/users/%s/swaps?limit=150"
UNIPCS_BUYS = 3          # 展示他最近几笔买入


def refresh_cookies():
    """cookie/JWT 会随浏览器活动轮换，401 时重抽一次。"""
    if not os.path.exists(VENV_PY):
        return False
    try:
        subprocess.run([VENV_PY, EXTRACTOR], capture_output=True, timeout=90)
        return True
    except Exception:  # noqa: BLE001
        return False


def api_get(url, retry=True):
    """带 Cookie + Bearer(privy-token) 的 GET；401 时重抽 cookie 再试一次。"""
    ck = load_json(COOKIES)
    header, tok = ck.get("header"), ""
    for c in ck.get("cookies", []):
        if c.get("name") == "privy-token":
            tok = c.get("value") or ""
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    cmd = ["curl", "-s", "--http2", "--max-time", "25",
           "-H", "Cookie: " + (header or ""), "-H", "Authorization: Bearer " + tok,
           "-H", "User-Agent: " + UA, "-H", "Accept: application/json",
           "-H", "Origin: https://fomo.family", "-H", "Referer: https://fomo.family/", url]
    try:
        body = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env).stdout
        j = json.loads(body or "{}")
    except Exception:  # noqa: BLE001
        return None
    if j.get("statusCode") == 401 and retry and refresh_cookies():
        return api_get(url, retry=False)
    return j


def dex_symbols(addrs):
    """批量把合约地址 → {symbol, name, mc, chg}（DexScreener）。"""
    addrs = [a for a in dict.fromkeys(addrs) if a]
    if not addrs:
        return {}
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    url = "https://api.dexscreener.com/latest/dex/tokens/" + ",".join(addrs[:20])
    try:
        body = subprocess.run(["curl", "-s", "--max-time", "25", "-H", "User-Agent: " + UA, url],
                              capture_output=True, text=True, timeout=60, env=env).stdout
        pairs = (json.loads(body or "{}") or {}).get("pairs") or []
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for p in pairs:
        a = (p.get("baseToken") or {}).get("address")
        if not a:
            continue
        vol = ((p.get("volume") or {}).get("h24") or 0)
        prev = out.get(a)
        if prev and (prev.get("_vol") or 0) >= vol:
            continue
        out[a] = {
            "symbol": (p.get("baseToken") or {}).get("symbol") or "?",
            "name": (p.get("baseToken") or {}).get("name") or "",
            "mc": p.get("marketCap") or p.get("fdv") or 0,
            "chg": ((p.get("priceChange") or {}).get("h24") or 0),
            "_vol": vol,
        }
    return out


def _gmgn_buys(n):
    """主源：GMGN 钱包活动（不依赖浏览器 cookie，最稳）。"""
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        out = subprocess.run([GMGN, "portfolio", "activity", "--chain", "sol",
                              "--wallet", UNIPCS_WALLET, "--raw"],
                             capture_output=True, text=True, timeout=120, env=env).stdout
        acts = (json.loads(out or "{}") or {}).get("activities") or []
    except Exception:  # noqa: BLE001
        return []
    buys, seen = [], set()
    for a in acts:
        if a.get("event_type") != "buy":
            continue
        tk = a.get("token") or {}
        ca = tk.get("address") or ""
        if not ca or ca in seen:
            continue
        seen.add(ca)
        buys.append({
            "ca": ca,
            "sym": tk.get("symbol") or "",
            "usd": a.get("cost_usd") or 0,
            "time": time.strftime("%m-%d %H:%M", time.localtime(a.get("timestamp") or 0)),
        })
        if len(buys) >= n:
            break
    return buys


def _fomo_buys(n):
    """兜底源：fomo 接口（cookie/JWT 会轮换，可能失败）。"""
    j = api_get(SWAPS_URL % UNIPCS_ID)
    swaps = ((j or {}).get("responseObject") or {}).get("swaps") or []
    buys, seen = [], set()
    STABLE = {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
              "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
    for s in swaps:
        if ((s.get("display") or {}).get("side")) != "buy":
            continue
        out_addr = s.get("outTokenAddress") or ""
        in_addr = s.get("inTokenAddress") or ""
        token = out_addr if out_addr not in STABLE else in_addr
        if not token or token in seen:
            continue
        seen.add(token)
        buys.append({
            "ca": token, "sym": "",
            "usd": s.get("humanUsdAmountOut") or s.get("humanUsdAmountIn") or 0,
            "time": (s.get("createdAt") or "")[:16].replace("T", " "),
        })
        if len(buys) >= n:
            break
    return buys


def unipcs_buys(n=UNIPCS_BUYS):
    """小黄人最近买入：GMGN 主源，失败时用 fomo 接口兜底（结果是本元组(来源,列表)）。"""
    b = _gmgn_buys(n)
    if b:
        return "GMGN链上", b
    b2 = _fomo_buys(n)
    if b2:
        return "fomo接口", b2
    return "", []


def _is_stable(sym, name):
    """稳定币特征过滤（符号/名称含 USD/Dollar 等）。"""
    s = ("%s %s" % (sym or "", name or "")).lower()
    for k in ("usd", "dollar", "usdc", "usdt", "dai", "tether", "stable"):
        if k in s:
            return True
    return False


def load_json(p, d=None):
    try:
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return d if d is not None else {}


def fetch(force=False):
    c = load_json(CACHE)
    if not force and c.get("ts") and time.time() - c["ts"] < TTL and c.get("tokens"):
        return c["tokens"]
    if not os.path.exists(COOKIES):
        return []
    cookie = load_json(COOKIES).get("header")
    if not cookie:
        return []
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    cmd = ["curl", "-s", "--http2", "-X", "POST", "--max-time", "30",
           "-H", "Cookie: " + cookie, "-H", "User-Agent: " + UA,
           "-H", "Accept: application/json", "-H", "Content-Type: application/json",
           "-H", "Origin: https://fomo.family", "-H", "Referer: https://fomo.family/",
           "-d", "{}", URL]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env).stdout
        rows = json.loads(out or "{}").get("responseObject") or []
    except Exception:  # noqa: BLE001
        return []
    toks = []
    for i, r in enumerate(rows):
        tk = r.get("token") or {}
        nid = tk.get("networkId")
        lp = tk.get("launchpad") or {}
        toks.append({
            "sym": tk.get("symbol") or "?", "name": tk.get("name") or "",
            "chain": CHAIN.get(nid) if isinstance(nid, int) else str(nid),
            "ca": tk.get("address") or "",
            "mc": float(r.get("marketCap") or 0), "vol": float(r.get("volume24") or 0),
            "chg": float(r.get("change24") or 0), "holders": r.get("holders") or 0,
            "rank": i + 1,
            "launchpad": lp.get("launchpadName") or "",
            "grad": lp.get("graduationPercent") or 0,
        })
    if toks:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump({"ts": time.time(), "tokens": toks},
                  open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return toks


def narr(token, cache, force=False):
    """用 GMGN token info 补叙事素材（twitter/官网/发射台），带 6h 缓存。"""
    ca = token["ca"]
    if not ca:
        return {}
    hit = cache.get(ca)
    if hit and not force and time.time() - hit.get("ts", 0) < NARR_TTL:
        return hit.get("d", {})
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        p = subprocess.run([GMGN, "token", "info", "--chain", token["chain"],
                            "--address", ca, "--raw"],
                           capture_output=True, text=True, timeout=90, env=env)
        j = json.loads(p.stdout or "{}")
    except Exception:  # noqa: BLE001
        return hit.get("d", {}) if hit else {}
    link = j.get("link") or {}
    d = {
        "symbol": j.get("symbol") or "",
        "name": j.get("name") or token["name"],
        "desc": (j.get("description") or "")[:80],
        "tw": link.get("twitter_username") or "",
        "web": link.get("website") or "",
        "launchpad": j.get("launchpad_platform") or token.get("launchpad") or "",
    }
    cache[ca] = {"ts": time.time(), "d": d}
    return d


def main():
    n = 5
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    force = "--force" in sys.argv
    toks = fetch(force=force)
    if not toks:
        print("🔥 fomo热门代币 TOP5: 暂不可用（cookie 失效或接口变动，请重跑 fomo_cookie_extract.py）")
        return 0

    ncache = load_json(NARR_CACHE)
    print("━━━ 🔥 fomo 热门代币 TOP%d ━━━" % n)
    for t in toks[:n]:
        d = narr(t, ncache, force=force)
        print("  #%d %s (%s) | MC $%s | 24h %s%% | 量 $%s | 持币 %s"
              % (t["rank"], t["sym"], t["chain"], f"{t['mc']:,.0f}", f"{t['chg']:+.1f}",
                 f"{t['vol']:,.0f}", f"{t['holders']:,}"))
        bits = []
        if d.get("name"):
            bits.append("名称: %s" % d["name"])
        tw = (d.get("tw") or "").lstrip("@")
        # twitter 字段常被伪造成链接（用户名/status/xxx、i/communities/xxx、search?q=）
        if tw and re.fullmatch(r"[A-Za-z0-9_]{2,20}", tw):
            bits.append("@%s" % tw)
        elif tw:
            bits.append("社交链接(非常规账号): %s" % tw[:60])
        if d.get("web"):
            bits.append(d["web"])
        if d.get("launchpad"):
            bits.append("发射台: %s" % d["launchpad"])
        if bits:
            print("     📖 素材: " + " | ".join(bits))
        if d.get("desc"):
            print("     📝 %s" % d["desc"])
        print("     CA: %s" % t["ca"])

    # ── 小黄人（Unipcs · fomo 盈利榜 #1）最新买入 ──
    src, buys = unipcs_buys()
    if buys:
        syms = dex_symbols([b["ca"] for b in buys])
        lines = []
        for b in buys:
            s = syms.get(b["ca"], {})
            d2 = narr({"ca": b["ca"], "chain": "sol",
                       "name": s.get("name") or ""}, ncache, force=force)
            sym = b.get("sym") or s.get("symbol") or d2.get("symbol") or "?"
            name = d2.get("name") or s.get("name") or ""
            # 稳定币（USDG/Global Dollar 之类）不算买入标的 —— 用符号+GMGN名称双重判断
            if _is_stable(sym, name):
                continue
            try:
                usd = float(b["usd"])
            except (TypeError, ValueError):
                usd = 0.0
            lines.append("  • %s | 买入 $%s | %s | MC $%s | 24h %s%%"
                         % (sym, f"{usd:,.0f}", b["time"],
                            f"{s.get('mc', 0):,.0f}", f"{s.get('chg', 0):+.1f}"))
            bits2 = []
            if d2.get("name"):
                bits2.append("名称: %s" % d2["name"])
            tw2 = (d2.get("tw") or "").lstrip("@")
            if tw2 and re.fullmatch(r"[A-Za-z0-9_]{2,20}", tw2):
                bits2.append("@%s" % tw2)
            elif tw2:
                bits2.append("社交链接(非常规账号): %s" % tw2[:56])
            if d2.get("launchpad"):
                bits2.append("发射台: %s" % d2["launchpad"])
            if bits2:
                lines.append("     📖 素材: " + " | ".join(bits2))
            lines.append("     CA: %s" % b["ca"])
        if lines:
            print("")
            print("  ── 🐤 %s 最新买入（源: %s）──" % (UNIPCS_NAME, src))
            print("\n".join(lines))
    else:
        print("")
        print("  ── 🐤 %s 最新买入: 暂不可用（cookie/JWT 失效）──" % UNIPCS_NAME)

    json.dump(ncache, open(NARR_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
