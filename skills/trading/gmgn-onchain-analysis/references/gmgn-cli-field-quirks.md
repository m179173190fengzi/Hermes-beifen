# gmgn-cli 字段与参数坑（实测汇总）

用这些字段前先看这里，能省掉一整轮「拿到数据但解析为空」的调试。

## 链名参数

```
sol / bsc / base / eth / arbitrum / hyperevm / robinhood / arc / stable
```

- **`--chain solana` 直接报错**：`Invalid chain: "solana". Must be one of: sol, bsc, ...`
- 记法：命令行里永远是 **sol**，接口返回里才叫 solana。

## `token info --raw` 的关键缺失字段

**没有 `market_cap` 字段**（有 `migration_market_cap`，那是迁移时的池子市值，不是当前 MC）。

MC 必须自己算：

```python
px = float((j.get("price") or {}).get("price") or 0)
supply = float(j.get("circulating_supply") or j.get("total_supply") or 0)
mc = px * supply
```

`price` 子对象里可用的字段（实测）：

```
price / price_1m / price_5m / price_1h / price_6h / price_24h
volume_1m / volume_5m / volume_1h / volume_6h / volume_24h
buy_volume_1m ...        buys_1m / buys_1h / buys_24h / sells_*
```

其它可用顶层字段：`circulating_supply` / `total_supply` / `max_supply` / `ath_price` /
`liquidity` / `holder_count` / `creation_timestamp` / `open_timestamp` / `launchpad_platform` /
`launchpad_progress` / `launchpad_status` / `locked_ratio` / `link.{website,twitter_username}` /
`dev.{creator_open_count,creator_token_status}` / `stat.{top_10_holder_rate,top_bundler_trader_percentage,top_entrapment_trader_percentage}`

## 各子命令的返回形状不同（容易写成同一个假设）

| 命令 | 返回 |
|---|---|
| `market trending` | `{"data":{"rank":[...]}}` |
| `market hot-searches` | **数组** `[{"interval","chain","tokens":[...]}]`（不是 .data） |
| `token info` | 扁平对象（无 code/data 包裹） |
| `token holders` | `{"list":[{address, addr_type, amount_percentage, usd_value, ...}]}` |
| `portfolio activity` | `{"activities":[{event_type:"buy"/"sell", token:{address,symbol}, cost_usd, timestamp, ...}]}` |

## 参数名坑

- `portfolio activity` 要 **`--wallet <地址>`**，用 `--address` 会报 `required option '--wallet <address>' not specified`
- `token info` / `token holders` / `token security` 用 `--address`
- `portfolio activity` 对**未被 GMGN 索引的地址**返回空数组（不是报错）——fomo 个人主页地址常常是空的，
  要用其**链上交易钱包**才有数据

## 静默失败

偶发把 stdout 写成 0 字节（进程返回 0 但无输出），典型是网络/代理瞬断。
→ 解析前判空 + **重试 1-2 次**，别把它当成「这个币没数据」。

## `market trenches` 是性价比最高的扫描源（一个调用够打分）

返回 `{"new_creation":[...], "near_completion":[...], "completed":[...]}`（三个分类各一个数组）。
**每个 token 已自带全部打分字段**，不需要再逐币调 `token info`：

```
address / symbol / name / market_cap / liquidity / holder_count / volume_24h / net_buy_24h
top_10_holder_rate / bundler_trader_amount_rate / entrapment_ratio / rat_trader_amount_rate
top70_sniper_hold_rate / suspected_insider_hold_rate / bot_degen_rate / fresh_wallet_rate
creator_created_count / creator_token_status / creator_balance_rate
is_honeypot / burn_status / open_source / owner_renounced / buy_tax / sell_tax
twitter / twitter_handle / website / telegram / x_user_follower
created_timestamp / open_timestamp / complete_timestamp
smart_degen_count / renowned_count / launchpad_platform / launchpad_status / progress
```

→ 双链日报只需 **2 次 trenches + 2 次 trending**，就能完成"扫描 + 硬门槛 + 11 项打分 + 去重"。
（对比：让 agent 自己扫 trending 再逐币 `token info`，36 次调用 → 上下文塞满 raw JSON。）

## 布尔字段是字符串 `"no" / "yes"`，不是 0/1

实测 `is_honeypot="no"`、`burn_status="yes"`（**字符串**）。
按 `honey in (0,"0",False,None)` 判断会把**每一个** flap 盘都误判成蜜罐、每个盘都报"LP 未烧"。
正确写法：

```python
honey_ok = str(t.get("is_honeypot", "")).lower() in ("no", "0", "false", "none", "")
burn_ok  = str(t.get("burn_status", "")).lower() in ("yes", "y", "burned", "burn", "locked")
```

## `market trending` 的涨跌幅**已经是百分数**

`price_change_percent`, `price_change_percent1h` 的值（如 `-0.0032`、`-98.66`）已经是以 % 为单位，
**不要再 ×100**（×100 会把 -98.66% 显示成 -9866%）。
该接口字段比 trenches 少（无 bundle/围猎/dev 发币数），只适合做"热度榜/叙事参考"，不适合打分。

## 429 封禁：重试会**延长**封禁时间

错误体：

```
[gmgn-cli] POST /v1/trenches failed: HTTP 429 code=429 error=RATE_LIMIT_BANNED
message=IP is temporarily banned due to repeated rate limit violations.
Rate limit resets at 2026-10-18 20:22:35 GMT+08:00 (~29s remaining).
Stop sending requests before then; repeated requests can extend the ban by 5s up to 5 minutes.
```

规则：
1. **每条新请求把封禁 +5s（最多 5 分钟）** → 快速重试 = 自己把坑挖深，最后整轮扫描全废。
2. 退避必须读 `~Ns remaining`，等 `N + 10~15s` 再试；**两次调用之间至少留 6s 间隔**（脚本里做全局 gap）。
3. 限流的连带伤害：批量扫描时会把"所有候选"都变成空 → 误判成"今天全是垃圾/没有机会"。
   看到整链 0 候选，先怀疑限流，别下市场结论。
4. 网络类错误（`Client network socket disconnected before secure TLS connection was established`、
   `fetch failed`）**不是限流**，也要重试（间隔 5-6s），否则会把整链静默跳过。

## ticker 歧义（必须先用 CA 固定）

同一个 ticker 在不同链/不同发射台是完全不同的东西，实测：
`FTR` 在 BSC 上是 `flap_stocks` 的股票主题盘（MC ~$12K、无官网），
在 SOL 上是 `Flying Tesla Roadster`（pump.fun，MC 数百万）。

→ **永远先用 CA 确认链和标的**，再讨论"这个币怎么样"。
用户说"我说的是 sol 上 FTR"这类纠正，就是踩了这个坑。
