---
name: narrative-diffusion-monitoring
description: "Use when 判断一个叙事/热点是否真在扩散、行情是否发动。独立事件计数，零 token。"
version: 1.0.0
author: Hermes Agent (session-derived)
license: MIT
tags: [crypto, narrative, news, rss, monitoring, zero-token]
metadata:
  hermes:
    tags: [crypto, narrative, news, rss, monitoring, zero-token]
    related_skills: [meme-token-structure-veto, onchain-market-temperature]
---

# 叙事扩散计数（零 LLM）

## When to Use

- KOL / 车头喊单后，判断「行情是不是真要发动」
- 发 CA 前需要叙事背景（这个题材最近在几个独立源出现过）
- 写日报第一段、定当天基调
- 用户问「XX 又在喊了」「行情要来了吗」「这个叙事真不真」
- 用户只发「叙事」两个字 → 默认跑 `--brief` 三行版

回答一个问题：**这个叙事是不是真在扩散？** 不调模型，纯字符串统计，零 token。

用于：KOL 喊单后判断是不是「行情发动」、发 CA 前找叙事背景、日报第一段定基调、
用户问「XX 又在喊了，行情要来了吗」。

## 核心定义：独立事件数 ≠ 条目数

一条通稿被 8 家转载，是 **1 个事件 + 8 个渠道**，不是 8 个独立信号。
把转载数当扩散度，会让你在**每一次通稿转发**里都看到「全网共识」。

所以所有计数都按**独立事件**：先折叠转载，再数。

## 流水线（顺序不能换）

```
1. 采集   RSS 6 家 + Google News 关键词 + GDELT + Telegram 公开频道（全部免费无 key）
2. 过滤   活动文案（referral / earn up to / price today / price prediction / how to buy）
3. 折叠   标题 Jaccard ≥ 0.55 视为同一稿 → 一个事件，域名集合单独记
4. 匹配   只匹配**标题**；正文提及不算（交易所站每篇都提稳定币，正文匹配会把稳定币刷到第一）
5. 门槛   泛化叙事（AI Agent / 监管 / DeFi / Layer2）必须同时出现加密词
6. 排序   按独立事件数，其次域名数
```

数据源（实测可用）：The Block / Cointelegraph / Decrypt / Blockworks / CryptoSlate / CoinDesk 的 RSS；
Google News `https://news.google.com/rss/search?q=<kw>&hl=en-US&gl=US&ceid=US:en`；
GDELT `api.gdeltproject.org/api/v2/doc/doc?query="<kw>"&mode=artlist&timespan=24h&format=json`；
Telegram `https://t.me/s/<channel>` 网页预览。

现成脚本：`~/.hermes/scripts/narrative_radar.py`（同机已存在；换机器时按上面的流水线重写，逻辑比代码重要）。

```bash
python3 ~/.hermes/scripts/narrative_radar.py --brief            # 3 行结论（用户要的格式）
python3 ~/.hermes/scripts/narrative_radar.py --brief --hours 6  # 盘中看新冒头的
python3 ~/.hermes/scripts/narrative_radar.py --min-events 3     # 只看强信号
```

## 五个必须踩过一次才知道的坑

1. **Google News 的 `<source>` 不解析 → 独立事件失真。**
   不读 `<source url="...">`，所有转载都挂在同一个 source 名下，最后报「15 个事件 / 1 个域名」。
   必须取 `<source>` 的域名当 `domain`，标题才是去重单位。
2. **Google News 标题尾部带 ` - 媒体名` → 媒体名里的 "Crypto" 混进匹配。**
   「United Airlines restricts AI agents' access — Crypto Briefing」会被判成 crypto 叙事。
   入库前用 `re.sub(r"\s+-\s+[^-]{2,45}$", "", title)` 剥掉后缀。
3. **正文匹配 ≠ 叙事命中。** 交易所有站是 SEO 农场，正文什么都提。只认标题。
4. **泛化叙事必须加加密上下文门。** AI Agent / 监管 / DeFi / Layer2 这类词在主流新闻里满地都是；
   要求标题里同时出现 crypto/token/chain/defi/solana/binance… 之一，否则一律丢弃。
5. **别把折叠阈值调太松。** Jaccard 0.55 是实测值；调到 0.4 会把不同事件并成一个，
   调到 0.8 则同一稿的改写标题会重复计数。

## 判定梯度（直接当动作依据）

| 独立事件 | 含义 | 动作 |
|---|---|---|
| 1 | 单一来源/KOL 在说 | 忽略 |
| 2-3 | 开始扩散 | 记下来，等 24h |
| 4-6 | 已被市场确认 | 可按叙事布局 |
| 7+ | 全市场共识 | **派发段，不是入场** |

「7+ = 派发段」是最反直觉、也最值钱的一条：叙事被所有人讲的时候，价格已经在出货。

## `--brief` 输出格式（用户指定，固定 3 行）

```
最强叙事  Meme 币 · 14 事件 / 12 域名
链        SOL×2 BSC×2 RH×1
读数     稳定币在收缩（链上子弹变少）；全市场共识 = 派发段，别追
```

第三行是纯规则叠加，最多两条：

```
稳定币 ≥ 4 事件          → "稳定币在收缩（链上子弹变少）"
Meme 币 ≥ 7 且非最强     → "meme 已是共识区"
最强 ≥ 7 → 派发段     4-6 → 已确认可布局     2-3 → 等 24h
```

`--brief` 时进度信息全部走 stderr 或静默，**stdout 只能有那 3 行**，否则没法直接贴。

## 行情是否「发动」的五条件（用叙事计数做其中一条）

```
① BTC 4H 收盘站上 EMA20，且 SMA20 上穿 SMA60
② 稳定币总供应连续 3 天回升（不是单日反弹）
③ 每日新盘数量翻倍
④ 叙事雷达出现「新」叙事 3+ 独立事件（不是 meme 本身，是某个具体题材）
⑤ 关注的钱包开始连续新建仓（不是单笔）
```

**三条以上才算发动；零到一条 = 存量博弈。**
单盘速通、KOL 喊单都不进这个清单 —— 它们解释的是单个盘，不是行情。

## 扩展词典

`NARRATIVES` 是一张「概念 → 多种说法」的表。用户提到一个新题材时，改这张表而不是改逻辑：

```python
"RWA 代币化": ["rwa", "real world asset", "tokenized treasur", "tokenization"],
"Perp DEX":  ["perp dex", "perpetual dex", "hyperliquid", "dydx", "gmx"],
```

同义词要覆盖**缩写 + 全称 + 头部项目名**，否则同一叙事会被拆成两三条。

## 没 LLM 的代价（要跟用户说清）

没有「补背景」和「社区讨论摘要」，只有计数和标题。
用户要的是「叙事扩散计数」时这正好够；他若想看「为什么重要」，那是另一个工具（需要 LLM，有 token 成本）。
别擅自升级成 LLM 版本 —— 用户明确选了零成本路线。
