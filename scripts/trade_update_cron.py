#!/usr/bin/env python3
"""cron 包装：刷新未平仓交易（算 1h/6h/24h 标记、当前浮盈，跌破 -20% 告警）。
无异常时完全静默（no_agent cron 的静默语义）。"""
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
TARGET = os.path.join(HOME, ".hermes/scripts/trade_log.py")
out = subprocess.run(["/usr/bin/python3", TARGET, "update"],
                     capture_output=True, text=True, timeout=600).stdout.strip()
if out:
    print(out)
sys.exit(0)
