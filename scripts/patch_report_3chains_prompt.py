#!/usr/bin/env python3
"""早报 prompt：双链 -> 三链（BSC/SOL/RH）。"""
import json
import os
import subprocess

HOME = os.path.expanduser("~")
JOBS = os.path.join(HOME, ".hermes/cron/jobs.json")
JOB = "fa0df7d27b24"

REPL = [
    ("双链 trenches 扫描", "三链 trenches 扫描（BSC/SOL/RH）"),
    ("- 🔗 跨链对照: [SOL ↔ BSC 对应标的强弱",
     "- 🔗 跨链对照: [SOL ↔ BSC ↔ RH 对应标的强弱"),
    ("若两链都无过线标的", "若三链都无过线标的"),
]


def main():
    with open(JOBS, encoding="utf-8") as f:
        data = json.load(f)
    jobs = data["jobs"] if isinstance(data, dict) else data
    job = next(j for j in jobs if j["id"] == JOB)
    p = job["prompt"]
    for old, new in REPL:
        if old in p:
            p = p.replace(old, new)
            print("✓ 替换:", old[:18])
        else:
            print("✗ 未找到:", old[:18])
    with open("/tmp/prompt_new.md", "w", encoding="utf-8") as f:
        f.write(p)
    r = subprocess.run(["hermes", "cron", "edit", JOB, "--prompt", p],
                       capture_output=True, text=True)
    print("edit exit:", r.returncode, (r.stdout or r.stderr)[-120:])


if __name__ == "__main__":
    main()
