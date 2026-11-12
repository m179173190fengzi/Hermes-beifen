#!/usr/bin/env python3
"""批量给三条日报的 prompt 加上「fomo 热门币要补一行叙事」的要求。

做法：读 jobs.json 取当前 prompt → 做一次精确替换 → 用 hermes cron edit 写回。
这样不用把整份长 prompt 重新过一遍上下文。
"""
import json
import shlex
import subprocess
import sys

JOBS = "/home/wei/.hermes/cron/jobs.json"
TARGETS = ["fa0df7d27b24", "2d1bbc759615", "b4468ed62c8e"]

OLD = ("{把 `fomo_top5.py` 的输出**原样整段粘贴**，它自带「━━━ 🔥 fomo 热门代币 TOP5 ━━━」标题；"
       "末尾加一行 📊 解读：这5个里有没有 SOL/BSC 链的、与当前叙事的呼应（一句话，没有就写\"与当前热点无直接呼应\"）}")

NEW = ("{把 `fomo_top5.py` 的输出整段粘贴（自带「━━━ 🔥 fomo 热门代币 TOP5 ━━━」标题），"
       "**并在每个代币条目下补一行叙事**：\n"
       "     📖 叙事: [一句话说清这币讲的是什么故事/梗/事件]\n"
       "（依据脚本给的「📖 素材」（名称/推特/官网/发射台）+ 当日 X 热议与新闻上下文推断；"
       "推不出来就写\"名称即叙事：<名称>\"，**绝对不要编造**；素材里标了\"非常规账号\"说明社交字段是伪装链接，"
       "不要当成真实推特账号输出）\n"
       "末尾加一行 📊 解读：这5个里有没有与当日热点/跨链对照的呼应（一句话，没有就写\"与当前热点无直接呼应\"）}")


def main():
    jobs = json.load(open(JOBS, encoding="utf-8"))
    ok, fail = [], []
    for job in jobs.get("jobs", []):
        jid = job.get("id")
        if jid not in TARGETS:
            continue
        prompt = job.get("prompt") or ""
        if NEW[:40] in prompt:
            ok.append("%s 已是新版，跳过" % jid)
            continue
        if OLD not in prompt:
            fail.append("%s 未找到待替换段落（prompt 可能已变）" % jid)
            continue
        new_prompt = prompt.replace(OLD, NEW)
        r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", new_prompt],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            ok.append("%s 已更新" % jid)
        else:
            fail.append("%s 失败: %s" % (jid, (r.stderr or r.stdout)[-160:]))
    print("成功:")
    for x in ok:
        print("  ✓", x)
    if fail:
        print("失败:")
        for x in fail:
            print("  ✗", x)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
