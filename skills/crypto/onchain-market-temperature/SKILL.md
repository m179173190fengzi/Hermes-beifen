---
name: onchain-market-temperature
description: |
  判断链上打狗市场「热还是枯」的量化指标组：链级 24h DEX 成交量 + Fees + 量/费比，
  以及 GMGN 平台手续费收入（真金白银的活跃度温度计）。用来回答「链上这么枯还能做什么」、
  「市场现在什么状态」、「该不该出手」，也用于日报的第一段。
  触发词：链上这么枯、市场怎么样、还能做什么、打狗温度、成交量、fees、GMGN 收入、
  市场冷热、是不是熊了、要不要出手。English: is the onchain meme market hot or cold, market activity gauges.
---

# 链上市场温度计

> 一句话：**TVL 是锁仓，不是热度。看成交量、Fees、以及平台自己赚了多少钱。**

## 三个指标（都免费、无需 key、走代理）

```bash
# 链 24h 成交量 / 变化率
https://api.llama.fi/overview/dexs/{chain}?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
#   → {total24h, total7d, change_1d}

# 链 24h Fees（协议+LP 手续费）
https://api.llama.fi/overview/fees/{chain}?excludeTotalDataChart=true

# GMGN 平台收入（打狗活跃度温度计）
https://api.llama.fi/summary/fees/gmgn?dataType=dailyFees
#   → {total24h, total7d, total30d, change_1d, totalDataChart: [[ts, usd], ...]}
```

chain slug：`solana` / `bsc` / `robinhood` / `ethereum` / `base` / `arbitrum` / `hyperliquid` / `sui` / `ton` …

现成脚本：`~/.hermes/scripts/chain_rank.py`（默认只跑 SOL/BSC/RH，`--all` 跑 14 条链，`--top N`）。
日报里由 `daily_scan.py` 的 `activity_lines()` + `gmgn_fee_lines()` 调用。

## 量/费比 = 最便宜的真假判别器

```
量/费比 = 24h 成交量 ÷ 24h Fees
```

| 比值 | 含义 |
|---|---|
| 低（<150x） | 费率正常、真实需求强（ETH 长期最低） |
| 中（150-400x） | 低费率链（pump 1%、four/flap 更低） |
| 高（>450x） | 费率极低 **或有刷量**（Base、RH 常年最高） |

**成交放大但 Fees 不跟 = 刷量**，这条判断要写进任何日报的口径。

实测基线（2026-10，24h）：
`SOL $1.57B / $9.7M = 161x｜BSC $951M / $2.3M = 420x｜Base $808M / $1.4M = 598x｜RH $801M / $1.7M = 474x｜ETH $750M / $8.4M = 89x`

## GMGN 收入为什么是温度计

它是**交易量 × 平台费率**的直接结果，比 TVL 更贴近"还有多少人在打狗"。

实测一周（2026-10-12 → 10-18，美元）：
```
10-12 469,966
10-13 373,591
10-14 493,309  ← 峰值
10-15 408,303
10-16 382,028
10-17 256,712
10-18 253,513
```
峰值到当前 -46%，且最后两天走平 → 「活跃度下跌后在新低位横住」。

## 呈现格式（用户钦定，别自创）

用户明确要求：**只看近三天逐日对比 + 7 日趋势**。
- ✅ 要：`10-16 $382K → 10-17 $257K → 10-18 $254K（3日 -34%）| 7日趋势 ↓46%（峰值 $493K）`
- ❌ 不要：7 日总收入、日均值
- 链也只列 **SOL / BSC / RH** 三条，不要 TOP5/TOP10 刷屏

三天走势比单看跌幅更有信息量：逐日下滑 = 还在恶化；后两天走平 = 可能见底。

## 读数 → 行动（枯水期纪律）

- **过线率是硬指标**：日报硬门槛淘汰率长期 95%+（BSC 172/180、SOL 174/180）时，说明没有值得打的盘。
- **枯水期最危险的动作是「降标准凑单」**——把门槛降到 40 分等于在冬天把子弹打光（对应用户心法第 5 条：珍惜子弹熬寒冬）。
- 枯水期该做的是：① 补录历史交易做归因 ② 收紧/校准过滤器门槛 ③ 把另一套系统（V4 趋势）跑起来 ④ 囤叙事与角度词存货。
- 「两套系统同时没信号」是最明确的空仓信号：链上过线率 <5% + 趋势系统评分 <6/10。

## 第二层：叙事层温度（扩散计数）

