#!/usr/bin/env python3
"""Token 消耗日报（一句话版，no_agent cron 用）。

输出格式：💰 今日消耗 ¥X.XX ｜ 用量 N.NM tokens ｜ 余额 ¥Y.YY

数据来源：
  * 当日用量   → `hermes insights --days 1`（解析 Total tokens）
  * 当日消耗   → DeepSeek 余额接口的【两次运行差值】（真正扣掉的钱，含缓存等所有计费）
  * 剩余余额   → https://api.deepseek.com/user/balance （CNY）
"""
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
ENV = os.path.join(HOME, ".hermes/.env")
STATE = os.path.join(HOME, ".hermes/cron/state/token_daily.json")
PROXY = "http://127.0.0.1:7890"


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
        return None, None
    env = dict(os.environ, HTTPS_PROXY=PROXY, HTTP_PROXY=PROXY)
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", "20", "-H", "Authorization: Bearer " + key,
             "https://api.deepseek.com/user/balance"],
            capture_output=True, text=True, timeout=40, env=env).stdout
        j = json.loads(out)
        info = (j.get("balance_infos") or [{}])[0]
        return float(info.get("total_balance") or 0), info.get("currency") or "CNY"
    except Exception:  # noqa: BLE001
        return None, None


def tokens_today():
    try:
        out = subprocess.run(["hermes", "insights", "--days", "1"],
                             capture_output=True, text=True, timeout=180).stdout
    except Exception:  # noqa: BLE001
        return None, None
    total = re.search(r"Total tokens:\s*([\d,]+)", out)
    msgs = re.search(r"Messages:\s*([\d,]+)", out)
    return (int(total.group(1).replace(",", "")) if total else None,
            int(msgs.group(1).replace(",", "")) if msgs else None)


def human(n):
    if n is None:
        return "?"
    if n >= 1_000_000:
        return "%.2fM" % (n / 1_000_000)
    if n >= 1_000:
        return "%.1fK" % (n / 1_000)
    return str(n)


def main():
    bal, cur = balance()
    tok, msgs = tokens_today()
    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}
    prev = state.get("balance")
    sym = "¥" if (cur or "CNY") == "CNY" else "$"

    parts = []
    if bal is None:
        parts.append("余额: 查询失败")
    elif prev is None:
        parts.append("余额 %s%.2f" % (sym, bal))
    else:
        delta = round(prev - bal, 2)
        if delta >= 0:
            parts.append("今日消耗 %s%.2f" % (sym, delta))
        else:
            parts.append("今日充值 %s%.2f（余额 %s%.2f）" % (sym, -delta, sym, bal))
    parts.append("用量 %s tokens" % human(tok))
    if msgs:
        parts.append("%d 条消息" % msgs)
    if prev is None and bal is not None:
        parts.append("（首次运行，明日开始显示当日消耗）")

    print("💰 " + " ｜ ".join(parts))

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump({"balance": bal, "ts": time.time(), "date": time.strftime("%Y-%m-%d")},
              open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
