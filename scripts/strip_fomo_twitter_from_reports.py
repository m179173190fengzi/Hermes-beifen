#!/usr/bin/env python3
"""从四条日报 prompt 中移除「fomo 热门币」和「推特热议」两块。

处理内容：
  - 工具清单里的 fomo_top5.py / x_hot_brief.py 两行
  - 代理说明里提到这两个脚本的一句
  - Workflow 里第 1、2 步（并重新编号）
  - Output Format 里的两个 {把 ... 粘贴} 块
  - 描述行、Risk Rule 5、CA 例外说明里的相关措辞
"""
import json
import re
import subprocess
import sys

JOBS = "/home/wei/.hermes/cron/jobs.json"
TARGETS = ["fa0df7d27b24", "2d1bbc759615", "b4468ed62c8e", "73d94b781435"]


def clean(prompt):
    lines = prompt.split("\n")
    out, skip_block, in_workflow = [], False, False
    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            in_workflow = s.startswith("## Workflow")
        # 工具清单两行
        if s.startswith("- **`") and ("fomo_top5.py" in s or "x_hot_brief.py" in s):
            continue
        # 代理说明那行
        if s.startswith("fomo_top5.py 和 x_hot_brief.py"):
            continue
        # Workflow 前两步
        if s.startswith("1. **跑 `python3 /home/wei/.hermes/scripts/fomo_top5.py`"):
            continue
        if s.startswith("2. **跑 `python3 /home/wei/.hermes/scripts/x_hot_brief.py`"):
            continue
        # 输出块：{把 `fomo_top5.py` ... }（多行）
        if s.startswith("{把 `fomo_top5.py`"):
            skip_block = True
            continue
        if skip_block:
            if s.endswith("}"):
                skip_block = False
            continue
        # 输出块：{把 `x_hot_brief.py` ... }（单行）
        if s.startswith("{把 `x_hot_brief.py`"):
            continue
        out.append(ln)

    text = "\n".join(out)

    # 措辞清理
    text = text.replace(
        "（链上扫描/TVL资金流/新币监控/fomo热门榜/推特热议/11项评分）",
        "（链上扫描/TVL资金流/新币监控/11项评分）")
    text = text.replace(
        "**其余段落（fomo榜/推特热议/新币/TVL/叙事）照常输出推送**",
        "**其余段落（新币/TVL/叙事）照常输出推送**")
    text = text.replace(
        "⚠️ 每个代币条目必须带完整CA（`🔗 CA: \\`...\\``）+ 叙事。**fomo段和推特热议段（脚本输出）例外，保持脚本原样**。",
        "⚠️ 每个代币条目必须带完整CA（`🔗 CA: \\`...\\``）+ 叙事。")

    # Workflow 重新编号
    lines2, in_wf, n = [], False, 0
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("## "):
            in_wf = s.startswith("## Workflow")
            lines2.append(ln)
            continue
        if in_wf and re.match(r"^\d+\.\s", s):
            n += 1
            lines2.append(re.sub(r"^\d+\.", "%d." % n, ln, count=1))
            continue
        lines2.append(ln)
    text = "\n".join(lines2)

    # 压缩连续空行（输出块删掉后可能留 2-3 个空行）
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def main():
    jobs = json.load(open(JOBS, encoding="utf-8"))
    ok, fail, skip = [], [], []
    for job in jobs.get("jobs", []):
        jid = job.get("id")
        if jid not in TARGETS:
            continue
        p = job.get("prompt") or ""
        if "fomo_top5.py" not in p and "x_hot_brief.py" not in p:
            skip.append("%s 已无相关内容" % jid)
            continue
        np = clean(p)
        r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", np],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            ok.append("%s 已清理（%d→%d 字）" % (jid, len(p), len(np)))
        else:
            fail.append("%s 失败: %s" % (jid, (r.stderr or r.stdout)[-140:]))
    for x in ok:
        print("  ✓", x)
    for x in skip:
        print("  -", x)
    for x in fail:
        print("  ✗", x)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
