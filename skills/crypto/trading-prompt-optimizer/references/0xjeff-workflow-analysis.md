# 0xJeff 工作流分析 — 链上+社媒Alpha合成模式

来源：@0xJeff 2026-07-13推文 — 4个月Hermes实战心得

## 三条核心工作流

### 1. 每日分析师追踪 + 书签分类 + Alpha合成
```
cron追踪11+分析师(24h汇总带链接) → Discord推送
     +
书签自动三级分类(高/中/低) → 每日推送
     +
分析师输出 + 书签 + 周轮换外部源 → Top 10 Alpha合成
```
**外部源周轮换（防信息茧房）：**
周一: arxiv论文 → 周二: 对冲基金信 → 周三: 链上数据 → 周四: 衍生品 → 周五: 宏观

### 2. 链上取证（Onchain Forensics）
- 查代币持仓分布 → 追踪聪明钱买卖 → 链上+推特交叉验证
- **核心逻辑：**
  - 链上卖 + 推特喊涨 = 🚩 有问题
  - 推特冷 + 链上流入 = 🐋 有人偷建仓

### 3. 反馈循环（Champion Loop + Feedback Sweep）
每天给Agent输出质量打分 → 反馈改进行为 → 第二天用改进后的prompt

## 对你的适用

你已经完成了：
- ✅ trading-prompt-optimizer — 结构化prompt方法论
- ✅ cron合并为每日Alpha简报 — 链上+推特+TVL合成
- ❌ 分析师名单 — 当前只有5位（AIBullss/0xJeff/Ansem/Murad/Cobie）
- ❌ 书签分类 — 未实现
- ❌ 外部源周轮换 — 未实现
- ❌ 反馈循环 — Dojo已装但未跑

## 关键差异

| 维度 | 0xJeff | 你的现状 |
|------|--------|---------|
| X Premium | ✅ (x_search API) | ❌ (访客API，受限) |
| 付费工具 | Nansen/BlockRun/Cookie | GMGN免费版 |
| 外部记忆 | Hindsight | 无 |
| 分析师数量 | 11+ | 5 |
| 反馈循环 | 每天 | Dojo已装未跑 |
