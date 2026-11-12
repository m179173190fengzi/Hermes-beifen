# gmgn-cli 字段与限流实测（2026-10 校准）

实测环境：`gmgn-cli` v1.6.7，链名必须写 `sol` / `bsc` / `base` / `eth`（写 `solana` 会失败）。
所有命令加 `--raw` 才是 JSON；不加是给人看的表格。外网必须带 `HTTPS_PROXY=http://127.0.0.1:7890`。

## 1. `market trenches` —— 打狗筛选的单次最优数据源

```bash
gmgn-cli market trenches --chain bsc \
  --type new_creation --type near_completion --type completed \
  --limit 40 --raw
```

- `--type` 可重复传多个（不要用逗号拼）。
- 返回对象三个键：`new_creation` / `near_completion` / `completed`，各是数组。
- **每个条目自带 ~80 个字段，足够做完 11 项打分，不需要再逐币调 `token info`。**
  常用字段：

| 用途 | 字段 |
|---|---|
| 规模 | `market_cap`, `liquidity`, `holder_count`, `volume_24h`, `net_buy_24h` |
| 筹码 | `top_10_holder_rate`, `bundler_trader_amount_rate`, `entrapment_ratio`, `rat_trader_amount_rate`, `top70_sniper_hold_rate`, `suspected_insider_hold_rate` |
| dev | `creator_created_count`, `creator_token_status`, `creator_balance_rate` |
| 安全 | `is_honeypot`, `burn_status`, `owner_renounced`, `buy_tax`, `sell_tax` |
| 社交 | `twitter`, `twitter_handle`, `website`, `telegram`, `x_user_follower` |
| 时间/台子 | `created_timestamp`, `open_timestamp`, `launchpad_platform`, `launchpad_status`, `progress` |
| 资金属性 | `smart_degen_count`, `renowned_count` |

### ⚠️ 两个布尔字段是字符串
```
is_honeypot: "no" / "yes"      burn_status: "yes" / "no"
```
用 `if honeypot in (0, False, None)` 判断会让**所有币都被误判成蜜罐**；
同样 `burn_status == "yes"` 才代表 LP 已烧。判据写 `str(v).lower() in ("no","0","false","none","")`。

## 2. `market trending` —— 只有热度，没有结构

```bash
gmgn-cli market trending --chain sol --interval 6h --limit 30 --order-by volume --raw
```
- 返回结构是 `{"code":0,"data":{"rank":[...]},"message":"success"}` —— **列表在 `data.rank`**，不是 `data` 本身。
- 字段：`market_cap`, `liquidity`, `volume`, `swaps/buys/sells`, `holder_count`,
  `top_10_holder_rate`, `price_change_percent1m/5m/1h`, `history_highest_market_cap`。
- **没有 bundle / entrapment / dev 发币数 / 社交** → 不能用 trending 单独打分，只能当「热度参考」。
- `price_change_percent1h` **已经是百分数**（`-0.003` = −0.003%），再 ×100 会放大 100 倍。
- 榜单会被「代币化股票」（pPOLY / NVDAB / QQQB 等）和 MC≈0 的垃圾盘污染，展示前先过滤 `mc >= 100_000`。

## 3. `token info` —— 没有 market_cap 字段

```bash
gmgn-cli token info --chain sol --address <CA> --raw
```
- **MC 必须自己算**：`price.price × circulating_supply`（无 `market_cap` 键；`migration_market_cap` 是另一回事）。
- 成交量字段是 `price.volume_24h`。
- 涨跌幅也没有现成的百分比字段，要用历史价算：`price_1h` / `price_6h` / `price_24h`
  → `chg = price / price_1h - 1`。
- SOL 侧安全字段：`locked_ratio`（0 = 未锁）、`stat.top_10_holder_rate`（字符串）、
  `stat.top_bundler_trader_percentage`、`stat.top_entrapment_trader_percentage`、
  `dev.creator_open_count`、`dev.creator_token_status`（`creator_hold` = 还拿着）。

## 4. `token holders` —— 用于与外部聪明钱库求交集

```bash
gmgn-cli token holders --chain bsc --address <CA> --limit 100 --raw
```
返回 `{"list":[{"address","balance","usd_value","amount_percentage",...}]}`。
把 `address` 小写后与本地地址库（如 `~/.hermes/cron/state/smart_money_evm.json`，449 个 o皇库地址）
求交集即可做「聪明钱是否在买」的加分项。命中天然低频（几百个地址 vs 前 100 持仓），
**命中 0 是正常结果，不是 bug**——要先用注入测试验证逻辑本身没问题。

## 5. 限流：重试会延长封禁

```
[gmgn-cli] POST /v1/trenches failed: HTTP 429 code=429 error=RATE_LIMIT_BANNED
message=IP is temporarily banned ... resets at 2026-10-18 20:22:35 GMT+08:00 (~29s remaining).
Stop sending requests before then; repeated requests can extend the ban by 5s up to 5 minutes.
```

- **每次重试都把封禁延长 5 秒**（上限 5 分钟）→ 无脑重试会陷入死亡螺旋。
- 可用做法：两次调用之间 **≥6 秒**；遇 429 解析 `~(\d+)s remaining`，sleep `remaining + 12`（上限 120s）再试。
- 单次任务 4 个调用（2×trenches + 2×trending）配 6 秒间隔是安全的；**调试时不要手敲同一个接口反复试**。
- 除 429 外还要重试这些：`fetch failed` / `TLS` / `socket disconnected` / `ECONNRESET` / `502/503`。
  只判断 `429` 会让整条链静默返回「扫描 0 个」。

## 6. 命令选择速查

| 想要 | 用 |
|---|---|
| 新盘/毕业盘 + 完整结构字段 | `market trenches` |
| 热度/成交量榜（叙事参考） | `market trending` |
| 单币详情/安全/社交 | `token info` |
| 持仓地址（配聪明钱库） | `token holders` |
| 钱包盈亏/胜率 | `portfolio stats` / `portfolio activity --wallet`（注意是 `--wallet` 不是 `--address`） |
