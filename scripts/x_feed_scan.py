#!/usr/bin/env python3
"""定时跑 x_watch.py --feed 的包装脚本（no_agent cron 用）。

cron 的 script 参数不支持传命令行参数，所以用这个壳。
"""
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
TARGET = os.path.join(HOME, ".hermes/scripts/x_watch.py")
PY = "/usr/bin/python3"

proc = subprocess.run([PY, TARGET, "--feed"],
                      capture_output=True, text=True, timeout=480)
out = (proc.stdout or "").strip()
if out:
    print(out)
elif proc.returncode != 0:
    print("⚠️ X 热议扫描失败 (rc=%d): %s" % (proc.returncode, (proc.stderr or "")[-200:]))
sys.exit(0)
