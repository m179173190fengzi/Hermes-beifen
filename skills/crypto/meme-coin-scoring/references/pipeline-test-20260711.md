# Pipeline 全流程实测 — 2026-07-11 Robinhood Chain

## 场景

首次测试 `meme-coin-multi-agent-pipeline` 管道，扫 Robinhood链 trending 1h。

## 扫描数据

统计: 10个代币（gmgn-cli 默认返回热门榜前10~15）

| # | 币名 | MC | 1h涨跌 | 评分 | 等级 | 聪明钱 | Top10 | 机器人率 |
|---|------|-----|--------|------|------|--------|-------|---------|
| 1 | SCAM | $69K | +2980% | 72 | B | 32 | 16% | 57% |
| 2 | URINE | $11K | +275% | 59 | D | 9 | — | — |
| 3 | Merrymen | $16K | +477% | 52 | D | 3 | — | — |
| 4 | meow | $62K | +599% | 56 | D | 4 | — | — |
| 5 | Pointless | $34K | -38% | 62 | C | 9 | — | — |
| 6 | OpenHood | $7K | -71% | 57 | D | 8 | — | — |
| 7 | Dumhood | $9K | -35% | 54 | D | 2 | — | — |
| 8 | UTILITY | $117K | -15% | 68 | C | 25 | — | 28% |
| 9 | bullieve | $54K | +135% | 50 | D | 4 | — | — |
| 10 | VLAD | $1.1M | -82% | 71 | B | 22 | 76% | — |

## 关键发现

### 1. `creator_close` 在RH上是通用状态
10个币全部 `creator_close: true`（部署者已撤池）。在Solana/BSC上这是正向信号（dev无抛售压力），但在RH链上 **没有区分度**，不能当正向信号用。

### 2. 评分分布完全匹配预期分级
- A级: 0% → 合理，RH链确实没有高质量标的
- B级: 20% → SCAM和VLAD各有亮点
- C级: 20% → UTILITY和Pointless值得观察
- D级: 60% → 大部分应该过滤

### 3. 聪明钱数量是最好的RH链过滤器
- 20+聪明钱 = 可以关注（SCAM 32, VLAD 22, UTILITY 25）
- <5聪明钱 = 基本没戏
- 其他指标在RH上区分度不高

### 4. RH链评分权重需要调整
| 维度 | 原权重 | 建议RH链 | 原因 |
|------|--------|---------|------|
| 部署者质量 | 30% | 20% | creator_close普遍无区分度 |
| 聪明钱质量 | 25% | 30% | 最佳区分指标 |
| 链上健康度 | 25% | 25% | 机器人率、Top10依然有效 |
| 交易活跃度 | 20% | 25% | 成交量/市值比是最佳RH链信号 |

## 命令备忘

```bash
# 正确的扫描命令
gmgn-cli market trending --chain robinhood --interval 1h

# 链名必须是全称，不是缩写
# ✅ robinhood, sol, bsc, base, eth
# ❌ rh, solana, binance

# --interval 必传
# 可选: 1m / 5m / 1h / 6h / 24h
```
