#!/usr/bin/env python3
"""从四条日报 prompt 里删掉代币条目中的「🐦 [x.com链接或关联推特]」行。

保留 11 项评分里的社交相关标准（那是用户自己的评分体系）。
"""
import json
import re
import subprocess
import sys

JOBS = "/home/wei/.hermes/cron/jobs.json"
TARGETS = ["fa0df7d27b24", "2d1bbc759615", "b4468ed62c8e", "73d94b781435"]
PAT = re.compile(r"^🐦\s*\[x\.com链接或关联推特\]\s*$", re.M)

ok, skip, fail = [], [], []
jobs = json.load(open(JOBS, encoding="utf-8"))
for job in jobs.get("jobs", []):
    jid = job.get("id")
    if jid not in TARGETS:
        continue
    p = job.get("prompt") or ""
    if not PAT.search(p):
        skip.append("%s 已无该行" % jid)
        continue
    np = PAT.sub("", p)
    np = re.sub(r"\n{3,}", "\n\n", np)
    r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", np],
                       capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        ok.append("%s 已删除推特链接行" % jid)
    else:
        fail.append("%s 失败: %s" % (jid, (r.stderr or r.stdout)[-120:]))

for x in ok:
    print("  ✓", x)
for x in skip:
    print("  -", x)
for x in fail:
    print("  ✗", x)
sys.exit(1 if fail else 0)
