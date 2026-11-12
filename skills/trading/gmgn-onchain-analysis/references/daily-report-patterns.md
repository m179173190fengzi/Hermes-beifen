# 链上日报模式参考

本文件记录从开源项目学到的链上日报生成模式，以及本用户环境中已实施并验证的日报模板。

---

## 项目 1: wsleepan/bitcoin-daily-onchain-report

**Repo**: https://github.com/wsleepan/bitcoin-daily-onchain-report
**架构**: Claude Code 定时任务（云端）→ 数据采集 → 规则评分 → Markdown 报告 → Telegram 发送 → Git 提交
**特点**: 全免费 API，运行在 Claude Code 云定时任务，无需持久化服务器

### 核心文件
- `ANALYSIS_PROMPT.md` — 完整执行 Prompt（~200行）：数据采集步骤 + 评分表 + 报告模板 + 发送流程 + Git 提交
- `reports/YYYY-MM-DD.md` — 每日报告
- `reports/SUMMARY.md` — 累计摘要表

### 评分系统

5项规则打分（各 -2 ~ +2），总分 -7 ~ +7：

| 项目 | -2 | -1 | 0 | +1 | +2 |
|------|----|----|---|----|----|
| A. F&G 逆反 | ≥76 极端贪婪 | 56-75 贪婪 | 45-55 中性 | 25-44 恐惧 | 0-24 极端恐惧 |
| B. MVRV | ≥5.0 | 3.5-5.0 | 2.0-3.5 | 1.0-2.0 | <1.0 |
| C. 算力趋势(30d) | — | <-2% | ±2% | >+2% | — |
| D. 活跃地址(30d) | — | 下跌 | 持平 | 上涨 | — |
| E. 价格动量(30d) | — | >+15% | ±15% | <-15% | — |

判定: ≥+3 → 买入 | -2~+2 → 观望 | ≤-3 → 卖出

### 可借鉴点
1. **单一 Prompt 调度** — 整个流程写成一个 Prompt，包括数据采集命令、评分表、报告模板、投递命令
2. **规则评分代替 LLM 主观判断** — 透明、可复现、可调试
3. **SUMMARY.md 累积日志** — 方便回溯趋势
4. **纯文本摘要 + 附件详情** — 双重投递

---

## 项目 2: edycutjong/nansen-make-alpha

**Repo**: https://github.com/edycutjong/nansen-make-alpha
**工具链**: Nansen CLI + Makefile + env auth + Telegram
**特点**: 零臃肿设计，Makefile 做编排

15个报告 target 覆盖：Wallet Profiler, Portfolio Tracker, Token God Mode, Whale Watching, Smart Money Flow/ Holding, Token Discovery, Cross-Chain Bridge, DeFi Exposure, Label Analyzer, PnL Calculator, Gas Optimizer

### 可借鉴点
1. **Makefile 编排模式** — 多命令链式执行
2. **Nansen 的智能钱角度** — 与 GMGN Smart Money 追踪互补
3. **0 运行时依赖** — 只需要 make + Nansen CLI

---

## 模板 C: 链上连续综合日报（5-Section）— 已验证

**用途**: Cron 定时投递，无用户交互，自动生成并投递 | **2026-07-25 首次成功运行**

### 5 个 Section

| # | 章节 | 内容 | 数据源 |
|---|------|------|--------|
| 1 | 市场概况 | BTC/ETH 当前价格、24h涨跌、一句话情绪判断 | Binance API (fallback from CoinGecko) |
| 2 | 链上热点 | 目标链 Top 代币 + 主导叙事 + 5m/1h 双区间数据 + SM/rug 指标 | GMGN market trending (5m+1h) + hot-searches |
| 3 | 聪明钱动向 | Smart Money 买入活动、KOL 追踪、Signal Type 12 事件 | GMGN market signal --signal-type 12 |
| 4 | 新币监控 | 新部署代币质量概览、Rug/貔貅风险标记 | GMGN market trenches --type new_creation |
| 5 | 风险提示 | 风险表格：类型 → 目标 → 说明 | 综合所有数据源 |

