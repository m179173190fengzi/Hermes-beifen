---
name: trade-journal-review-loop
description: |
  给链上/meme 交易者搭「交易记录 → 自动追踪 → 周期归因」的闭环：入场瞬间自动快照指标、
  之后自动打 1h/6h/24h 标记、跌破止损线告警、周报算出胜率/期望值/「哪一类单必亏」。
  解决的是"只有原则、没有测量"的问题 —— 用户能说出六条交易心法，却答不出哪一条被违反。
  触发词：复盘、交易日志、记一笔、胜率、期望值、我这笔亏在哪、归因、交易记录、
  复盘闭环、trade journal、win rate、expectancy、post-mortem。
  English: trade log, journal a trade, review my trades, which setup loses money, expectancy.
---

# 交易记录 → 追踪 → 归因闭环

## 何时用

- 用户说「记一笔」「我买了 X」「这笔平了」→ 入库/平仓
- 用户问「我胜率多少」「哪类单在亏」「复盘一下」→ 周报
- 用户抱怨「知道要止损但还是乱打」「没有数据」→ 先建闭环，再谈策略

## 为什么必须做（不要跳过的理由）

用户的交易纪律（见 `beidou-meme-hunter` 心法）6 条全是"何时进 / 进什么 / 省子弹"，
**没有一条是测量**。后果：亏损集中在哪一类（打错类型？位置暴露？追高？）永远只能靠回忆。

**没有已平仓记录时，胜率和期望值毫无意义** —— 不要为了"有个报表"去算假数据，
直接说"还没有已平仓记录，算不出来"。

## 工具：`~/.hermes/scripts/trade_log.py`

```bash
# 1) 入库（自动抓入场指标快照 + 自动打标签）
python3 ~/.hermes/scripts/trade_log.py add <CA> --chain sol --usd 200 \
  --type ferment \
  --reason "特斯拉超跑发布会事件驱动" --tags "事件驱动" --plan "事件当天减半，冲高清仓"
# --type 只有两个合法值（见下节「盘型」）：
#   pvp     = 浇给型，赚了就跑（行情热时的抢跑盘）
#   ferment = 发酵型，出本长持（翻倍先撤本金）

# 2) 刷新未平仓（1h/6h/24h 标记、当前浮盈、跌破 -20% 告警）
python3 ~/.hermes/scripts/trade_log.py update

# 3) 列表 / 平仓
python3 ~/.hermes/scripts/trade_log.py list
python3 ~/.hermes/scripts/trade_log.py close <id> [--price 0.0072] [--note "事件兑现走一半"]

# 4) 周期归因
python3 ~/.hermes/scripts/trade_log.py report --days 30
```

### 入库自动抓什么（这是它的全部价值）

`gmgn-cli token info --chain <chain> --address <CA> --raw` 一次调用取：
价格、MC、LP、持币数、24h 量、ATH、Top10 占比、bundle 率、围猎盘率、
dev 发币次数、dev 状态、发射台、推特字段。**用户不需要手填任何指标。**

自动标签：用户给的 `--tags` + `MC 区间档位` + `发射台` + （给了 `--type` 时的）`盘型:pvp|ferment`。
这几个就是归因的分组维度。

### 盘型（PVP vs 发酵）：一个必填的分类，不是可选标签

来源是中文圈实盘共识（o皇体系，见 `crypto-carhead-smartmoney-monitoring`）：
**meme 只有两种，离场方式完全不同**。

| 类型 | 特征 | 离场 |
|---|---|---|
| **pvp**（浇给型） | 抢跑盘、热度盘、同名盘内卷 | **赚了就跑**；行情热时"进去 30s 没起来直接 sell" |
| **ferment**（发酵型） | 有叙事、有持续资金、能带一波 | **翻倍出本**（本金先撤），剩余长持 |

**判不出类型 = 不该开仓**——因为离场规则无法预先确定。
所以 `--type` 缺失时按"未分类"记，并在周报纪律检查里一并暴露（和"没写离场计划"同级）。

## 踩过的坑（写代码前先看）

- **MC 要自己算**：GMGN `token info` **没有** `market_cap` 字段，
  必须 `price.price × circulating_supply`（缺失时回退 `total_supply`）。
  直接读 `price.market_cap` 会得到 0，MC 档位标签也就全错。
- **稳定币必须过滤**：按「符号或名称含 `usd/dollar/stable/tether`」排除。
  实测抓错过一次 `USDG (Global Dollar)` 被当成"买入标的"进归因。
- **推特字段可能是伪装的链接**：值形如 `用户名/status/123`、`i/communities/...`、`search?q=`。
  用 `^[A-Za-z0-9_]{2,20}$` 校验，不匹配就当"非常规账号"处理，别渲染成 `@Polymarket/status/...`。
- **止损告警只响一次**：用 `stop_alerted` 标记位，否则每小时刷一次同样的告警会让人麻木。
- **测试会污染统计**：造测试记录后必须清掉 journal（`rm ~/.hermes/trading/journal.json`），
  否则"胜率 100%（1胜0负）"这种垃圾数会长期误导。
- **入场指标抓不到时仍要入库**：快照为空也要留记录（标记 `入场快照缺失`），
  比丢掉这笔强——周报会把它算进"纪律检查"。

## 数据结构

`~/.hermes/trading/journal.json` → `{"trades": [...]}`，每笔：

