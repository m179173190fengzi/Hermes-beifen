#!/usr/bin/env python3
"""看某次 cron 运行的 token 用量（执行库里若有记录）。"""
import os
import sqlite3
import sys

DB = os.path.expanduser("~/.hermes/cron/executions.db")
job = sys.argv[1] if len(sys.argv) > 1 else "fa0df7d27b24"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()
cols = [r[1] for r in cur.execute("PRAGMA table_info(executions)")]
tok_cols = [c for c in cols if "token" in c.lower() or "usage" in c.lower() or "cost" in c.lower()]
print("token 相关列:", tok_cols or "（无）")
sel = ", ".join(["started_at", "status"] + tok_cols) if tok_cols else "started_at, status"
q = "select %s from executions where job_id=? order by started_at desc limit %d" % (sel, n)
for row in cur.execute(q, (job,)):
    d = dict(row)
    print(" | ".join("%s=%s" % (k, d.get(k)) for k in d))
