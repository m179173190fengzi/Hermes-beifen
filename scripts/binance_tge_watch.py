#!/usr/bin/env python3
"""币安 TGE / 打新公告监控（no_agent cron，零 LLM 成本）。

盯 币安公告 的 TGE 类条目（TGE / Launchpool / Megadrop / HODLer Airdrop /
Booster / Pre-Market / Binance Wallet），一有新的就推送，并把条目写入 pending
队列供分析任务消费。

静默语义：没有新公告 → 不输出（cron 不推送任何东西）。

用法：
  python3 binance_tge_watch.py           # 正常（cron）
  python3 binance_tge_watch.py --test    # 打印当前匹配到的公告（不写状态）
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

HOME = os.path.expanduser("~")
STATE = os.path.join(HOME, ".hermes/cron/state/binance_tge.json")
PROXY = "http://127.0.0.1:7890"
API = ("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
       "?type=1&pageNo=1&pageSize=20")
CATALOGS = {48, 49, 93, 128}          # 新币上线 / 新闻 / 活动 / 空投
KEYWORDS = ["tge", "token generation event", "launchpool", "megadrop",
            "hodler airdrop", "booster", "pre-market", "binance wallet",
            "binance alpha", "alpha will list", "will list"]
# 噪音：这些标题里带关键词但其实不是打新机会
NOISE = ["trading competition", "trading tournament", "carnival",
         "predict lol", "zero trading fee", "collateral asset", "margin"]
CST = timezone(timedelta(hours=8))


def load(p, d):
    try:
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return d


def save(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0"})
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    with opener.open(req, timeout=40) as r:
        return json.loads(r.read().decode())


def fmt_time(cid):
    try:
        return datetime.fromtimestamp(int(cid) / 1000, CST).strftime("%m-%d %H:%M")
    except (TypeError, ValueError):
        return "?"


def main():
    test = "--test" in sys.argv
    try:
        data = fetch()
    except Exception as e:  # noqa: BLE001
        print("⚠️ 币安公告抓取失败: %s" % str(e)[:120])
        return 1

    arts = []
    for c in (data.get("data") or {}).get("catalogs") or []:
        if c.get("catalogId") not in CATALOGS:
            continue
        for a in c.get("articles") or []:
            title = a.get("title") or ""
            low = title.lower()
            if any(k in low for k in KEYWORDS) and not any(n in low for n in NOISE):
                arts.append({
                    "id": str(a.get("id")),
                    "code": a.get("code") or "",
                    "title": title,
                    "catalog": c.get("catalogName"),
                    "ts": fmt_time(a.get("releaseDate")),
                    "url": "https://www.binance.com/en/support/announcement/%s" % (a.get("code") or ""),
                })

    if test:
        for a in arts[:8]:
            print("[%s] %s | %s" % (a["ts"], a["catalog"], a["title"][:80]))
        print("共匹配 %d 条" % len(arts))
        return 0

    st = load(STATE, {"seen": {}, "pending": []})
    seen = st.get("seen") or {}
    pending = st.get("pending") or []

    # 首次运行：把当前所有条目记为已见，不推送（避免历史公告刷屏）
    if not seen:
        st["seen"] = {a["id"]: datetime.now(CST).isoformat(timespec="seconds") for a in arts}
        st["pending"] = []
        save(STATE, st)
        print("（首次运行：已播种 %d 条历史公告为已读，不推送）" % len(arts))
        return 0

    new = []
    for a in arts:
        if a["id"] in seen:
            continue
        seen[a["id"]] = datetime.now(CST).isoformat(timespec="seconds")
        new.append(a)
        pending.append({"id": a["id"], "title": a["title"], "catalog": a["catalog"],
                        "url": a["url"], "ts": a["ts"],
                        "detected": datetime.now(CST).isoformat(timespec="seconds"),
                        "analyzed": False})

    # 只保留最近 40 条待分析，避免无限增长
    st["pending"] = pending[-40:]
    st["seen"] = dict(list(seen.items())[-400:])
    save(STATE, st)

    if new:
        lines = ["🆕 币安公告（TGE/打新类）"]
        for a in new[:6]:
            lines.append("• [%s] %s\n  %s\n  %s" % (a["ts"], a["catalog"], a["title"], a["url"]))
        if len(new) > 6:
            lines.append("…另有 %d 条" % (len(new) - 6))
        lines.append("\n（已进入分析队列，稍后给结论）")
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