### 并行取数顺序

**Batch 1**（同时发起，互不依赖）：
- Binance BTC 价格 + 24h 涨跌
- Binance ETH 价格
- GMGN Solana trending (5m)
- GMGN Solana trending (1h)
- GMGN Robinhood/BSC trending (5m)
- GMGN Robinhood/BSC trending (1h)

**Batch 2**（Batch 1 完成后）：
- GMGN Solana hot-searches (1h)
- GMGN 目标链 hot-searches (1h)
- GMGN market signal (type 12 = Smart Money buys)
- GMGN market trenches (new_creation, safe preset)

### BTC/ETH 价格获取

**CoinGecko 经常被限速**，使用 Binance REST API 作为主数据源：
```bash
curl -s "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
curl -s "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"   # 含 priceChangePercent
curl -s "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
```

### 输出格式基准

```
📊 **链上综合日报 | YYYY-MM-DD**

## 1️⃣ 市场概况
**BTC: $X** | 24h ±X%
**ETH: $X** | {行情简述}
> {情绪判断}

## 2️⃣ 链上热点 — {主导叙事名称}
{链名} {时间区间} 涨幅榜
{代币条目: SYMBOL, CA, MC, Vol, ±%, SM, KOL, rug, 观察}

{跨链叙事说明}

## 3️⃣ 聪明钱动向
{SM活动摘要}

## 4️⃣ 新币监控
{新盘概述}

## 5️⃣ 风险提示
⚠️ {类型}: {目标} — {说明}
🔴 {类型}: {目标} — {说明}

📌 **今日核心叙事：** {一句话}
```

### 关键规则
- 每条信息 ≤ 3 行，结论前置
- 每个代币 **必须包含 CA**
- 每个 Section 标注链名（Solana / Robinhood / BSC）
- 跨链镜像叙事（Sol → RH/BSC）需要单独指出
- 使用 `[SILENT]` 静默模式（全部数据源都空时才用）

---

## 本项目（gmgn-onchain-analysis 用户）的其他已实施模板

### Cron: 每日Alpha合成简报（19:00）

**数据流**: GMGN trending 扫 Sol/BSC/RH 三链 6h → 6类过滤器 + 0-75 评分系统 → DeFiLlama 三链 TVL → 跨链叙事交叉验证

**输出**: 三链 TVL + 优质标的分 + 叙事 + 跨链信号 + 建议

### Cron: 链上全景日报（22:00）

**数据源**: CoinGecko (代理) → BTC/ETH/SOL 价格 → alternative.me F&G → DeFiLlama 6大链 TVL → gmgn-cli gas-price → gmgn market trenches/trending → gmgn track smartmoney

**输出格式**:
```
━━━ 📊 链上全景日报 ━━━
📅 YYYY-MM-DD 22:00
━━━ 📈 大资产 ━━━
━━━ 🧠 市场情绪 ━━━
━━━ ⛓️ 链上TVL ━━━
━━━ 🐋 聪明钱异动 ━━━
━━━ 🔥 今日新币/优质标的 ━━━
━━━ 📊 今日关键数据 ━━━
━━━ 🎯 明日关注 ━━━
```

### 与开源项目的差异

| 维度 | wsleepan | 本项目 |
|------|----------|--------|
| 覆盖资产 | 仅 BTC | BTC/ETH/SOL + 三链 meme |
| 链上指标 | BTC 原生指标（算力/地址/交易） | TVL + Gas + 聪明钱 |
| 信号输出 | 规则评分买/卖/观望 | 过滤评分+叙事分析+跨链 |
| 数据源 | 免费公开 API | GMGN + API + OKX |
| 执行方式 | Claude Code 云端 | Hermes cron job |

### 关键规则（通用）

1. **所有数据必须有来源** — 不编造、不猜测
2. **评分规则透明** — 规则驱动，不靠 LLM 瞎猜
3. **每日累计日志** — SUMMARY 方便回溯
4. **每条信息 ≤ 3 行** — Telegram 友好，结论前置
