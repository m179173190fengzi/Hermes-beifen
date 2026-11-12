#!/usr/bin/env python3
"""把两条在跑的日报换成瘦身版 prompt（daily_scan.py 预消化）。

先备份旧 prompt 到 ~/.hermes/cron/prompts/backup-<jid>-<日期>.md，
再用 hermes cron edit 写入 lean-report-v2.md。
"""
import json
import os
import subprocess
import sys
from datetime import datetime

HOME = os.path.expanduser("~")
JOBS = os.path.join(HOME, ".hermes/cron/jobs.json")
NEW_PROMPT = os.path.join(HOME, ".hermes/cron/prompts/lean-report-v2.md")
TARGETS = ["fa0df7d27b24", "b4468ed62c8e"]   # 5:40 和 19:00（其余已暂停）
STAMP = datetime.now().strftime("%Y%m%d")

prompt = open(NEW_PROMPT, encoding="utf-8").read()
jobs = json.load(open(JOBS, encoding="utf-8"))

ok, fail = [], []
for job in jobs.get("jobs", []):
    jid = job.get("id")
    if jid not in TARGETS:
        continue
    old = job.get("prompt") or ""
    bak = os.path.join(HOME, ".hermes/cron/prompts/backup-%s-%s.md" % (jid, STAMP))
    with open(bak, "w", encoding="utf-8") as f:
        f.write(old)
    r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", prompt],
                       capture_output=True, text=True, timeout=180)
    if r.returncode == 0:
        ok.append("%s 已换瘦身版（%d→%d 字，备份 %s）" % (jid, len(old), len(prompt), os.path.basename(bak)))
    else:
        fail.append("%s 失败: %s" % (jid, (r.stderr or r.stdout)[-150:]))

for x in ok:
    print("  ✓", x)
for x in fail:
    print("  ✗", x)
sys.exit(1 if fail else 0)
