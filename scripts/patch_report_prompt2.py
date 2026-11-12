#!/usr/bin/env python3
"""给三条日报的 prompt 追加「小黄人(Unipcs)最新买入」段的叙事要求。

在前一次替换的基础上再做一次精确替换：
  旧锚点：「自带「━━━ 🔥 fomo 热门代币 TOP5 ━━━」标题）
  新内容：补充说明脚本还会输出「🐤 小黄人最新买入」子段，并要求一并补叙事 + 标注它是参考信号不是推荐。
"""
import json
import subprocess
import sys

JOBS = "/home/wei/.hermes/cron/jobs.json"
TARGETS = ["fa0df7d27b24", "2d1bbc759615", "b4468ed62c8e"]

OLD = "自带「━━━ 🔥 fomo 热门代币 TOP5 ━━━」标题）"
NEW = ("自带「━━━ 🔥 fomo 热门代币 TOP5 ━━━」标题，以及「🐤 小黄人(Unipcs·fomo盈利榜#1) 最新买入」子段"
       "——后者是盈利榜第一名的链上买入记录，属于**参考信号**，要如实输出但注明不是推荐）")

OLD2 = '末尾加一行 📊 解读：这5个里有没有与当日热点/跨链对照的呼应（一句话，没有就写"与当前热点无直接呼应"）}'
NEW2 = ('末尾加一行 📊 解读：这些标的（含小黄人买入）与当日热点/跨链对照有无呼应'
        '（一句话，没有就写"与当前热点无直接呼应"）}')


def main():
    jobs = json.load(open(JOBS, encoding="utf-8"))
    ok, fail = [], []
    for job in jobs.get("jobs", []):
        jid = job.get("id")
        if jid not in TARGETS:
            continue
        p = job.get("prompt") or ""
        if "🐤 小黄人" in p:
            ok.append("%s 已含小黄人说明，跳过" % jid)
            continue
        if OLD not in p:
            fail.append("%s 未找到锚点1" % jid)
            continue
        np = p.replace(OLD, NEW, 1)
        np = np.replace(OLD2, NEW2, 1)
        r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", np],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            ok.append("%s 已更新" % jid)
        else:
            fail.append("%s 失败: %s" % (jid, (r.stderr or r.stdout)[-140:]))
    for x in ok:
        print("  ✓", x)
    for x in fail:
        print("  ✗", x)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
