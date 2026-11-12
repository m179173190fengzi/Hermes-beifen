# 实测案例（2026-10，Robinhood 链 / Solana）

## 案例 A：$PIERRE —— 事件型，第一个盘赢

事件：尼斯 Micromania 店员 Pierre 对抗抢劫者的爆款视频（评论区一边倒夸 Pierre）。

| 项 | 数据 |
|---|---|
| 主盘 | `D3S6J9s1byrNBt3ZKwEDiPsNRqHtoEP8zQKdhyBdpump`（Solana, Pump.fun） |
| 创建 | 00:38 |
| 结果 | MC $1.31M，24h **+2951%（约 30x）**，24h 量 $5.32M |
| 结构 | 持币 4,123｜Top10 20.4%｜bundle 18.1%｜围猎 9.1%｜LP 未锁 $114K |
| dev | 发过 39 个币，`creator_close`（已清仓） |

同名盘 8 个，全部在同一 CA 的不同池或仿盘：
```
00:38  主盘           MC $1.31M  ✅
02:10  同一 CA 其它池  MC $1.27M
03:12  同一 CA 其它池  MC $1.28M
04:50  仿盘           MC $5,621   LP $0  ❌
04:36  仿盘           MC $7,491   LP $0  ❌
05:12  仿盘           MC $3,043   LP $0  ❌
BSC 仿盘              MC $11,778        ❌
```

**结论**：
1. 最早的创建者赢，仿盘全归零 → 「第一时间」的前提是「第一个正确的盘」。
2. dev 清仓了币还涨 30 倍 → 事件盘定价权在社区情绪，不在 dev。
3. 围猎仅 9.1% 是它能活的隐含条件（结构差但没被做局）。

## 案例 B：$SEASON (Farming Season) —— 官方皮 + 围猎内核

`0xea0071a8778fa02c12378e88868255e0e0952be6`｜Robinhood 链｜Uniswap｜台子 `pons_v2`

| 项 | 数据 |
|---|---|
| MC / FDV | $832K |
| 24h 量 | $662K |
| LP | 主池 $84K，**18 个池合计仅 $113K** |
| 变化 | 1h +50%｜6h +180%｜24h **+1610%** |
| 持币 | 2,105 |
| Top10 | **49.4%** |
| 围猎 | **51.5%**（实测最高） |
| bundle | 0 |
| dev | 发币 1 次，**已清仓** |
| LP 锁定 | 未锁 |
| 币龄 | 11 小时 |
| 买卖 | 24h 买 4,990 / 卖 3,367；**1h 买 288 / 卖 296（已翻转）** |

基本面：有官网 `farmingseason.io` + docs（农场经营游戏：田地/能量/建筑/竞技场/部落）+ 推特
`@farmingseasonio`，**全英文无中文界面**，`<html lang="en">`，JS bundle 里只有 `en-US` 且仅用于数字/日期格式化。

**结论**：结构一票否决。另外「没有中文界面」= 中文社群不会接盘，这是它围猎比例高的成因之一。

## 案例 C：Robinhood 链的真实格局（判「新链热度」时别只看链总量）

24h 热门（GMGN trending）：
```
PONS      $273.6M  ← 台子本币（链的 beta）
SPY       $20.3M   ← 代币化 S&P500
STANDARD  $19.4M
NVDA      $18.8M   ← 代币化英伟达
UHI       $18.7M
SPCX      $11.5M   ← 代币化 SpaceX
MEME/TORCH/godspeed $5-13M
──── pons_v2 台子上 ────
VRAX $3.54M｜KOLSHI $0.26M(+6415%)｜SEASON $0.72M(+11371%)｜EMPIREX $0.14M｜Prowler $0.01M
```
链级 24h 量 $800M，其中大头是**代币化股票**，不是 meme。
`Fables`（RH 链最大 DEX，ve(3,3) on Uniswap v4）TVL $32.3M、24h 量 $51.5M、24h fees $69K。

**推论**：所谓「RH 链第一个链游 + 底池发币」——链游部分可能成立，但「新机制」不成立（`pons` 是既有台子，
台子本币已 $273M）。新链溢价的正确落点是台子本币（beta），不是第一个应用币（alpha）。