上面三个指标量的是**钱**；叙事扩散量的是**故事**。钱先枯、故事后死；反过来故事先起、钱才回来，
所以两层一起读才知道现在是「真行情」还是「只有话题没有子弹」。

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
python3 ~/.hermes/scripts/narrative_radar.py --brief             # 3 行（默认交付形态）
python3 ~/.hermes/scripts/narrative_radar.py --hours 24            # 完整表（日报）
python3 ~/.hermes/scripts/narrative_radar.py --hours 6 --min-events 3   # 盘中强信号
```

判定梯度（按**独立事件数**，不是条目数）：1 = 单一源在说，忽略；2-3 = 开始扩散；4-6 = 已确认，
可按叙事布局；7+ = 全市场共识，**已是退出窗口**。

**日常交付用 `--brief`**：固定 3 行（最强叙事 / 链 / 一句话读数），进度信息全部静默，stdout 只有那 3 行，
可直接粘给用户。要标题清单、要判断哪个媒体在带头时才跑完整表。

零 LLM 成本（纯字符串统计，约 200-300 条/次、30-60 秒）。脚本在本 skill 的 `scripts/narrative_radar.py`，
口径、四个必做过滤（标题命中 / 转载折叠 / Google News `<source>` / 泛化叙事的加密上下文闸门）与
读数写法见 `references/narrative-diffusion.md`——**改脚本前先读它**，少一个过滤结果就不可用。

## 第三层：子弹层（稳定币供应）

链上买盘的本金就是稳定币。**供应在缩 = 子弹在抽，meme 拿什么接力。** 这是比成交量更前置的指标：
成交量是已经花掉的子弹，稳定币供应是还没花的。

```bash
# 稳定币总市值 + 变化（DefiLlama，免费无 key）
curl -s "https://stablecoins.llama.fi/stablecoins?includePrices=true" | jq '[.peggedAssets[].circulating.peggedUSD] | add'
# 分链（看 SOL / BSC 的本地子弹）
# .peggedAssets[] | select(.chainBalances.solana) → circulating
```

读数口径：**看连续 3 天方向，不看单日反弹**。单日回升常只是赎回延迟或跨链搬运。

实测（2026-11-12）：一周 **-$14.2B**，2022 熊市以来最大收缩 —— 同期 meme 叙事已达全市场共识（14 个独立事件）。
**子弹在抽 + 故事已共识 = 派发段**，这种组合下开新仓是接最后一棒。

## 行情是否真的「发动」：五条可验证信号

单个盘速通 **≠** 行情发动。存量市场里一个盘速通必然对应另外三个归零。
「行情要来了」只能由下面五条回答，**出现三条以上才叫发动，零到一条 = 存量博弈**：

```
① BTC 4H 收盘站上 EMA20，且 SMA20 上穿 SMA60（4H 均线由空头排列转多头）
② 稳定币总供应连续 3 天回升（不是单日）
③ 每日新盘数量翻倍
④ 叙事雷达出现「新」叙事 3+ 独立事件（是某个具体题材，不是 meme 本身）
⑤ 关注的钱包开始连续新建仓（不是单笔）
```

```bash
# ① 的一行测法（本机已有脚本）
python3 ~/.hermes/scripts/ma_state.py --inst BTC-USDT-SWAP --bars 1H,4H
# 看 4H 的「排列」字段：空头排列 = 价格在任何反弹之前先证伪；纠缠+跌破 EMA20 = 方向未定
```

**BTC 4H 空头排列时，任何「行情发动」判断都是假的** —— 大盘的 beta 压着，meme 只可能有局部轮动。

## KOL 喊单的证伪：只看一个数

有人喊「速通千万」「要发动了」，不要评价他的人，去查**喊单之后的量能是否放大**：

```
喊单后 1h 量 ÷ 24h 量
> 5%    → 真的带来增量资金，值得看
< 1%    → 喊单没带来买盘，是在派发而不是发动
```

实测（2026-11-12，某 KOL 喊「速通千万」的盘）：1h 量 $149K = 24h 量 $18.6M 的 **0.8%**，
1h 净卖出（买 1,104 / 卖 1,169）→ 那波喊单已经被消化完了。
**附带判据：同名仿盘（`xxx wif hat` 之类）已经出现 = 叙事被消费过的标志。**

## References

- `references/narrative-diffusion.md` — 叙事扩散计数的口径、过滤规则、读数梯度与成本对比
- `scripts/narrative_radar.py` — 可直接运行的扩散计数器（RSS + Google News + GDELT + Telegram）
