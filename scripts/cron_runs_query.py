#!/usr/bin/env python3
"""查询 cron 执行库：某任务最近若干次运行的状态与错误。"""
import os
import sqlite3
import sys

DB = os.path.expanduser("~/.hermes/cron/executions.db")
job = sys.argv[1] if len(sys.argv) > 1 else None
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()
cols = [r[1] for r in cur.execute("PRAGMA table_info(executions)")]
has_err = "error" in cols

q = "select * from executions"
args = ()
if job:
    q += " where job_id=?"
    args = (job,)
q += " order by started_at desc limit %d" % n

for row in cur.execute(q, args):
    d = dict(row)
    started = str(d.get("started_at") or "")[:19]
    finished = str(d.get("finished_at") or "")[:19]
    err = (d.get("error") or "")[:120].replace("\n", " ") if has_err else ""
    print("%-12s %-10s start=%s end=%s" % (d.get("job_id"), d.get("status"), started, finished))
    if err:
        print("   err: %s" % err)
