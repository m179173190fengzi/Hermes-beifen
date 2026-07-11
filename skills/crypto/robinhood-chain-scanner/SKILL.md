---
name: robinhood-chain-scanner
description: Robinhood Chain 链上扫币全流程 — 从发现新币到评分筛选到买入建议
trigger: 用户要求扫描 Robinhood Chain 新币
---

# Robinhood Chain 扫币技能

## 完整流程

### 第一步：打开监控页面
打开 DexScreener Robinhood New Pairs + NOXA Fun Trending。

### 第二步：实时扫描，关注新出现的对
- 年龄 < 30 分钟
- 用 `gmgn-cli market trending --chain robinhood --limit 20 --raw` 获取热搜数据
- 用浏览器打开 DexScreener Robinhood 页面获取最新交易对

### 第三步：快速筛选
检查以下几点：
1. 有无社交链接（Twitter/TG）？
2. 叙事是否强？（Robinhood/GME/官方相关）
3. 交易量和买入笔数是否突破？

## 叙事地图

参见 `references/narrative-map.md`。

Robinhood Chain 上所有代币都可以映射到三层叙事结构之一。分析时先判断代币属于哪个层级：
- **公司 Lore 层**（最强）：CASHCAT/KITSU/FIDEL/1/4663 等
- **HOOD 双关/传说层**（中强）：HOODRAT/ROB/MARIAN/DIH
- **WSB 记忆层**（回忆）：TENDIES/GME

如果代币不属于以上任何一层 → 叙事弱，需要其他维度更强才能推荐。

### 第四步：评分系统

用 meme-coin-scoring 技能给每个币打分（0-100），四个维度：
- 部署者质量（30%）：Bundle率、Top10集中度、开发者是否抛售
- 聪明钱质量（25%）：Smart Money 数量
- 链上健康度（25%）：流动性、锁仓、持仓分布
- 交易活跃度（20%）：成交量/市值比、买卖比、持有人数

### 第五步：筹码检查清单

按顺序检查每个币：
1. 年龄 < 30分钟？
2. 搜X看有没有热度：`twitter search "$SYMBOL robinhood"`
3. 数据：交易量上升？买入多？持仓数快速增加？市值低（几万~百万）？
5. 用 Blockscout 检查：https://robinhoodchain.blockscout.com
   - 打开 token 页面: `https://robinhoodchain.blockscout.com/token/<ADDRESS>`
   - 检查关键数据: 总供应量（通常10亿）、持仓人数、转账次数
   - 检查创造者：`https://robinhoodchain.blockscout.com/address/<ADDRESS>` 看创建者地址
   - 参考 `references/verified-blockscout-procedure.md` 获取详细操作步骤和已验证案例
   - 参考案例：$1 代币分析显示 2,364 持有人 / 10亿供应 / 62,344 转账（属于活跃但正常的Robinhood链代币）
5. GMGN确认：聪明钱有没有买？Bundle率如何？
6. 仅小仓位建议（总资金1-2%）

### 第六步：立即回避的信号
- 开发者/创建者钱包持续抛售
- 持仓极端集中或狙击手捆绑
- 无社交/叙述、虚假流量
- 流动性可随时移除
- 蜜罐或高税费

### 第七步：卖出与风控
- 止盈：涨2x卖30%、5x卖30%、10x卖剩余
- 止损：跌50%坚决卖
- 同时看3-5个币，不重仓一个

## 输出格式

```
🏆 推荐榜（评分≥75）
  币名 | 评分 | 亮点 | 风险

🟡 观察榜（评分60-74）
  币名 | 评分 | 亮点 | 风险

⛔ 回避榜（明显rug信号）
  币名 | 原因
```
