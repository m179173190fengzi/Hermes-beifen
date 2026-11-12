#!/usr/bin/env python3
"""钱包交易行为审计：抓 GMGN 活动记录，算补仓/追高/持仓时长/单笔金额分散度。

用法：python3 wallet_audit.py --wallet 0x... [--chains bsc,sol,robinhood]
"""
import argparse
import json
import os
import subprocess
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

PROXY = "http://127.0.0.1:7890"
CST = timezone(timedelta(hours=8))
CACHE = os.path.expanduser("~/.hermes/cron/state/wallet_audit.json")


def gmgn(args):
    env = dict(os.environ)
    env["HTTPS_PROXY"] = PROXY
    env["HTTP_PROXY"] = PROXY
    r = subprocess.run(["gmgn-cli"] + args, capture_output=True, text=True, env=env, timeout=120)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def activities(wallet, chain, max_pages=4):
    out, cursor = [], None
    for _ in range(max_pages):
        args = ["portfolio", "activity", "--chain", chain, "--wallet", wallet,
                "--limit", "100", "--raw"]
        if cursor:
            args += ["--cursor", cursor]
        d = gmgn(args)
        items = d.get("activities") or []
        out.extend(items)
        cursor = d.get("next")
        if not cursor or not items:
            break
    return out


def analyze(rows):
    rows = sorted(rows, key=lambda r: r["timestamp"])
    per = defaultdict(lambda: {"qty": 0.0, "cost": 0.0, "buys": [], "sells": [],
                               "realized": 0.0, "sym": ""})
    add_cnt = add_up = add_down = 0
    rebuy_after_sell = 0
    trade_usd = []
    for r in rows:
        a = r["token"]["address"]
        p = per[a]
        p["sym"] = r["token"].get("symbol") or "?"
        amt = float(r.get("token_amount") or 0)
        usd = float(r.get("cost_usd") or 0)
        px = float(r.get("price_usd") or 0)
        if r["event_type"] == "buy":
            trade_usd.append(usd)
            if p["qty"] > 1e-9:
                add_cnt += 1
                avg = p["cost"] / p["qty"]
                if px > avg * 1.02:
                    add_up += 1
                elif px < avg * 0.98:
                    add_down += 1
            elif p["sells"]:
                rebuy_after_sell += 1
            p["qty"] += amt
            p["cost"] += usd
            p["buys"].append({"t": r["timestamp"], "px": px, "usd": usd, "amt": amt})
        else:
            if p["qty"] > 1e-9:
                avg = p["cost"] / p["qty"]
                sell_amt = min(amt, p["qty"])
                p["realized"] += (px - avg) * sell_amt - 0.0
                p["qty"] -= sell_amt
                p["cost"] -= avg * sell_amt
            p["sells"].append({"t": r["timestamp"], "px": px, "usd": usd, "amt": amt})
    return per, {"add_cnt": add_cnt, "add_up": add_up, "add_down": add_down,
                 "rebuy": rebuy_after_sell, "trade_usd": trade_usd}


