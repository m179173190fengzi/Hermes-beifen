# GMGN CLI 常用命令参考

## 市场/扫描
```bash
gmgn-cli market trending --chain <chain> --interval <1h|6h|24h>
```
支持的链: sol, bsc, base, eth, robinhood, arb, op, sui, avax, tron

## 代币详情
```bash
gmgn-cli token info --address <address> --chain <chain>
gmgn-cli token security --address <address> --chain <chain>
gmgn-cli token smart-money --address <address> --chain <chain>
```

## 安全字段解读
| 字段 | 好 | 坏 |
|------|----|----|
| top_10_holder_rate | <20% 分散 | >50% 高度集中 |
| is_honeypot | false | true (不能卖) |
| is_renounced | true (放弃权限) | false |
| buy_tax/sell_tax | 0-5% | >10% |
| lock_percent | >80% | <50% |
| bundler_rate | <5% | >20% |
| creator_close | false(在池) | true(已撤池) |

## 评分速算
```
创建者在池:       +15
放弃权限:         +15
锁仓>80%:         +10
机器人<20%:       +10
Top10<20%:        +15
聪明钱>15个:      +10
持币>1000:        +10
流动性>$50K:      +10
买>卖:            +5
满分100, ≥70可推, ≥85重点推荐
```
