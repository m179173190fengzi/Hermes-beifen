---
name: onchain-meme-analysis
category: crypto
description: 全链打狗数据分析。整合GMGN + DexScreener + Twitter + DeFiLlama + NOXA/Robinhood链数据，任何币地址扔过来自动评分。
---

# 链上打狗数据分析系统

## 触发条件

用户提供任何链上的代币地址，或是要求扫链分析时，执行本技能。

## 工具链

- `gmgn-cli` — GMGN链上数据（热搜/聪明钱/Token信息/信号）
- `curl` — DexScreener API / DeFiLlama API
- `twitter` — X/Twitter搜索
- `yt-dlp` — YouTube信息抓取

## 工作流

### 模式A：分析单个代币

用户发来一个代币地址和链名时：

1. **GMGN数据拉取**
   ```bash
   gmgn-cli token info --chain <chain> --address <地址> --raw
   gmgn-cli token signal --chain <chain> --address <地址> --raw
   ```
   
2. **DexScreener数据**
   ```bash
   curl -s "https://api.dexscreener.com/latest/dex/tokens/<地址>"
   ```

3. **Twitter搜索**（看社区热度）
   ```bash
   twitter search "\$<币符号> -is:retweet" 
   ```

4. **评分（0~100）**
   - 筹码分布(25%): Top10集中度 + Bundle率
   - 聪明钱(25%): smart_degen_count数量
   - 流动性(20%): 流动性与市值比
   - 交易活跃(15%): Volume/MC比
   - 社交热度(15%): Twitter提及量

5. **输出格式**
   ```
   🔍 <币符号> 评分分析
   ━━━━━━━━━━━━━━━━━━━━━━━
   链: <chain> | 地址: <address[:12]>
   
   📊 维度评分:
     筹码分布: XX/100 (Top10 X%, Bundle X%)
     聪明钱:   XX/100 (Smart X个)
     流动性:   XX/100 ($X)
     交易活跃: XX/100 (Vol $X)
     社交热度: XX/100 (Twitter X条)
   
   🔥 复合总分: XX/100
   
   ⚠️ 风险提示:
   - Bundle > 30%? → 机器人盘
   - Dev还在持币? → 随时出货
   - 流动性可移除? → 可能rug
   
   💡 建议: [买入/观察/回避]
   ```

### 模式B：扫链浏览

用户要求扫某个链时：

1. **GMGN热搜榜**
   ```bash
   gmgn-cli market trending --chain <chain> --limit 20
   ```
   
2. **DexScreener新币**（Robinhood链专用）
   ```bash
   curl -s "https://api.dexscreener.com/latest/dex/search?q=robinhood"
   ```
   
3. **新币Trenches**（Solana/BSC/Base/ETH）
   ```bash
   gmgn-cli market trenches --chain <chain> --limit 30
   ```

4. **信号检测**
   ```bash
   gmgn-cli market signal --chain <chain>
   ```

5. **过滤规则**
   - ✅ Bundle < 20%
   - ✅ Top10 < 50%
   - ✅ 聪明钱 > 2个
   - ✅ 流动性 > $5K
   - ✅ < 1小时 新币优先
   - ✅ 有社交链接优先

### 模式C：Robinhood链专用扫链

按用户的完整流程：

1. 打开壁门监控：DexScreener Robinhood New Pairs + NOXA Fun Trending
2. 实时刷新，关注年龄 < 30分钟的新对
3. 快速筛选：
   - 有社交链接(Twitter/TG)?
   - 叙述是否强？（Robinhood/GME/官方相关）
   - 交易量和买入笔数是否突破？
4. 深入分析：
   - GMGN查聪明钱
   - Blockscout查持仓分布
   - 合约安全检查

### 模式D：链市纵观

```
用于定时任务，输出简报
1. 📊 链上TVL概览（DeFiLlama）
2. 🔥 DexScreener交易量TOP5（Solana/BSC/Robinhood）
3. 💬 Twitter热点/叙事
4. 🎯 机会推荐
```

## 相关技能

- `mc-robinhood-narrative-map` (crypto) — Robinhood Chain叙事图谱，判断新币的叙事层和板块轮动。分析Robinhood链代币时优先加载该技能对照叙事地图。
- `meme-coin-scoring` (crypto) — 0~100分复合评分系统（部署者信誉/聪明钱/链上健康/交易活跃度/社交热度）

- GMGN CLI对Robinhood Chain仅支持market trending，不支持token info和signal
- Twitter搜索不需要认证
- DexScreener API限流较宽，但不要高频请求
- 评分中Bundle/SmartMoney数据优先来自GMGN，因为最准确
