#!/usr/bin/env python3
"""日报 prompt：链上活跃度段改为照抄 TOP5 链排行榜。"""
import json
import os
import subprocess

HOME = os.path.expanduser("~")
JOBS = os.path.join(HOME, ".hermes/cron/jobs.json")
TARGETS = ["fa0df7d27b24", "b4468ed62c8e"]

OLD = """━━━ 💰 链上活跃度（24h）━━━
🟢/🔴 SOL: 成交 $X | Fees $Y
🟢/🔴 BSC: 成交 $X | Fees $Y
📊 结论: [一句话：哪条链更活跃、资金往哪边流；成交放大但 Fees 跟不上=刷量]"""

NEW = """━━━ 💰 链上活跃度（24h）━━━
[原样照抄脚本输出的 TOP5 五行：排名 / 链 / 24h成交 / 变化% / Fees / 量费比]
📊 结论: [一句话：资金往哪条链流；量/费比高=费率低或刷量，低=真实需求強]"""

jobs = json.load(open(JOBS, encoding="utf-8"))
for job in jobs.get("jobs", []):
    jid = job.get("id")
    if jid not in TARGETS:
        continue
    p = job.get("prompt") or ""
    if OLD not in p:
        print("  ✗ %s 未匹配到旧段落" % jid)
        continue
    p2 = p.replace(OLD, NEW)
    r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", p2],
                       capture_output=True, text=True, timeout=180)
    if r.returncode == 0:
        open(os.path.join(HOME, ".hermes/cron/prompts/lean-report-v4.md"), "w",
             encoding="utf-8").write(p2)
        print("  ✓ %s 已改（%d字）" % (jid, len(p2)))
    else:
        print("  ✗ %s %s" % (jid, (r.stderr or r.stdout)[-120:]))
