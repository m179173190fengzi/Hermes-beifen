#!/usr/bin/env python3
"""日报 prompt：链只留 SOL/BSC/RH；GMGN 收入改近3日对比。"""
import json
import os
import subprocess

HOME = os.path.expanduser("~")
JOBS = os.path.join(HOME, ".hermes/cron/jobs.json")
TARGETS = ["fa0df7d27b24", "b4468ed62c8e"]

OLD = ("[原样照抄脚本输出的 TOP5 五行：排名 / 链 / 24h成交 / 变化% / Fees / 量费比]\n"
       "[原样照抄紧跟其后的 GMGN 收入那一行（24h/7d/日均/7日趋势）——这是打狗活跃度温度计]")
NEW = ("[原样照抄脚本输出的 SOL / BSC / RH 三行：成交 / 变化% / Fees / 量费比]\n"
       "[原样照抄紧跟其后的 GMGN 收入那一行（近3日逐日 + 3日变化 + 7日趋势）——打狗活跃度温度计]")

jobs = json.load(open(JOBS, encoding="utf-8"))
for job in jobs.get("jobs", []):
    jid = job.get("id")
    if jid not in TARGETS:
        continue
    p = job.get("prompt") or ""
    if OLD not in p:
        print("  ✗ %s 未匹配" % jid)
        continue
    p2 = p.replace(OLD, NEW)
    r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", p2],
                       capture_output=True, text=True, timeout=180)
    print("  %s %s（%d字）" % ("✓" if r.returncode == 0 else "✗", jid, len(p2)))
    if r.returncode == 0:
        open(os.path.join(HOME, ".hermes/cron/prompts/lean-report-v6.md"), "w",
             encoding="utf-8").write(p2)
