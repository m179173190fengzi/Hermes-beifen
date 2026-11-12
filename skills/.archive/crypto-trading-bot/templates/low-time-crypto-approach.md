# 碎片化时间用户的链上打法

## 适用人群
- 工作时间长、没空盯盘（工地/工厂/司机等）
- 有家庭负担，资金有限（$20-50/仓）
- 想参与链上打狗但风险承受力低
- 每天只有~10分钟看盘时间

## 每日流程（~10分钟）

```
1. 看 GMGN 热搜榜（5分钟）
   → gmgn-cli market trending --chain sol --interval 5m --order-by volume --limit 10
   → 只看有叙事的币（人物IP/社区情绪/梗文化）
   
2. 查感兴趣代币的 CA + 安全审计（3分钟）
   → gmgn-cli token info --chain sol --address <CA>
   → gmgn-cli token security --chain sol --address <CA>
   
3. 决定是否入场（2分钟）
   → 看 SM ≥ 3 且 rug_ratio < 0.3 可考虑
   → 小仓 $20-50 试水
   → 设好止损
```

## 监控策略（自动化）
- 设 cron 每15分钟检查 BSC MC>100K 或 Solana MC>200K
- 有新金狗自动推送到聊天
- 没新货不打扰（省token）
- 参数：`--min-marketcap 100000 --order-by market_cap`

## 五条铁律
1. **每天10分钟看GMGN热搜榜**（吃饭时刷一下）
2. **设好定时任务**（MC超阈值自动通知）
3. **看到有叙事的好币，收工了再研究**
4. **看好了就小仓位$20-50试试，设好止损**
5. **别追高、别FOMO、别all in**

## 识别叙事类型（老外角度）
| 类型 | 例子 | 特征 |
|:----|:----|:----|
| 人物IP | $ANSEM (Ansem), $MURAD | 有真实KOL背书 |
| 社区情绪 | $FOMO | 踩市场心理 |
| 反讽/恶搞 | $BITCH, $TRENCHER | 自嘲幽默 |
| 动物/符号 | $SKULLY | 简单好记 |
| 城市/地域 | $SOLANGELES | 蹭热度 |

## 注意
- 90%+代币归零，只有闲钱投资
- 不用杠杆、不借贷、不碰合约
- AI Agent适合：代币审计、钱包分析、市场趋势、监控告警
- AI Agent不适合：实时狙击、盯盘、替代TG Bot
