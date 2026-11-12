#!/usr/bin/env python3
"""新建 23:00 的 BSC+SOL 链上日报：直接复用 5:40 那条的 prompt 与技能集。"""
import json
import subprocess
import sys

JOBS = "/home/wei/.hermes/cron/jobs.json"
SOURCE = "fa0df7d27b24"          # 复制源
NEW_NAME = "BSC+SOL链上日报(23:00)"
SCHEDULE = "0 23 * * *"


def main():
    jobs = json.load(open(JOBS, encoding="utf-8"))
    src = next((j for j in jobs.get("jobs", []) if j.get("id") == SOURCE), None)
    if not src:
        print("找不到源任务", SOURCE)
        return 1

    # 已存在同名任务就不重复建
    for j in jobs.get("jobs", []):
        if j.get("name") == NEW_NAME:
            print("已存在同名任务 %s (%s)，跳过" % (NEW_NAME, j.get("id")))
            return 0

    prompt = src.get("prompt") or ""
    skills = src.get("skills") or []
    cmd = ["hermes", "cron", "create", SCHEDULE, prompt,
           "--name", NEW_NAME, "--deliver", src.get("deliver") or "origin"]
    for s in skills:
        cmd += ["--skill", s]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = (r.stdout or "") + (r.stderr or "")
    print("rc=%d" % r.returncode)
    print(out[-600:])
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
