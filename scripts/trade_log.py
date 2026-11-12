#!/usr/bin/env python3
"""交易复盘闭环（猎人手记）—— 零 LLM 成本。

核心：**入场瞬间自动快照指标**，之后自动追踪 1h/6h/24h，最后自动归因：
"你哪一类单必亏"。

用法：
  # 1) 记一笔（自动抓入场指标快照）
  python3 trade_log.py add <CA> [--chain sol|bsc] [--usd 200]
                           [--reason "特斯拉发布会事件驱动"] [--tags "事件驱动,sol"]
                           [--plan "事件当天减半，冲高清仓"]

  # 2) 刷新所有未平仓（算 1h/6h/24h 标记 + 当前浮盈；跌破 -20% 会告警）
  python3 trade_log.py update

  # 3) 看未平仓
  python3 trade_log.py list

  # 4) 平仓（默认用当前市价）
  python3 trade_log.py close <id> [--price 0.0072] [--note "发布会兑现走一半"]

  # 5) 周报归因（胜率/期望值/哪类单必亏）
  python3 trade_log.py report [--days 30]
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

HOME = os.path.expanduser("~")
JOURNAL = os.path.join(HOME, ".hermes/trading/journal.json")
GMGN = os.path.join(HOME, ".local/bin/gmgn-cli")
PROXY = "http://127.0.0.1:7890"
STOP_PCT = -20.0          # 硬止损线（用户规则）
TZ = timezone(timedelta(hours=8))


# ---------------- 基础 ----------------

def load():
    if os.path.exists(JOURNAL):
        try:
            return json.load(open(JOURNAL, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"trades": []}


def save(d):
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    json.dump(d, open(JOURNAL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def now_iso():
    return datetime.now(TZ).isoformat(timespec="seconds")


def fnum(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ---------------- 链上快照 ----------------

def snapshot(ca, chain):
    """抓入场指标快照（GMGN token info）。"""
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        out = subprocess.run([GMGN, "token", "info", "--chain", chain,
                              "--address", ca, "--raw"],
                             capture_output=True, text=True, timeout=120, env=env).stdout
        j = json.loads(out or "{}")
    except Exception:  # noqa: BLE001
        return {}
    price = (j.get("price") or {})
    stat = (j.get("stat") or {})
    dev = (j.get("dev") or {})
    link = (j.get("link") or {})
    px = fnum(price.get("price"))
    supply = fnum(j.get("circulating_supply")) or fnum(j.get("total_supply"))
    return {
        "sym": j.get("symbol") or "?",
        "name": j.get("name") or "",
        "price": px,
        "mc": px * supply if (px and supply) else 0,   # GMGN 无现成 MC 字段，自行计算
        "lp": fnum(j.get("liquidity")),
        "holders": j.get("holder_count") or 0,
        "vol24": fnum(price.get("volume_24h")),
        "ath": fnum(j.get("ath_price")),
        "top10": fnum(stat.get("top_10_holder_rate")),
        "bundle": fnum(stat.get("top_bundler_trader_percentage")),
        "entrap": fnum(stat.get("top_entrapment_trader_percentage")),
        "dev_launches": dev.get("creator_open_count") or 0,
        "dev_status": dev.get("creator_token_status") or "",
        "launchpad": j.get("launchpad_platform") or "",
        "twitter": link.get("twitter_username") or "",
    }


def mc_band(mc):
    if mc < 100_000:
        return "MC<100K(微盘)"
    if mc < 1_000_000:
        return "MC 100K-1M"
    if mc < 10_000_000:
        return "MC 1M-10M"
    if mc < 50_000_000:
        return "MC 10M-50M"
    return "MC>50M"


# ---------------- 命令 ----------------

def cmd_add(argv):
    if not argv:
        print("用法: add <CA> [--chain sol|bsc] [--usd N] [--type pvp|ferment] "
              "[--reason ...] [--tags a,b] [--plan ...]")
        return 1
    ca = argv[0]
    opt = {"chain": "sol", "usd": 0, "reason": "", "tags": "", "plan": "", "type": ""}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--") and i + 1 < len(argv):
            k = a[2:]
            if k in opt:
                opt[k] = argv[i + 1]
            i += 2
        else:
            i += 1

    snap = snapshot(ca, opt["chain"])
    if not snap:
        print("⚠️ 抓不到链上数据（GMGN 失败或地址不对）——仍会记录，但快照为空")
        snap = {}
    d = load()
    tid = "t%d" % int(time.time())
    tags = [t.strip() for t in opt["tags"].split(",") if t.strip()]
    if snap.get("mc"):
        tags.append(mc_band(snap["mc"]))
    if snap.get("launchpad"):
        tags.append(snap["launchpad"])
    # 盘型：pvp(浇给/赚了就跑) 或 ferment(发酵/出本长持)
    ptype = (opt["type"] or "").strip().lower()
    if ptype in ("pvp", "浇给"):
        ptype = "pvp"
    elif ptype in ("ferment", "fomo", "发酵", "长持"):
        ptype = "ferment"
    else:
        ptype = "未分类"
    if ptype != "未分类":
        tags.append("类型:" + ptype)
    trade = {
        "id": tid,
        "status": "open",
        "chain": opt["chain"],
        "ca": ca,
        "sym": snap.get("sym") or "?",
        "name": snap.get("name") or "",
        "opened_at": now_iso(),
        "entry": snap,
        "usd": fnum(opt["usd"]),
        "reason": opt["reason"],
        "plan": opt["plan"],
        "type": ptype,
        "tags": tags,
        "marks": {},
        "closed_at": None,
        "exit": None,
    }
    d["trades"].append(trade)
    save(d)
    e = snap
    print("✅ 已记账 [%s] %s (%s)" % (tid, trade["sym"], opt["chain"]))
    print("   入场: $%.8f | MC $%s | LP $%s | 持币 %s | Top10 %.1f%% | dev发币%s次 | %s"
          % (fnum(e.get("price")), f"{fnum(e.get('mc')):,.0f}", f"{fnum(e.get('lp')):,.0f}",
             e.get("holders") or 0, fnum(e.get("top10")) * 100, e.get("dev_launches") or 0,
             e.get("launchpad") or "-"))
    print("   标签: %s" % ", ".join(tags))
    if opt["plan"]:
        print("   离场计划: %s" % opt["plan"])
    else:
        print("   ⚠️ 没写离场计划（心法缺口 A：入场前必须知道什么时候走）")
    return 0


def cmd_update(argv):
    d = load()
    alerts, touched = [], 0
    for t in d["trades"]:
        if t["status"] != "open":
            continue
        snap = snapshot(t["ca"], t["chain"])
        p = fnum(snap.get("price"))
        e = fnum((t.get("entry") or {}).get("price"))
        if not p or not e:
            continue
        touched += 1
        chg = (p / e - 1) * 100
        t["last_price"] = p
        t["last_chg_pct"] = round(chg, 2)
        t["last_check"] = now_iso()
        # 时间标记 1h / 6h / 24h
        try:
            opened = datetime.fromisoformat(t["opened_at"])
            age_h = (datetime.now(TZ) - opened).total_seconds() / 3600
        except Exception:  # noqa: BLE001
            age_h = 0
        for mark, h in (("1h", 1), ("6h", 6), ("24h", 24)):
            if age_h >= h and mark not in t["marks"]:
                t["marks"][mark] = {"price": p, "chg_pct": round(chg, 2)}
                print("📌 %s %s 标记: %+.1f%%" % (t["sym"], mark, chg))
        if chg <= STOP_PCT and not t.get("stop_alerted"):
            t["stop_alerted"] = True
            alerts.append("🔴 %s 跌破 %.0f%% 止损线（当前 %+.1f%%，入场 $%.8f → 现 $%.8f）"
                          % (t["sym"], STOP_PCT, chg, e, p))
    save(d)
    if alerts:
        print("\n".join(alerts))
        print("（心法第5条：宁可饿着，也别把剩下的子弹全打出去赌 —— 该走就走）")
    elif touched:
        pass  # 正常刷新 → 静默
    return 0


def cmd_list(argv):
    d = load()
    opens = [t for t in d["trades"] if t["status"] == "open"]
    if not opens:
        print("当前没有未平仓记录")
        return 0
    print("未平仓 %d 笔:" % len(opens))
    for t in opens:
        chg = t.get("last_chg_pct")
        print("  [%s] %-10s %s | 入 $%.8f | 现 %s | 仓位 $%s"
              % (t["id"], t["sym"], t["chain"], fnum((t.get("entry") or {}).get("price")),
                 ("%+.1f%%" % chg) if chg is not None else "未刷新",
                 f"{fnum(t.get('usd')):,.0f}"))
        if t.get("plan"):
            print("        离场计划: %s" % t["plan"])
    return 0


def cmd_close(argv):
    if not argv:
        print("用法: close <id> [--price X] [--note ...]")
        return 1
    tid = argv[0]
    price, note = None, ""
    i = 1
    while i < len(argv):
        if argv[i] == "--price" and i + 1 < len(argv):
            price = fnum(argv[i + 1])
            i += 2
        elif argv[i] == "--note" and i + 1 < len(argv):
            note = argv[i + 1]
            i += 2
        else:
            i += 1
    d = load()
    for t in d["trades"]:
        if t["id"] != tid:
            continue
        if price is None:
            snap = snapshot(t["ca"], t["chain"])
            price = fnum(snap.get("price"))
        e = fnum((t.get("entry") or {}).get("price"))
        if not price or not e:
            print("⚠️ 没有有效价格，无法计算盈亏")
            return 1
        pnl = (price / e - 1) * 100
        t["status"] = "closed"
        t["closed_at"] = now_iso()
        t["exit"] = {"price": price, "pnl_pct": round(pnl, 2), "note": note}
        save(d)
        print("✅ [%s] %s 已平仓: %+.2f%%  (入 $%.8f → 出 $%.8f)"
              % (tid, t["sym"], pnl, e, price))
        if note:
            print("   备注: %s" % note)
        return 0
    print("找不到 %s" % tid)
    return 1


def cmd_report(argv):
    days = 30
    for i, a in enumerate(argv):
        if a == "--days" and i + 1 < len(argv):
            days = int(argv[i + 1])
    d = load()
    cut = datetime.now(TZ) - timedelta(days=days)
    trades = []
    for t in d["trades"]:
        try:
            if datetime.fromisoformat(t["opened_at"]) >= cut:
                trades.append(t)
        except Exception:  # noqa: BLE001
            trades.append(t)
    if not trades:
        print("📓 近 %d 天没有交易记录（心法缺口 D：没有记录就没有进步）" % days)
        return 0

    closed = [t for t in trades if t["status"] == "closed" and t.get("exit")]
    openn = [t for t in trades if t["status"] == "open"]
    lines = ["📓 猎人手记 · 近 %d 天（共 %d 笔，已平 %d / 持有 %d）"
             % (days, len(trades), len(closed), len(openn))]

    if closed:
        wins = [t for t in closed if t["exit"]["pnl_pct"] > 0]
        losses = [t for t in closed if t["exit"]["pnl_pct"] <= 0]
        wr = len(wins) / len(closed) * 100
        aw = sum(t["exit"]["pnl_pct"] for t in wins) / len(wins) if wins else 0
        al = sum(t["exit"]["pnl_pct"] for t in losses) / len(losses) if losses else 0
        exp = sum(t["exit"]["pnl_pct"] for t in closed) / len(closed)
        lines.append("")
        lines.append("胜率 %.0f%%（%d胜/%d负）｜ 平均盈利 %+.1f%% ｜ 平均亏损 %+.1f%%"
                     % (wr, len(wins), len(losses), aw, al))
        lines.append("单笔期望值 %+.1f%%  ← 正数才值得继续打" % exp)

        # 归因：按标签分组
        groups = {}
        for t in closed:
            for tag in (t.get("tags") or ["未分类"]):
                g = groups.setdefault(tag, [])
                g.append(t["exit"]["pnl_pct"])
        lines.append("")
        lines.append("按特征归因（期望值从差到好）:")
        for tag, l in sorted(groups.items(), key=lambda x: sum(x[1]) / len(x[1])):
            avg = sum(l) / len(l)
            if len(l) >= 1:
                lines.append("  %-22s %d笔 ｜ 期望 %+.1f%%" % (tag, len(l), avg))
        lines.append("")
        lines.append("最差标签: %s" % min(groups.items(), key=lambda x: sum(x[1]) / len(x[1]))[0])

        # 盘型对比：pvp（浇给·赚了就跑）vs ferment（发酵·出本长持）
        by_type = {}
        for t in closed:
            by_type.setdefault(t.get("type") or "未分类", []).append(t["exit"]["pnl_pct"])
        if by_type:
            lines.append("")
            lines.append("按盘型对比（决定你该打哪种）:")
            for k, l in sorted(by_type.items(), key=lambda x: -len(x[1])):
                w = sum(1 for v in l if v > 0)
                lines.append("  %-8s %2d笔 ｜ 胜率 %3.0f%% ｜ 期望 %+.1f%%"
                             % (k, len(l), w / len(l) * 100, sum(l) / len(l)))
    else:
        lines.append("")
        lines.append("（还没有已平仓记录 —— 平仓后我才能算胜率和期望值）")

    # 心法纪律检查
    no_plan = [t for t in trades if not t.get("plan")]
    no_snap = [t for t in trades if not (t.get("entry") or {}).get("mc")]
    lines.append("")
    lines.append("纪律检查:")
    lines.append("  没写离场计划的: %d 笔%s" % (len(no_plan), "  ← 违心法缺口A" if no_plan else ""))
    lines.append("  入场快照缺失的: %d 笔%s" % (len(no_snap), "  ← 违心法缺口D" if no_snap else ""))
    print("\n".join(lines))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd, argv = sys.argv[1], sys.argv[2:]
    return {"add": cmd_add, "update": cmd_update, "list": cmd_list,
            "close": cmd_close, "report": cmd_report}.get(cmd, lambda a: print(__doc__) or 0)(argv)


if __name__ == "__main__":
    sys.exit(main())
