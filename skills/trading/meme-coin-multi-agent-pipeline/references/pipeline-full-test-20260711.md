# Pipeline 全流程实测 — 2026-07-11

## 测试数据

### Robinhood Chain — trending 6h (10个代币)

🎯 匹配6类过滤器: 4个保留 / 6个过滤

| # | 代币 | MC | 保留原因 | 评分 |
|---|------|-----|---------|------|
| 1 | $VLAD (The Green Bull) | $2.6M | 链创始人 (vlad) | 80/100 |
| 2 | $VLAD (The Robinhood) | $1.2M | 链创始人 (hood/vlad) | 55/100 |
| 3 | $SCAM (Scam Altman) | $37K | 科技领袖 (altman) | scam名过滤 |
| 4 | $VLAD (Robinhood) | $810K | 链创始人 (hood/vlad) | 35/100 |
| 5-10 | URINE, Merrymen, meow, Pointless | <$100K | 不匹配 | 直接过滤 |

### BSC Chain — trending 6h (10个代币)

🎯 匹配6类过滤器: 4个保留 / 6个过滤

| # | 代币 | MC | 保留原因 |
|---|------|-----|---------|
| 1 | $CZ | $11M | 链创始人+科技领袖 (CZ/Binance) |
| 2 | $bibi | $5.8M | 链创始人 (binance) |
| 3 | $CZBULL | $244K | 链创始人+科技领袖 (CZ) |
| 4 | $Spark | $28K | 链创始人 (binance) |

## 关键发现

1. Robinhood链代币质量整体偏低 — creator_close 标配(10/10), MC普遍<$100K
2. BSC链CZ主题币质量高 — $CZ MC $11M, 持币11793, 聪明钱129
3. SCAM类关键词过滤有效 — $SCAM匹配altman但名含Scam, 被实值逻辑拦截
4. 6类过滤器在两条链上都过滤掉60%的垃圾

## 单地址分析样本

### $WALLET (Robinhood Wallet) — 0x0339f5459fc690ac85f1782e15782a151b4a9e1b
- 链: Robinhood | 类别: 链创始人 | 知名机构
- MC: $2.6M | 流动性: $222K | 持币: 2408
- 安全: 开源/放弃权限/非蜜罐/锁仓95%/0税
- Top10: 14.04% (非常分散) | 聪明钱: 20+
- 推特: x.com/robinhoodapp
- 结论: Robinhood链上质量最高的实值币之一

### $JUGGERNAUT — 0xd7321801caae694090694ff55a9323139f043b88
- 链: Robinhood | 类别: 不匹配6类过滤器
- 持币6532 | 流动性$698K
- 无推特/无聪明钱/无热度
- 结论: 有流动性但无任何实值关联, 垃圾meme
