# 复盘闭环：`trade_log.py`（心法缺口 A + D 的落地工具）

心法原文 6 条里**没有一条讲离场、也没有一条讲测量**。这个工具就是补这两块：
**入场自动快照指标 → 定时追踪 → 自动归因「你哪一类单必亏」**。

- 脚本：`~/.hermes/scripts/trade_log.py`（纯标准库，零 LLM 成本）
- 账本：`~/.hermes/trading/journal.json`（JSON，可直接读/改）
- 已挂的 cron：
  - `持仓追踪(每小时)` → `trade_update_cron.py`（`0 * * * *`，正常时静默，**跌破 -20% 才发声**）
  - `交易周报(周日20点)` → `trade_report_cron.py`（`0 20 * * 0`）

## 命令

```bash
# 记一笔（自动抓入场快照 + 自动打标签）
python3 ~/.hermes/scripts/trade_log.py add <CA> --chain sol --usd 200 \
  --reason "特斯拉超跑发布会事件驱动" --tags "事件驱动" --plan "事件当天减半，冲高清仓"

python3 ~/.hermes/scripts/trade_log.py update          # 刷 1h/6h/24h 标记 + 浮盈 + 止损告警
python3 ~/.hermes/scripts/trade_log.py list            # 未平仓概览
python3 ~/.hermes/scripts/trade_log.py close <id> [--price X] [--note "..."]
python3 ~/.hermes/scripts/trade_log.py report --days 30
```

## 设计要点（照抄，别简化掉）

- **入库即快照**：`add` 时自动抓 `price / MC / LP / holders / vol24 / ath / top10 / bundle /
  entrapment / dev发币次数 / 发射台 / twitter`。**这是整个闭环的价值来源**——手工补记的指标
  一定是事后合理化过的，没有诊断价值。
- **标签自动生成**：从快照派生 `MC 区间`（<100K / 100K-1M / 1M-10M / 10M-50M / >50M）与发射台，
  再加上用户手写的叙事标签。**归因就靠这些标签分组**。
- **离场计划是必填的软强制**：没写 `--plan` 时在输出里当场警告（「心法缺口 A」）。
- **止损机械执行**：`update` 里对每笔算浮盈，跌破 **-20%** 且未告警过 → 打印告警（含入场价/现价）+
  心法第 5 条的提醒。**用 `stop_alerted` 标记保证只响一次**（否则每小时刷屏）。
- **时间标记只写一次**：`1h/6h/24h` 三个 mark 在首次达到该年龄时落库，之后不再覆盖——
  这样事后看得到「买入后 1 小时是什么状态」，不受后续刷新污染。
- **report 的输出顺序**：胜率 → 平均盈亏 → **单笔期望值**（"正数才值得继续打"）→
  **按标签的期望值排序（最差在前）** → 纪律检查（没写离场计划 N 笔 / 入场快照缺失 N 笔）。

## 坑（实测）

- **GMGN `token info` 没有现成的 `market_cap` 字段** —— 必须自己算
  `price × circulating_supply`（`circulating_supply` 缺失时退回 `total_supply`）。
  直接取 `price.market_cap` 会静默拿到 0，标签也跟着错。
- **抓取失败不能中断记账**：GMGN 会偶发网络抖动/限流。抓不到就记一笔空快照并**明确提示**，
  仍然入库（有记录 > 没记录），report 里「入场快照缺失」会把这类点出来。
- **`no_agent` cron 的 `script` 参数不能传命令行参数** —— 所以 `update` / `report` 各需要一个
  极薄的包装脚本（`trade_update_cron.py` / `trade_report_cron.py`），内部 `subprocess.run([...])`
  带参数调用真脚本，有输出才 `print`，否则 stdout 为空（保持 cron 静默语义）。
- **最低摩擦的录入方式**：不要让用户记命令。他在 TG 里说一句
  「记一笔 FTR sol 仓位200 事件驱动，计划发布会当天减半」→ agent 翻译成 `add` 调用。
  摩擦决定这个闭环会不会被用起来。
- 平仓时若不传 `--price`，脚本按当前市价平——**市价平仓会随抓取时点漂移**，重要交易最好显式给价。

## 验证

```bash
jq -r '.trades[] | "\(.id) \(.sym) \(.status) \(.exit.pnl_pct // "-")"' ~/.hermes/trading/journal.json
```
