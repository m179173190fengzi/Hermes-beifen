# Hermes社区生态工具（2026-07更新）

本session新安装/了解的工具汇总：

## 已安装 ✅

| 工具 | ⭐ | 安装方式 | 用途 |
|:----|:--:|---------|:-----|
| **Workspace** | 6,050 | git clone + pnpm install → :3000 | Web指挥中心 |
| **Super Hermes** | 307 | `bash install.sh` → 5个棱镜技能+7个prism | 元推理层 |
| **Dojo** | 117 | `bash install.sh` → 可对话Skill | 自改进道场 |
| **女娲 (Nuwa)** | 27,600 | `npx skills add` + 手动cp到skills目录 | 人物蒸馏 |
| **0xSun-perspective** | 自制 | 女娲蒸馏 | 孙哥链上交易视角 |
| **冷静冷静在冷静-perspective** | 自制 | 女娲蒸馏 | 车头meme视角 |

## 已知但未装 📦

| 工具 | ⭐ | 待评估 |
|:----|:--:|:-------|
| Oh My Hermes (OMH) | 105 | multi-agent编排，deep-research有用 |
| Dashboard | — | 模块缺失(`dashboard_auth`不存在)，等升级 |
| Skill Marketplace | 42 | 等技能数量多了再考虑 |
| Achievements | 42 | 纯玩法，和交易无关 |
| Blacktea | 5 | Agent花钱管控，不需要 |

## 各工具调用命令速查

```bash
# Workspace
cd ~/hermes-workspace && node server-entry.js  # :3000

# Super Hermes (在Hermes对话中用斜杠)
/prism-scan      # 单次分析
/prism-full      # 多轮分析+自修正
/prism-3way      # WHERE/WHEN/WHY正交
/prism-reflect   # 自感知分析+遗漏报告

# Dojo (在Hermes对话中)
/dojo analyze    # 运行分析

# 女娲 (加载skill后)
skill_view name=huashu-nuwa
# 然后说: 蒸馏 @用户名

# 已蒸馏Skill (直接加载)
skill_view name=0xsun-perspective
skill_view name=lengjinglengjing-perspective
```

## 蒸馏crypto KOL的注意事项

1. **用快速档** — 币圈KOL主要产出是推文+短thread，不是书籍/论文
2. **不要用完整6-agent** — 容易超时(10min+)，且大部分agent搜不到有价值内容
3. **手动构建更快** — `twitter search from:用户名 -n 20` 获取推文→手工提炼3-5个心智模型→写SKILL.md
4. **必须加L5诚实边界** — 标注"基于有限公开信息蒸馏，非本人真实思维全貌"
5. **推文有策略性** — KOL可能藏仓/喊单/控盘，Skill无法分辨哪些是真心话哪些是套
