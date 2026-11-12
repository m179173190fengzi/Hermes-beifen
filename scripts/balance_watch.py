#!/usr/bin/env python3
"""DeepSeek 余额看门狗（no_agent cron 用，零 LLM 成本）。

规则：余额 < 阈值 就报警；否则完全静默（不打扰）。
      同一次"低余额"状态最多每 RE_ALERT_HOURS 小时提醒一次，避免刷屏。

用法：
  python3 balance_watch.py          # 正常跑（cron 用）
  python3 balance_watch.py --test   # 无视静默/去重，强制打印当前状态
"""
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
ENV = os.path.join(HOME, ".hermes/.env")
STATE = os.path.join(HOME, ".hermes/cron/state/balance_watch.json")
PROXY = "http://127.0.0.1:7890"

THRESHOLD = 1.0        # 低于这个余额就提醒（CNY）
RE_ALERT_HOURS = 12    # 持续低余额时的重复提醒间隔
CRITICAL = 0.5         # 更低一档，措辞升级


def api_key(name):
    try:
        for line in open(ENV, encoding="utf-8"):
            m = re.match(r"\s*%s=(.*)" % re.escape(name), line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def balance():
    key = api_key("DEEPSEEK_API_KEY")
    if not key:
        return None, None, "未找到 DEEPSEEK_API_KEY"
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", "20", "-H", "Authorization: Bearer " + key,
             "https://api.deepseek.com/user/balance"],
            capture_output=True, text=True, timeout=40, env=env).stdout
        j = json.loads(out)
        if not j.get("balance_infos"):
            return None, None, "接口返回无余额信息"
        info = j["balance_infos"][0]
        return float(info.get("total_balance") or 0), info.get("currency") or "CNY", None
    except Exception as exc:  # noqa: BLE001
        return None, None, "查询失败: %s" % str(exc)[:80]


def main():
    force = "--test" in sys.argv
    bal, cur, err = balance()
    sym = "¥" if (cur or "CNY") == "CNY" else "$"

    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}

    if bal is None:
        if force:
            print("⚠️ DeepSeek 余额查询失败：%s" % err)
        return 0

    if bal >= THRESHOLD and not force:
        return 0  # 余额充足 → 静默

    last = state.get("last_alert_ts", 0)
    if not force and time.time() - last < RE_ALERT_HOURS * 3600:
        return 0  # 已提醒过，没到重复提醒时间

    tag = "（--test 强制显示；实际余额高于阈值，正式运行时不会打扰）" if (force and bal >= THRESHOLD) else ""
    if bal < CRITICAL:
        print("🔴 DeepSeek 余额仅剩 %s%.2f —— 即将耗尽，请立即充值！%s\n"
              "（余额归零后所有 cron 日报/X监控/链上扫描会全部失败）" % (sym, bal, tag))
    else:
        print("⚠️ DeepSeek 余额剩 %s%.2f —— 低于 %s%.0f，建议尽快充值。%s\n"
              "（余额耗尽后 cron 日报/X监控会停止工作）" % (sym, bal, sym, THRESHOLD, tag))

    state["last_alert_ts"] = time.time()
    state["balance"] = bal
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