```
id / status(open|closed) / chain / ca / sym / name / opened_at
entry{price, mc, lp, holders, vol24, ath, top10, bundle, entrap, dev_launches, launchpad, twitter}
type(pvp | ferment | 未分类) / usd / reason / plan / tags[] / marks{1h,6h,24h:{price,chg_pct}}
last_price / last_chg_pct / last_check / stop_alerted
closed_at / exit{price, pnl_pct, note}
```

`plan`（离场计划）是最重要的一列：**空着就等于"没有离场规则"**，入库时要当场提醒用户。

## cron 化（零 token）

| 任务 | 频率 | 行为 |
|---|---|---|
| 持仓追踪 | 每小时 | 刷标记+浮盈；**正常时完全静默**，只有跌破 -20% 才输出 |
| 交易周报 | 每周（如周日 20:00） | 输出胜率/期望值/特征归因/纪律检查 |

⚠️ **no_agent cron 不能传命令行参数** → 需要两个极薄的 wrapper 脚本
（`trade_update_cron.py` / `trade_report_cron.py`：subprocess 调 `trade_log.py update|report`，
把 stdout 原样 print，退出码恒 0）。这是 Hermes cron 的通用形态，不是本项目特例。

## 单币监控：只在用户明确要求时启动

用户原话：「这个币不要盯了，**以后我发 ca 我说要你盯才开始盯**」。

- **只发 CA** → 只做体检（结构 / 评分 / 叙事），不建监控、不进 watchlist、不挂 cron
- **发 CA + 明说"盯"** → 才建阈值告警：`~/.hermes/scripts/price_watch.py` +
  `~/.hermes/cron/watch_prices.json`（`mc_below` / `mc_above` / `lp_below`，越线才推、平时静默）
- **停止**：`watch_prices.json` 置 `[]` + `cronjob(action="pause")`。
  **不要删 cron / 脚本**——用户下次说"盯"要能一条命令恢复
- 阈值规则要能**自动重新武装**：条件解除后重置 `fired` 标记，下次再越线仍然报

## 枯水期（硬门槛过线率 <5%）该怎么用这套记录

meme 枯水期不是"找事做"，是"趁没行情补数据"：

| 做 | 不做 |
|---|---|
| 补录历史单 → 周报才能算"哪类单必亏" | 降低标准凑单（= 心法第 5 条警告的打光子弹） |
| **调高**过滤器门槛（宁可看不到，也别看垃圾） | 因为没打到就加大仓位 |
| 把趋势系统（V4 / 4H）提上来跑 —— meme 枯 ≠ 趋势枯 | 把 meme 的离场规则套到趋势单上（反之亦然） |

实测枯水期基线：两链各扫 180 个新盘，过硬门槛的只有 8 个（BSC）/ 3 个（SOL），
且过线的还带 `dev 发币 2000+ 次`、`围猎盘 20%+`。这种时候"没有标的就是正确答案"。

## 往回看：没有日志也能做归因（wallet_audit.py）

journal 是「往后记」，用户往往没耐心记。**他说「分析我的操作逻辑 / 我的交易随意性 / 我总爱补仓」时，
不要要求他从今天开始记笔记——直接扒链上活动反推。**

```bash
python3 ~/.hermes/scripts/wallet_audit.py --wallet <addr>            # 全量（三链）
python3 ~/.hermes/scripts/wallet_audit.py --wallet <addr> --cached   # 秒出
bash ~/.hermes/scripts/wallet_daily.sh                               # 24h 巡检，无交易则静默
```

输出：胜率 / 盈亏比 / **按持仓时长分桶的盈亏** / 加仓分类（追涨·补跌·平摊）/ 卖了又买回次数 /
单笔金额离散度 / 摩擦成本（单笔 -$5~0 的合计）。

**核心用法：先验证他的自我叙事，再开药。** 实测用户的「我总爱补仓」是错的——
他 36% 胜率却赚钱，靠 7.4:1 盈亏比，利润 100% 来自 >1 天的 5 笔，而唯一赚大钱的补仓
（-46% 连补三次后 3.5 倍卖出）正是"补仓"。真正伤害是「卖出后买回」和「1 分钟内秒进秒出」。

完整算法、字段、坑与结论模板见 `references/onchain-wallet-behavior-audit.md`。

## 低摩擦用法（关键）

用户不会记命令。他只说一句话：

> 「记一笔 FTR sol 仓位200 事件驱动，计划发布会当天减半」

agent 的职责：解析成 `add` 命令、抓快照、回显入场指标 + 标签 + 离场计划，
并在 `--plan` 缺失时提醒（这是纪律，不是啰嗦）。

平仓同理：「FTR 平了」→ `close <id>` 用当前市价算盈亏。

## 怎么读周报（别只念数字）

1. **单笔期望值**是核心指标：`平均盈利×胜率 + 平均亏损×(1-胜率)`。负期望 = 停下来改规则，不是加大仓位。
2. **按特征归因**看的是"最差标签"：那才是"你哪一类单必亏"。
3. **按盘型对比（pvp vs ferment）**——这是最该看的一张表：它直接回答"我到底该打哪种盘"。
   两类各算胜率与期望值，差距大就砍掉差的那一类，而不是"两边都打、两边都不精"。
4. **纪律检查**（没写离场计划 / 快照缺失 / 未分类盘型的笔数）比盈亏更重要——它预测未来会不会亏。
5. 样本 < 10 笔时不要下结论，只说趋势。
