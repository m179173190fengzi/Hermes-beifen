#!/usr/bin/env python3
"""BSC 硬过滤器告警（no_agent cron 用）。

逻辑：
  1. 跑 bsc_hard_filter.py --trending N --json
  2. 只挑「非股票镜像 + 非安全判死 + 评分 >= SCORE_MIN」的代币
  3. 去掉 12 小时内已经推过的（状态文件），避免同一币反复打扰
  4. 有货 → 打印纯文本告警（cron 直发 TG）；没货 → 不输出任何东西（静默）

no_agent 语义：stdout 为空 = 不发消息；非空 = 原样发送。所以静默必须真的 print nothing。
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FILTER = os.path.join(HERE, "bsc_hard_filter.py")
STATE = os.path.expanduser("~/.hermes/cron/state/bsc_filter_alert.json")
SCORE_MIN = int(os.environ.get("SCORE_MIN", "60"))  # 低于这条线不打扰（BSC 榜普遍 30-55 分）
TRENDING_N = 15
REALERT_HOURS = 12      # 同一个币多久内不重复推
PY = sys.executable or "python3"


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {"alerted": {}}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def main():
    now = int(time.time())
    try:
        p = subprocess.run([PY, FILTER, "--trending", str(TRENDING_N), "--json"],
                           capture_output=True, text=True, timeout=900)
        data = json.loads(p.stdout)
    except Exception as e:
        print("BSC过滤器执行失败: %s" % e, file=sys.stderr)
        return  # 出错不推送，避免误导

    st = load_state()
    alerted = st.get("alerted", {})
    fresh = []
    for r in data:
        if r.get("dead") or r.get("stockish") or r.get("verdict") == "NODATA":
            continue
        if r.get("score", 0) < SCORE_MIN:
            continue
        ca = r.get("ca", "")
        if not ca:
            continue
        if now - alerted.get(ca, 0) < REALERT_HOURS * 3600:
            continue
        fresh.append(r)

    if not fresh:
        return  # 静默

    fresh.sort(key=lambda x: x.get("score", 0), reverse=True)
    L = []
    L.append("🎯 BSC 打狗候选（硬过滤器评分 ≥%d）" % SCORE_MIN)
    L.append("⏰ %s" % time.strftime("%Y-%m-%d %H:%M"))
    L.append("")
    for r in fresh:
        alerted[r["ca"]] = now
        L.append("✅ %d分  %s  [%s]" % (r.get("score", 0), r.get("symbol", "?"),
                                       r.get("launchpad", "?")))
        L.append("   💵 MC $%.0f | 💧 LP $%.0f | 币龄%.1fh | 持币%d | 24h量$%.0f"
                 % (r.get("mc", 0), r.get("lp", 0), r.get("age_h", 0),
                    r.get("holders", 0), r.get("vol24", 0)))
        L.append("   👥 Top10 %.1f%% | dev发币%d次 | 聪明钱%d | KOL%d"
                 % (r.get("top10", 0) * 100, r.get("dev_launches", 0),
                    r.get("smart", 0), r.get("renowned", 0)))
        L.append("   🌐 官网%s 推特%s | 税%s"
                 % ("有" if r.get("site") else "无", "有" if r.get("twitter") else "无",
                    r.get("tax", "-")))
        if r.get("deductions"):
            L.append("   📉 扣分: %s"
                     % "; ".join("-%d %s" % (p, w) for p, w in r["deductions"]))
        if r.get("notes"):
            L.append("   📝 %s" % "; ".join(r["notes"]))
        L.append("   🔗 CA: %s" % r["ca"])
        L.append("   📏 单笔1-2%仓 | 止损-30~-40% | 2x卖50%回本 | 12-24h不涨撤")
        L.append("")

    # 清掉过期的记录
    st["alerted"] = {k: v for k, v in alerted.items() if now - v < 7 * 86400}
    save_state(st)
    L.append("⚠️ 机器筛选，非投资建议。分数高≠能赚钱，仍需自己看叙事和盘面。")
    print("\n".join(L))


if __name__ == "__main__":
    main()
