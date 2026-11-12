---
name: cex-listing-event-monitoring
description: |
  监控交易所（币安为主）的上新 / TGE / Launchpool / Megadrop / HODLer 空投 / Binance Alpha 公告，
  并把「要不要打新」做成带事实依据的判断。两层架构：no_agent 高频检测（零 token）+ 低频 LLM 分析（[SILENT] 早退）。
  触发词：币安上新、币安公告、TGE 监控、Alpha 上新、打新、Launchpool、HODLer 空投、
  「以后币安出现 TGE 帮我分析」、CEX listing alert。
  English: monitor Binance announcements, new listing alerts, TGE analysis, launchpool watch.
---

# CEX 上新 / TGE 公告监控与打新分析

> 目标：**公告一出来 15 分钟内知道，2 小时内拿到「打不打」的结论。**
> 原则：公告是**事件驱动**的确定性信息，不要用昂贵的 LLM 轮询去发现它。

## 零、默认不自动监控（用户偏好，优先于下面所有架构）

用户 2026-10 亲口否掉了自动监控：**「算了还是费钱，我刷X看见了你给我分析就行了不用监控了」**。
所以本技能的正确默认状态是：

- **默认不存在任何检测/分析 cron。** 不要因为下面写了「两层架构」就顺手建 job —— 建了会被要求删掉，白折腾。
- 触发方式改为**按需**：用户发公告链接 / 币名 / 推文截图 → 现场抓 detail API（见第二节）+ 补链上结构 → 直接给结论。
- 只有用户明确说「要监控」「帮我盯着上新」「设成自动」时，才启用第一节的两层架构，**并先报成本**
  （检测层 0 token；分析层 ~1.5K/次 × 12 次/天 ≈ **15K tokens/天**，约 ¥0.05）。
- `binance_tge_watch.py` / `binance_tge_analyze.py` 留作**手动工具**。按需分析不必走 pending 队列：
  直接 `articleCode` → detail API → `lex_text()` 抽正文 → 正则捞 CA/时间/百分比 → 有 CA 再补 GMGN。
- 同类偏好也适用于单币监控：**只给 CA 只做体检；说「盯」才启动监控**。



```
检测层  no_agent 脚本，每 15 分钟           ← 0 token
        └─ 有新公告 → 推送「标题 + 类目 + 时间 + 链接」 + 入队
分析层  agent cron，每 2 小时               ← 空跑 ~1.5K tokens（[SILENT] 早退）
        └─ 队列有货 → 抓正文事实 → 给结论
```

**不要把两层合成一个高频 LLM，也不要为了「第一时间」让 agent 每 15 分钟跑一次。**

参考实现（本机已落地）：
- `~/.hermes/scripts/binance_tge_watch.py` —— 检测 + 推送 + 入队去重
- `~/.hermes/scripts/binance_tge_analyze.py` —— 抓正文、抽事实、补链上结构
- 状态：`~/.hermes/cron/state/binance_tge.json`（`{seen:{id:ts}, pending:[{...,analyzed:bool}]}`）

## 二、币安公告 API（实测可用）

**列表**（一次能拿到 7 个类目）：
```
GET https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20
→ data.catalogs[] = {catalogId, catalogName, articles[{id, code, title, releaseDate}]}
```
| catalogId | 含义 | 与打新相关度 |
|---|---|---|
| 48 | New Cryptocurrency Listing | ★★★ |
| 93 | Latest Activities（Launchpool/Megadrop/Booster） | ★★★ |
| 128 | Crypto Airdrop（HODLer） | ★★★ |
| 49 | Latest Binance News | ★★ |
| 161 / 157 / 51 | Delisting / Maintenance / API Updates | 无关 |

**详情**（正文）：
```
GET https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=<code>
→ data.body = Lexical 编辑器 JSON 的**字符串**（不是纯文本，也不是 HTML）
```
取文本：`json.loads(body)` 后递归遍历，收集所有 `text` 字段即可（见 `binance_tge_analyze.py` 的 `lex_text`）。

公告页：`https://www.binance.com/en/support/announcement/<code>`

## 三、关键词与噪音

**命中**：`tge` / `token generation event` / `launchpool` / `megadrop` / `hodler airdrop` /
`booster` / `pre-market` / `binance wallet` / `binance alpha` / `will list`

**噪音（必须排除，否则天天刷屏）**：`trading competition` / `trading tournament` /
`carnival` / `predict lol` / `zero trading fee` / `collateral asset` / `margin`

## 四、两个必须处理的坑

1. **首次运行会把历史公告全推一遍。** 必须「播种」：state 里 `seen` 为空时，把当前抓到的所有 id
   记为已见、**不推送**、直接退出。否则第一个 tick 就给你 20 条旧公告。
2. **同一事件会发多条公告**（首发 + 参数补充 + 上线提醒）。用 article `id` 去重，并接受
   「同一项目多条待分析」的情况——分析层按项目合并输出。

## 五、打新分析清单（对每个新公告走一遍）

```
【项目】名称 (代币) | 类型（TGE / Alpha / Launchpool / Megadrop / HODLer）
📅 关键时间: 上线时间 / 快照 / 资格窗口（统一换算 UTC+8）
💰 代币经济: 总供应 / 本次发放量 / 初始流通% / 解锁节奏（团队+投资人锁多久）
⛓️ 链上: CA | MC | LP | 持币数 | Top10 | dev 发币历史
🎯 结论: 打新 / 不打 / 观察（三选一，不许模棱两可）+ ≤3 条理由
⏰ 行动: 几点去蹲、要不要锁 BNB、什么价位出
⚠️ 风险: 最致命的 1-2 条
```

**判断权重（按踩过的坑排序）**：
1. **初始流通比例 + 解锁曲线** —— 低流通（<15%）+ 团队零释放锁 12 个月 = 上线即出货窗口
2. **LP 深度 vs MC** —— MC $65M 而 LP 只有 $5.9K 这种结构，一砸就穿
3. **持币数极少**（几百个）而 MC 很高 = 筹码高度集中，别接
4. **上线时间以公告原文为准**，媒体/推特常写错（曾出现公告 16:00、帖子写 8:00）
5. **打新 ≠ 长持**：TGE/上币是典型「买预期卖事实」，事件当天必须减仓

## 六、输出规则（给用户看的）

- 纯文本直发 Telegram，禁 HTML/表格/附件
- **禁止编造数字**：拿不到就写「未披露」，CA 原样照抄
- 结论必须三选一；给「观察」时要说清触发条件（例如「回到 MC 200-300K 且 LP 已锁再看」）
- 多项目分条列，一次最多 5 条
