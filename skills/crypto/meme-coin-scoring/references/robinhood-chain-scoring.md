# Robinhood Chain 评分工作流

## 当前 GMGN 支持状态 (v1.5.2)

| 功能 | 状态 |
|:----|:----:|
| ✅ 热搜榜 | 可用（Bundle/Top10/聪明钱全） |
| ❌ 币详情 | 暂不支持 |
| ❌ 信号检测 | 暂不支持 |
| ❌ Trenches | 暂不支持 |
| ❌ K线 | 暂不支持 |

## 热搜榜数据格式

```python
# gmgn-cli market trending --chain robinhood --interval 1h --limit 20 --raw
# 数据在 data > rank 数组中
items = d['data']['rank']

# 每个 item 的关键字段：
# symbol, address, market_cap, volume, liquidity
# price_change_percent1h, buys, sells, holder_count
# top_10_holder_rate, smart_degen_count, bundler_rate
# renounced_mint, creator, creator_token_status
```

## Robinhood Chain 实测特点

从 2026-07-10 的数据观察：

| 特点 | Solana | Robinhood |
|:-----|:-------|:----------|
| Bundle率 | 5-40%（经常有机器人） | 普遍接近 0% |
| Top10 集中度 | 10-70% | 大多 < 10% |
| 聪明钱密度 | 0-18个 | 可到 25个 |
| 流动性 | 不稳定 | 相对稳定 |
| 机器人行为 | 多 | 少 |

Robinhood Chain 上的数据看起来比 Solana 干净，但用户量也小很多。

## 受限的评分

由于 token info 不可用，以下维度无法评估：
- 开发者持仓（creator_token_status）
- 铸币权是否放弃（renounced_mint）
- 锁仓率（lock_percent）
- 狙击手数量（sniper_count）

可用的评分维度仅限热搜数据包含的字段：
- Bundle率 → 部署者信誉分
- Top10 → 筹码分散度
- 聪明钱数量 → 机构关注度
- 流动性 + 市值 → 链上健康度
- 交易笔数 + 买卖比 → 活跃度

## 典型高分标的 (2026-07-10)

```
#1 WALLET — MC $671K, 聪明钱25个, 持仓1056人, Bundle0%, Top10 0%
#2 pooɥ — MC $396K, 聪明钱21个, 持仓995人, Bundle0%
#3 poou — MC $26.7K, 聪明钱25个, 持仓252人, Bundle0%
```

## 建议

1. 先用热搜榜扫描，过滤出 Bundle<5%、Top10<20%、聪明钱>5的币
2. 手动去 DexScreener 上查币详情
3. 等 GMGN 后续版本完善 token info 支持后再做自动评分
