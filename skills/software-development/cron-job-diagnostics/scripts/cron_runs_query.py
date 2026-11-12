#!/usr/bin/env python3
"""查询 Hermes cron 执行库：某任务最近若干次运行的状态、起止时间与错误。

为什么需要它：机器上通常没有 sqlite3 CLI，而 `cronjob list` 只给一个
`last_status`，看不到失败原因、也分不清"还在跑"和"跑挂了"。

用法：
    python3 cron_runs_query.py <job_id> [N]     # N 默认 5
    python3 cron_runs_query.py                 # 全部任务最近 8 条

判读：
    status=running 且 end 为空  → 还在跑（别重复触发）
    status=failed/completed + err 非空 → 看 err 文本（402=余额、401=凭据）
"""
import os
import sqlite3
import sys

DB = os.path.expanduser("~/.hermes/cron/executions.db")


def main():
    job = sys.argv[1] if len(sys.argv) > 1 else None
    n = int(sys.argv[2]) if len(sys.argv) > 2 else (5 if job else 8)

    if not os.path.exists(DB):
        print("找不到执行库：%s" % DB)
        return 1

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cols = [r[1] for r in cur.execute("PRAGMA table_info(executions)")]
    if not cols:
        print("执行库为空或表结构不同：%s" % DB)
        return 1
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
        finished = str(d.get("finished_at") or "")[:19] or "(未结束)"
        err = (d.get("error") or "").replace("\n", " ")[:160] if has_err else ""
        print("%-28s %-10s start=%s end=%s" % (d.get("job_id"), d.get("status"),
                                               started, finished))
        if err:
            print("    err: %s" % err)
    return 0


if __name__ == "__main__":
    sys.exit(main())