def fmt_ts(t):
    return datetime.fromtimestamp(t, CST).strftime("%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wallet", required=True)
    ap.add_argument("--chains", default="bsc,sol,robinhood")
    ap.add_argument("--cached", action="store_true", help="用上次抓取的缓存，不重新请求")
    ap.add_argument("--today", action="store_true", help="只看最近24小时并做违规提醒（静默模式）")
    a = ap.parse_args()
    all_rows = []
    if a.cached and os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            all_rows = json.load(f)
    else:
        for ch in [c.strip() for c in a.chains.split(",") if c.strip()]:
            rs = activities(a.wallet, ch, max_pages=1 if a.today else 4)
            for r in rs:
                r["_chain"] = ch
            all_rows.extend(rs)
        if not a.today:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE, "w", encoding="utf-8") as f:
                json.dump(all_rows, f)
    if not a.today:
        print("抓到 %d 条交易 | %s → %s\n" % (
            len(all_rows),
            fmt_ts(min(r["timestamp"] for r in all_rows)) if all_rows else "-",
            fmt_ts(max(r["timestamp"] for r in all_rows)) if all_rows else "-"))

    if a.today:
        import time as _t
        cut = int(_t.time()) - 86400
        day = sorted([r for r in all_rows if r["timestamp"] >= cut],
                     key=lambda r: r["timestamp"])
        if not day:
            return
        qty, cost, syms = {}, {}, {}
        flags = []
        for r in day:
            ad = r["token"]["address"]
            syms[ad] = r["token"].get("symbol") or "?"
            amt = float(r.get("token_amount") or 0)
            usd = float(r.get("cost_usd") or 0)
            px = float(r.get("price_usd") or 0)
            if r["event_type"] == "buy":
                if qty.get(ad, 0) > 1e-9:
                    avg = cost[ad] / qty[ad]
                    if px < avg * 0.98:
                        flags.append("⚠️ 补跌加仓 %s 价低于均价 %.0f%%（$%.2f）"
                                     % (syms[ad], (px / avg - 1) * 100, usd))
                qty[ad] = qty.get(ad, 0) + amt
                cost[ad] = cost.get(ad, 0) + usd
                if usd < 5:
                    flags.append("🔸 小额交易 %s 仅 $%.2f（手续费吃掉）" % (syms[ad], usd))
            elif qty.get(ad, 0) > 1e-9:
                avg = cost[ad] / qty[ad]
                amt2 = min(amt, qty[ad])
                pnl = usd - avg * amt2
                qty[ad] -= amt2
                cost[ad] -= avg * amt2
                flags.append("📤 卖出 %s $%.2f（%s $%.2f）"
                             % (syms[ad], usd, "+" if pnl >= 0 else "", pnl))
        buys = sum(1 for r in day if r["event_type"] == "buy")
        print("今日交易 %d 笔（买 %d / 卖 %d）" % (len(day), buys, len(day) - buys))
        for f in flags[:12]:
            print("  " + f)
        return
    per, agg = analyze(all_rows)
    usd = agg["trade_usd"]
    if usd:
        print("== 单笔买入金额 ==")
        print("笔数 %d | 中位数 $%.2f | 均值 $%.2f | 最大 $%.2f | 标准差 $%.2f"
              % (len(usd), statistics.median(usd), statistics.mean(usd),
                 max(usd), statistics.pstdev(usd) if len(usd) > 1 else 0))
    print("\n== 加仓行为 ==")
    print("加仓 %d 次 → 追涨 %d 次 / 亏钱补仓 %d 次"
          % (agg["add_cnt"], agg["add_up"], agg["add_down"]))
    print("卖了又买回 %d 次" % agg["rebuy"])
    print("\n== 按币种（按买入金额排序）==")
    rows = []
    for addr, p in per.items():
        buy_usd = sum(b["usd"] for b in p["buys"])
        if not p["buys"]:
            continue
        hold = (p["sells"][-1]["t"] - p["buys"][0]["t"]) / 60 if p["sells"] else None
        rows.append((buy_usd, p["sym"], len(p["buys"]), len(p["sells"]),
                     p["realized"], hold, addr))
    rows.sort(reverse=True)
    for buy_usd, sym, nb, ns, rp, hold, addr in rows[:15]:
        print("%-10s 买%d笔 $%7.2f 卖%d笔 已实现 $%+7.2f 持仓 %s %s"
              % (sym[:10], nb, buy_usd, ns, rp,
                 ("%.0f分钟" % hold) if hold is not None and hold < 1440 else
                 ("%.1f天" % (hold / 1440) if hold else "未卖"),
                 addr[:10] + "…"))
    tot = sum(r[4] for r in rows)
    print("\n合计已实现盈亏: $%+.2f | 参与币种 %d" % (tot, len(rows)))

    # ---- 逐笔卖出结算：胜率、持仓时长分布、摩擦成本 ----
    rr = sorted(all_rows, key=lambda r: r["timestamp"])
    state = {}
    closed = []  # (pnl_usd, hold_sec, sym)
    for r in rr:
        a = r["token"]["address"]
        st = state.setdefault(a, {"qty": 0.0, "cost": 0.0, "first": None, "sym": "?"})
        st["sym"] = r["token"].get("symbol") or st["sym"]
        amt = float(r.get("token_amount") or 0)
        usd = float(r.get("cost_usd") or 0)
        if r["event_type"] == "buy":
            if st["first"] is None:
                st["first"] = r["timestamp"]
            st["qty"] += amt
            st["cost"] += usd
        elif st["qty"] > 1e-9:
            avg = st["cost"] / st["qty"]
            sell_amt = min(amt, st["qty"])
            pnl = usd - avg * sell_amt
            closed.append((pnl, r["timestamp"] - (st["first"] or r["timestamp"]), st["sym"]))
            st["qty"] -= sell_amt
            st["cost"] -= avg * sell_amt
            if st["qty"] <= 1e-9:
                st["first"] = None
    if closed:
        wins = [c for c in closed if c[0] > 0]
        losses = [c for c in closed if c[0] <= 0]
        print("\n== 卖出结算（%d 笔）== " % len(closed))
        print("盈利 %d 笔 / 亏损 %d 笔 | 胜率 %.0f%%"
              % (len(wins), len(losses), 100.0 * len(wins) / len(closed)))
        print("盈利合计 $%+.2f | 亏损合计 $%+.2f"
              % (sum(c[0] for c in wins), sum(c[0] for c in losses)))
        buckets = [("0-1分钟", 0, 60), ("1-10分钟", 60, 600), ("10分钟-1小时", 600, 3600),
                   ("1小时-1天", 3600, 86400), (">1天", 86400, 10 ** 9)]
        print("\n== 持仓时长分布 ==")
        for name, lo, hi in buckets:
            sel = [c for c in closed if lo <= c[1] < hi]
            if sel:
                print("%-12s %2d 笔 | 合计 $%+7.2f | 平均 $%+.2f"
                      % (name, len(sel), sum(c[0] for c in sel),
                         sum(c[0] for c in sel) / len(sel)))
        small = [c for c in closed if -5 <= c[0] < 0]
        print("\n单笔亏 $0-5 的有 %d 笔，合计亏 $%.2f ← 手续费+滑点摩擦"
              % (len(small), sum(c[0] for c in small)))
        big = sorted(closed, key=lambda c: c[0])[:3]
        print("最大三笔亏损: " + " | ".join("%s $%.2f" % (c[2], c[0]) for c in big))


if __name__ == "__main__":
    main()
