#!/usr/bin/env python3
"""给四条日报加「角度先行」：叙事段必须给 角度词 + 最贴合标的。

改动：
  1) 阶段2 增加一条铁律：先提炼角度词，再找盘（禁止先列标的后编叙事）
  2) 输出模板的【核心叙事】块加入 🔑 角度词 / 🎯 最贴合标的
"""
import json
import subprocess
import sys

JOBS = "/home/wei/.hermes/cron/jobs.json"
TARGETS = ["fa0df7d27b24", "2d1bbc759615", "b4468ed62c8e", "73d94b781435"]

OLD_RULE = "- 分别聚类 BSC 和 SOL 上的热点叙事（中文meme/名人/动物/政治/科技/机构等）"
NEW_RULE = ("- 分别聚类 BSC 和 SOL 上的热点叙事（中文meme/名人/动物/政治/科技/机构等）\n"
            "- **🔑 角度先行（铁律）**：先从这波热点里提炼出「一个角度词」——必须是能直接当 ticker / 图片梗用的"
            "那个词（如 FTR 那波的「翻车/能飞/roadster」），**再去找哪个盘最贴合它**。"
            "禁止先列标的后编叙事（顺序反了就是自欺）。")

OLD_BLOCK = ("- [热点簇描述]\n"
             "- 🔗 跨链对照: [SOL 侧 ↔ BSC 侧 对应标的与强弱对比；无镜像就写\"今日无强跨链镜像\"]\n"
             "- 🐋 资金流向: [净买盘/资金流入判断]")
NEW_BLOCK = ("- [热点簇描述]\n"
             "- 🔑 角度词: [从这波热度提炼出的那一个词——最好能直接当 ticker/图片梗用，不是泛泛主题词]\n"
             "- 🎯 最贴合标的: [按「贴合角度词 + 台子正确 + 图片梗对 + 结构干净」排序 1-2 个；"
             "每个给 symbol + `CA` + 一句贴合理由]\n"
             "- 🔗 跨链对照: [SOL 侧 ↔ BSC 侧 对应标的与强弱对比；无镜像就写\"今日无强跨链镜像\"]\n"
             "- 🐋 资金流向: [净买盘/资金流入判断]")

ok, skip, fail = [], [], []
jobs = json.load(open(JOBS, encoding="utf-8"))
for job in jobs.get("jobs", []):
    jid = job.get("id")
    if jid not in TARGETS:
        continue
    p = job.get("prompt") or ""
    if "🔑 角度先行" in p:
        skip.append("%s 已有角度先行" % jid)
        continue
    if OLD_RULE not in p or OLD_BLOCK not in p:
        fail.append("%s 锚点未找到" % jid)
        continue
    np = p.replace(OLD_RULE, NEW_RULE, 1).replace(OLD_BLOCK, NEW_BLOCK, 1)
    r = subprocess.run(["hermes", "cron", "edit", jid, "--prompt", np],
                       capture_output=True, text=True, timeout=120)
    (ok if r.returncode == 0 else fail).append(
        "%s 已更新" % jid if r.returncode == 0
        else "%s 失败: %s" % (jid, (r.stderr or r.stdout)[-120:]))

for x in ok:
    print("  ✓", x)
for x in skip:
    print("  -", x)
for x in fail:
    print("  ✗", x)
sys.exit(1 if fail else 0)
