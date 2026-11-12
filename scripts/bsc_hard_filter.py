#!/usr/bin/env python3
"""BSC 打狗硬过滤器 —— 候选币先过机器门槛，不过的直接丢，不进人眼。

零 LLM 成本：纯脚本，可手动跑，也可挂 no_agent cron。

数据源分工（两份互补，不可替代）：
  * GoPlus  -> 「我买了能不能跑出来」：蜜罐 / 税 / 可增发 / 弃权 / 隐藏owner（硬结论）
  * GMGN    -> 「谁在参与、发生了什么」：LP / 币龄 / dev 史 / Top10 / Bundle / 老鼠仓

用法：
  python3 bsc_hard_filter.py <CA> [<CA> ...]     # 过滤指定代币
  python3 bsc_hard_filter.py --trending [N]      # 取 BSC trending 前 N 个当候选（默认12）
  python3 bsc_hard_filter.py --trending 12 --json
  python3 bsc_hard_filter.py --trending --pass-only

阈值全部来自 2026-10 两份研究报告（meme 跟单方法论 + 中文圈车头调研）。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

PROXY = "http://127.0.0.1:7890"
CHAIN = "bsc"
GOPLUS_CHAIN_ID = 56
GMGN = "gmgn-cli"

# ---------- 硬门槛（不通过 = FAIL，直接丢） ----------
MIN_LP_USD = 50_000          # <$50K 薄池子：10-30秒延迟会把入场价推高 3-5 倍
MIN_AGE_HOURS = 24           # <24h 是极高风险区（多数 rug 发生在此）
MAX_DEV_LAUNCHES = 3         # 连环发币者 100k 峰值率 0.0%；BSC 上 50% 的垃圾制造者 rug 过
MAX_TAX = 0.05               # 买卖税 >5% 扣分，>10% 直接丢
NEED_WEBSITE = True          # 无官网 = 100k 峰值率 0.0%
NEED_TWITTER = True          # 有推特主页：100k 峰值率 2.2% -> 15.2%

# ---------- 软门槛（不通过 = WARN，人工判断） ----------
WARN_TOP10 = 0.30            # Top10 持币（GMGN 口径已剔除池子/黑洞）
WARN_BUNDLER = 0.10          # Bundle 成交量占比（GMGN 默认线 10%）
WARN_RAT_TRADER = 0.05       # 老鼠仓（Insiders）占比
WARN_ENTRAPMENT = 0.05       # 阴谋集团/围猎盘占比
WARN_FRESH = 0.50            # 新钱包占比过高 = 可能是批量小号
WARN_VOL_LP_RATIO = 5.0      # 24h量 / LP > 5x = 疑似操纵
WARN_HOLDERS = 100           # 持币人数过少

# ---------- 致命安全项（命中即判死，不参与评分） ----------
DEAD_PREFIX = "安全:"


def classify(info, gp):
    """区分「打狗标的」和「机构/股票镜像」——后者的高 Top10 是正常结构，不是控盘。

    只按结构特征判定，不按发射台名字硬编码（TapeFour/GM 等名字像股票其实是 meme）。
    """
    top10 = f((info.get("stat") or {}).get("top_10_holder_rate"))
    holders = i(info.get("holder_count"))
    proxy = str(gp.get("is_proxy", "0")) == "1"
    lpname = (info.get("launchpad_platform") or "").lower()
    # 明确的股票发射台
    if "stock" in lpname:
        return "股票镜像/机构盘(非打狗标的)"
    # 结构特征：代理合约 + 高度集中 + 持币人数多（托管方持有背书资产）
    if proxy and top10 > 0.55 and holders > 1000:
        return "股票镜像/机构盘(非打狗标的)"
    if "flap" in lpname or "four" in lpname or "pump" in lpname:
        return "meme(发射台)"
    return "meme/其他"


def log(m):
    print(m, file=sys.stderr)


# ---------- 聪明钱库（o皇 449 地址）作为加分项 ----------
SM_STATE = os.path.join(os.path.expanduser("~"), ".hermes/cron/state/smart_money_evm.json")
SM_PER = 8       # 每命中 1 个聪明钱地址 +8 分
SM_CAP = 24      # 最多 +24


def load_sm():
    try:
        rows = json.load(open(SM_STATE, encoding="utf-8"))
        return {r["addr"].lower(): (r.get("name") or "") for r in rows if r.get("addr")}
    except Exception:  # noqa: BLE001
        return {}


def sm_holders(ca):
    """用 GMGN holders 前 100 与聪明钱库求交集 → (命中数, 名字列表)。"""
    sm = load_sm()
    if not sm:
        return 0, []
    data = gmgn(["token", "holders", "--chain", "bsc", "--address", ca,
                 "--limit", "100", "--raw"])
    rows = (data or {}).get("list") or []
    hits = []
    for h in rows:
        a = (h.get("address") or "").lower()
        if a in sm:
            hits.append(sm[a] or a[:8])
    return len(hits), hits[:4]


def gmgn(args, timeout=90):
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    for attempt in range(3):
        try:
            p = subprocess.run([GMGN] + args, capture_output=True, text=True,
                               env=env, timeout=timeout)
        except Exception as e:
            log("gmgn error: %s" % e)
            return None
        if p.returncode == 0:
            try:
                return json.loads(p.stdout.strip())
            except Exception:
                return None
        err = (p.stderr or "") + (p.stdout or "")
        if "429" in err or "RATE_LIMIT" in err:
            wait = 60 * (attempt + 1)
            log("gmgn 429 限流，等 %ds 后重试 (%d/3)" % (wait, attempt + 1))
            time.sleep(wait)
            continue
        log("gmgn rc=%s: %s" % (p.returncode, err.strip()[:160]))
        return None
    log("gmgn 限流重试耗尽: %s" % " ".join(args[:4]))
    return None


def goplus(ca, timeout=40):
    url = "https://api.gopluslabs.io/api/v1/token_security/%d?contract_addresses=%s" % (
        GOPLUS_CHAIN_ID, ca)
    try:
        # 本机外网必须走代理：显式挂 ProxyHandler（不依赖环境变量）
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
        req = urllib.request.Request(url, headers={"accept": "application/json"})
        with opener.open(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        return (data.get("result") or {}).get(ca.lower()) or {}
    except Exception as e:
        log("goplus error %s: %s" % (ca[:10], e))
        return {}


def f(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return d


def i(v, d=0):
    try:
        return int(float(v))
    except Exception:
        return d


def trend_cas(limit=12):
    d = gmgn(["market", "trending", "--chain", CHAIN, "--interval", "6h",
              "--limit", str(limit), "--raw"])
    out = []
    if not d:
        return out
    for row in (d.get("data", {}).get("rank") or d.get("rank") or []):
        a = row.get("address")
        s = row.get("symbol") or "?"
        if a:
            out.append((a, s))
    return out


def check(ca):
    """返回 dict：四层结果 + FAIL/WARN/PASS 判定"""
    info = gmgn(["token", "info", "--chain", CHAIN, "--address", ca, "--raw"])
    gp = goplus(ca)
    r = {"ca": ca, "symbol": (info or {}).get("symbol") or "?",
         "name": (info or {}).get("name") or "", "fails": [], "warns": [], "notes": [],
         "deductions": [], "class": "?", "score": 0, "dead": False, "stockish": False}
    if not info:
        # 区分「数据缺失/限流」和「真的不合格」——不要拿限流假象当淘汰
        r["verdict"] = "NODATA"
        r["fails"].append("GMGN 数据缺失(可能限流)")
        return r

    # ---------- 第 3 层：安全硬结论（GoPlus） ----------
    hard = [("is_honeypot", "蜜罐"),
            ("cannot_sell_all", "不能全部卖出"),
            ("cannot_buy", "不能买入"),
            ("hidden_owner", "隐藏owner"),
            ("can_take_back_ownership", "可夺回所有权"),
            ("owner_change_balance", "owner可改余额"),
            ("transfer_pausable", "可暂停转账"),
            ("is_blacklisted", "有黑名单")]
    for key, label in hard:
        if str(gp.get(key, "0")) == "1":
            r["fails"].append("安全:%s" % label)
    if str(gp.get("is_mintable", "0")) == "1":
        r["warns"].append("可增发(烧币可被撤销)")
    if str(gp.get("is_proxy", "0")) == "1":
        r["warns"].append("代理合约")
    if str(gp.get("is_whitelisted", "0")) == "1":
        r["warns"].append("有白名单")
    owner = str(gp.get("owner_address") or "").lower()
    if owner and set(owner.replace("0x", "")) != {"0"}:
        r["warns"].append("未弃权(owner非零地址)")
    bt, st = f(gp.get("buy_tax"), -1), f(gp.get("sell_tax"), -1)
    if bt >= 0 or st >= 0:
        r["tax"] = "买%.1f%%/卖%.1f%%" % (bt * 100, st * 100)
        if max(bt, st) > 0.10:
            r["fails"].append("税率>10%%(%s)" % r["tax"])
        elif max(bt, st) > MAX_TAX:
            r["warns"].append("税率偏高(%s)" % r["tax"])
    if str(gp.get("is_open_source", "0")) == "0":
        r["warns"].append("合约未开源")
    cp = f(gp.get("creator_percent"))
    if cp > 0.05:
        r["warns"].append("创建者持币%.1f%%" % (cp * 100))

    # ---------- 第 1 层：来源 + 基础盘（GMGN） ----------
    liq = f(info.get("liquidity"))
    r["lp"] = liq
    r["launchpad"] = info.get("launchpad_platform") or "?"
    if liq < 10_000:
        r["fails"].append("LP仅$%.0f(结构性脆弱)" % liq)
    elif liq < MIN_LP_USD:
        r["warns"].append("LP $%.0fK < $%dK(延迟会推高入场价)" % (liq / 1000, MIN_LP_USD // 1000))

    created = i(info.get("creation_timestamp"))
    age_h = (time.time() - created) / 3600.0 if created else 0
    r["age_h"] = age_h
    if created and age_h < MIN_AGE_HOURS:
        r["fails"].append("币龄%.1fh<24h(极高风险区)" % age_h)
    elif created and age_h < 24 * 7:
        r["warns"].append("币龄%.1f天(<7天高风险)" % (age_h / 24))

    pr = info.get("price") or {}
    mc = f(pr.get("price")) * f(info.get("circulating_supply"))
    r["mc"] = mc
    vol = f(pr.get("volume_24h"))
    r["vol24"] = vol
    if liq > 0 and vol / liq > WARN_VOL_LP_RATIO:
        r["warns"].append("量/LP=%.1fx(疑似操纵)" % (vol / liq))
    hold = i(info.get("holder_count"))
    r["holders"] = hold
    if hold < WARN_HOLDERS:
        r["warns"].append("持币仅%d人" % hold)

    # ---------- 第 2 层：地址画像 / 控盘（GMGN） ----------
    stt = info.get("stat") or {}
    dev = info.get("dev") or {}
    link = info.get("link") or {}
    top10 = f(stt.get("top_10_holder_rate"))
    r["top10"] = top10
    if top10 > 0.50:
        r["fails"].append("Top10 %.1f%%>50%%(高度控盘)" % (top10 * 100))
    elif top10 > WARN_TOP10:
        r["warns"].append("Top10 %.1f%% >30%%" % (top10 * 100))
    bund = f(stt.get("top_bundler_trader_percentage"))
    if bund > WARN_BUNDLER:
        r["warns"].append("Bundle %.1f%% >10%%" % (bund * 100))
    rat = f(stt.get("top_rat_trader_percentage"))
    if rat > WARN_RAT_TRADER:
        r["warns"].append("老鼠仓 %.1f%% >5%%" % (rat * 100))
    ent = f(stt.get("top_entrapment_trader_percentage"))
    if ent > WARN_ENTRAPMENT:
        r["warns"].append("围猎盘 %.1f%% >5%%" % (ent * 100))
    fresh = f(stt.get("fresh_wallet_rate"))
    if fresh > WARN_FRESH:
        r["warns"].append("新钱包 %.0f%%(疑批量小号)" % (fresh * 100))

    # ---------- 第 3 层：DEV 事件与历史 ----------
    launches = i(dev.get("creator_open_count"))
    r["dev_launches"] = launches
    if launches >= MAX_DEV_LAUNCHES:
        r["fails"].append("dev发币%d次(连环发币者)" % launches)
    cts = (dev.get("creator_token_status") or "").lower()
    if cts == "creator_close":
        r["notes"].append("dev已卖光(可能社区接管)")
    elif cts == "creator_hold":
        r["notes"].append("dev仍持仓")

    # ---------- 硬门槛：社交/官网（100k 峰值率关键因子） ----------
    site = (link.get("website") or "").strip()
    tw = (link.get("twitter_username") or "").strip()
    r["site"], r["twitter"] = bool(site), bool(tw)
    if NEED_WEBSITE and not site:
        r["fails"].append("无官网(100k峰值率0.0%)")
    if NEED_TWITTER and not tw:
        r["fails"].append("无推特主页")

    wts = info.get("wallet_tags_stat") or {}
    r["smart"] = i(wts.get("smart_wallets"))
    r["renowned"] = i(wts.get("renowned_wallets"))

    # ---------- 分类 + 评分 ----------
    r["class"] = classify(info, gp)
    r["stockish"] = r["class"].startswith("股票镜像")
    r["dead"] = any(x.startswith(DEAD_PREFIX) for x in r["fails"])
    if r["dead"]:
        r["score"] = 0
    else:
        ded = []
        if liq < 10_000:
            ded.append((40, "LP<$10K"))
        elif liq < MIN_LP_USD:
            ded.append((15, "LP<$%dK" % (MIN_LP_USD // 1000)))
        if created and age_h < MIN_AGE_HOURS:
            ded.append((20, "币龄<24h"))
        elif created and age_h < 24 * 7:
            ded.append((8, "币龄<7天"))
        if launches >= MAX_DEV_LAUNCHES:
            ded.append((20, "dev发币%d次" % launches))
        if not site:
            ded.append((12, "无官网"))
        if not tw:
            ded.append((6, "无推特"))
        if not r["stockish"]:
            if top10 > 0.50:
                ded.append((25, "Top10>50%"))
            elif top10 > WARN_TOP10:
                ded.append((10, "Top10>30%"))
        if bund > WARN_BUNDLER:
            ded.append((8, "Bundle>10%"))
        if rat > WARN_RAT_TRADER:
            ded.append((10, "老鼠仓>5%"))
        if ent > WARN_ENTRAPMENT:
            ded.append((8, "围猎盘>5%"))
        if liq > 0 and vol / liq > WARN_VOL_LP_RATIO:
            ded.append((10, "量/LP=%.1fx" % (vol / liq)))
        if str(gp.get("is_mintable", "0")) == "1":
            ded.append((10, "可增发"))
        if str(gp.get("is_proxy", "0")) == "1":
            ded.append((5, "代理合约"))
        if str(gp.get("is_open_source", "0")) == "0":
            ded.append((8, "未开源"))
        if hold < WARN_HOLDERS:
            ded.append((10, "持币<100"))
        if owner and set(owner.replace("0x", "")) != {"0"}:
            ded.append((10, "未弃权"))
        if max(bt, st) > MAX_TAX:
            ded.append((15, "税>5%"))
        base = max(0, 100 - sum(p for p, _ in ded))
        # 聪明钱加分：命中 o皇库里的地址（+8/个，最多 +24）
        n_sm, sm_names = sm_holders(ca)
        r["sm_o"] = n_sm
        r["sm_names"] = sm_names
        r["score"] = min(100, base + min(SM_CAP, n_sm * SM_PER))
        r["deductions"] = ded
    r["verdict"] = "FAIL" if r["fails"] else ("WARN" if r["warns"] else "PASS")
    return r


def show(r):
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "🚫", "NODATA": "❓"}.get(r["verdict"], "?")
    print("%s %s (%s) [%s]" % (icon, r["symbol"], r["verdict"], r["launchpad"]))
    print("   CA: %s" % r["ca"])
    print("   MC $%.0f | LP $%.0f | 币龄%.1fh | 持币%d | 24h量$%.0f"
          % (r.get("mc", 0), r.get("lp", 0), r.get("age_h", 0), r.get("holders", 0),
             r.get("vol24", 0)))
    print("   Top10 %.1f%% | dev发币%d次 | 聪明钱%d | KOL%d | 官网%s 推特%s | 税%s"
          % (r.get("top10", 0) * 100, r.get("dev_launches", 0), r.get("smart", 0),
             r.get("renowned", 0), "有" if r.get("site") else "无",
             "有" if r.get("twitter") else "无", r.get("tax", "-")))
    if r["fails"]:
        print("   ❌ 硬门槛不过: %s" % "; ".join(r["fails"]))
    if r["warns"]:
        print("   ⚠️ 警示: %s" % "; ".join(r["warns"]))
    if r["notes"]:
        print("   📝 %s" % "; ".join(r["notes"]))
    if r.get("sm_o"):
        print("   🧠 聪明钱库命中 %d 个: %s (+%d分)"
              % (r["sm_o"], ", ".join(r.get("sm_names") or []), min(SM_CAP, r["sm_o"] * SM_PER)))
    print()


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    pass_only = "--pass-only" in args
    args = [a for a in args if a not in ("--json", "--pass-only")]

    if args and args[0] == "--trending":
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 12
        cands = trend_cas(n)
        log("候选: %d 个 (BSC trending)" % len(cands))
    else:
        cands = [(a, "?") for a in args]
    if not cands:
        print("用法: bsc_hard_filter.py <CA>... | --trending [N] [--json] [--pass-only]")
        return

    results = []
    for idx, (ca, _sym) in enumerate(cands, 1):
        log("[%d/%d] %s" % (idx, len(cands), ca[:12]))
        r = check(ca)
        results.append(r)
        time.sleep(0.3)

    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
        return

    nodata = [r for r in results if r["verdict"] == "NODATA"]
    valid = [r for r in results if r["verdict"] != "NODATA"]
    dead = [r for r in valid if r.get("dead")]
    stock = [r for r in valid if not r.get("dead") and r.get("stockish")]
    meme = sorted([r for r in valid if not r.get("dead") and not r.get("stockish")],
                  key=lambda x: x.get("score", 0), reverse=True)
    print("=" * 56)
    print("BSC 硬过滤器: 候选%d | 打狗候选%d | 股票镜像%d | 安全判死%d | 无数据%d"
          % (len(results), len(meme), len(stock), len(dead), len(nodata)))
    print("=" * 56)
    if nodata:
        print("⚠️ %d 个取不到数据（多为 GMGN 限流）——不判死，建议稍后重跑。" % len(nodata))
    print()
    if meme:
        print("───── 🎯 打狗候选排行榜（按评分降序）─────")
        print()
        for r in meme:
            icon = "✅" if r["score"] >= 80 else ("⚠️" if r["score"] >= 60 else "🚫")
            print("%s %d分  %s  (%s) [%s]" % (icon, r["score"], r["symbol"], r["class"],
                                             r.get("launchpad", "?")))
            print("   CA: %s" % r["ca"])
            print("   MC $%.0f | LP $%.0f | 币龄%.1fh | 持币%d | 24h量$%.0f"
                  % (r.get("mc", 0), r.get("lp", 0), r.get("age_h", 0),
                     r.get("holders", 0), r.get("vol24", 0)))
            print("   Top10 %.1f%% | dev发币%d次 | 聪明钱%d | KOL%d | 官网%s 推特%s | 税%s"
                  % (r.get("top10", 0) * 100, r.get("dev_launches", 0), r.get("smart", 0),
                     r.get("renowned", 0), "有" if r.get("site") else "无",
                     "有" if r.get("twitter") else "无", r.get("tax", "-")))
            if r.get("deductions"):
                print("   📉 扣分: %s" % "; ".join("-%d %s" % (p, w) for p, w in r["deductions"]))
            if r["warns"]:
                print("   ⚠️ 警示: %s" % "; ".join(r["warns"]))
            for line in r["notes"]:
                print("   📝 %s" % line)
            print()
    elif not pass_only:
        print("🎯 无打狗候选（本轮全是股票镜像或安全判死）")
        print()
    if dead and not pass_only:
        print("───── 🚫 安全判死（蜜罐/不能卖/可夺权等，%d 个）─────" % len(dead))
        for r in dead:
            print("   %s (%s) — %s" % (r["symbol"], r["class"], "; ".join(r["fails"])))
        print()
    if stock and not pass_only:
        print("───── 🏦 股票镜像/机构盘（非打狗标的，%d 个，忽略）─────" % len(stock))
        for r in stock:
            print("   %s | MC $%.0f | LP $%.0f | 持币%d | Top10 %.1f%%(托管结构，非控盘)"
                  % (r["symbol"], r.get("mc", 0), r.get("lp", 0), r.get("holders", 0),
                     r.get("top10", 0) * 100))
        print()
    if nodata:
        print("───── ❓ 无数据（%d 个）─────" % len(nodata))
        for r in nodata:
            print("   %s | %s" % (r["ca"][:20], "; ".join(r["fails"])))


if __name__ == "__main__":
    main()
