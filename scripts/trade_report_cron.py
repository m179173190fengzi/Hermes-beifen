#!/usr/bin/env python3
"""cron 包装：交易周报（胜率/期望值/特征归因/纪律检查）。"""
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
TARGET = os.path.join(HOME, ".hermes/scripts/trade_log.py")
out = subprocess.run(["/usr/bin/python3", TARGET, "report", "--days", "30"],
                     capture_output=True, text=True, timeout=300).stdout.strip()
if out:
    print(out)
sys.exit(0)
