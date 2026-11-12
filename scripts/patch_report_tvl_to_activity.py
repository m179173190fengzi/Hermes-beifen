#!/usr/bin/env python3
"""把两条日报 prompt 里的「链上 TVL」段换成「链上活跃度（成交量+Fees）」。"""
import json
import os
import subprocess

HOME = os.path.expanduser("~")
JOBS = os.path.join(HOME, ".hermes/cron/jobs.json")
TARGETS = ["fa0df7d27b24", "b4468ed62c8e"]

OLD = """━━━ 💰 链上 TVL ━━━
🟢/🔴 SOL: $XB | 🟢/🔴 BSC: $YB
📊 结论: [一句话，含资金流向哪边]"""

NEW = """━━━ 💰 链上活跃度（24h）━━━
🟢/🔴 SOL: 成交 $X | Fees $Y
🟢/🔴 BSC: 成交 $X | Fees $Y
📊 结论: [一句话：哪条链更活跃、资金往哪边流；成交放大但 Fees 跟不上=刷量]"""

jobs = json.load(open(JOBS, encoding="utf-8"))
ok, fail = [], []
for job in jobs.get("jobs", []):
    jid = job.get("id")
    if jid not in TARGETS:
        continue
    p = job.get("prompt") or ""
    if OLD not in p:
        # 容错：老版本可能写的是 "链上 TVL"
        if "链上 TVL" not in p:
            fail.append("%s 没找到 TVL 段" % jid)
            continue
    p2 = p.replace(OLD, NEW)
    r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", p2],
                       capture_output=True, text=True, timeout=180)
    if r.returncode == 0 and "链上 TVL" not in p2:
        ok.append("%s 已改（%d字）" % (jid, len(p2)))
        open(os.path.join(HOME, ".hermes/cron/prompts/lean-report-v3.md"), "w",
             encoding="utf-8").write(p2)
    else:
        fail.append("%s 失败: %s" % (jid, (r.stderr or r.stdout)[-120:]))

for x in ok:
    print("  ✓", x)
for x in fail:
    print("  ✗", x)
