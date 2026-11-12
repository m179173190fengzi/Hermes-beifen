# GMGN 字段避坑（实测 2026-10）

不同端点对同一概念用**不同字段名**，且部分值是字符串不是数字。踩过的坑都在这。

## 1. `market trenches` 一次调用就够打分（省 API 和大把 token）

```bash
gmgn-cli market trenches --chain bsc --type new_creation --type near_completion --type completed --limit 40 --raw
# 返回: {new_creation:[...], near_completion:[...], completed:[...]}
```

每条已包含全部打分要素，**不需要再对每个币调 `token info`**：

| 用途 | 字段 |
|---|---|
| 市值/流动性/量 | `market_cap` / `liquidity` / `volume_24h` / `net_buy_24h` |
| 筹码 | `top_10_holder_rate` / `top70_sniper_hold_rate` / `suspected_insider_hold_rate` |
| 关联盘 | `bundler_trader_amount_rate` / `entrapment_ratio` / `rat_trader_amount_rate` |
| dev | `creator_created_count` / `creator_token_status` / `creator_balance_rate` |
| 安全 | `is_honeypot` / `open_source` / `owner_renounced` / `burn_status` / `buy_tax` / `sell_tax` |
| 社交 | `twitter` / `twitter_handle` / `website` / `x_user_follower` / `x_user_following` |
| 时间/台子 | `created_timestamp` / `open_timestamp` / `launchpad_platform` / `launchpad_status` / `progress` |
| 聪明钱 | `smart_degen_count` / `renowned_count` / `bot_degen_rate` / `fresh_wallet_rate` |

### ⚠️ 值是字符串，不是数字

```
is_honeypot = "no"     # 不是 0 / False
burn_status = "yes"    # 不是 "burned" / 1
```

用 `str(v).lower() in ("no","0","false","none","")` 判安全，
`str(v).lower() in ("yes","y","burned","burn","locked")` 判已烧池。
**按整数比会 100% 误判**：全部 BSC flap 币会被标成"蜜罐 + LP 未烧"。

## 2. `token info` 没有 market_cap 字段

```python
mc = price.price * circulating_supply     # 必须自己算
```
`ath_price`、`liquidity`、`holder_count`、`locked_ratio`、`circulating_supply` 都有。
`stat` 下是 `top_10_holder_rate` / `top_bundler_trader_percentage` / `top_entrapment_trader_percentage` / `top_rat_trader_percentage`（**注意和 trenches 的命名不同**）。
`dev` 下是 `creator_open_count` / `creator_token_status`（`creator_hold` = dev 还持仓 = 潜在抛压）。

## 3. 涨跌幅要自己算

`token info` 的 `price` 对象里给的是**历史价格**：`price_1h` / `price_6h` / `price_24h`。
涨跌幅 = `now/ref - 1`。`price_change_percent1h` 这类字段在 token info 里常年缺失（返回 0）。

`market trending` 的 `price_change_percent1h` **已经是百分数**（-98.66 就是 -98.66%），**不要再 ×100**。

## 4. `market trending` 的返回结构

```json
{"code":0, "data": {"rank": [ {address, symbol, market_cap, liquidity, volume, holder_count,
                               top_10_holder_rate, price_change_percent1h, creation_timestamp, ...} ]},
 "message":"success"}
```
→ 取 `data.rank`。trending 的字段比 trenches 少（没有 bundle/围猎/dev/honeypot），
**买盘判断用 trenches，热度参考用 trending**。
榜单里会混进"代币化股票"（AAPLB / NVDAB / QQQB）和 MC≈0 的垃圾盘，按 `market_cap >= 100_000` 过滤。

## 5. 其它

- `portfolio activity --chain sol --wallet <地址> --raw` → `{activities:[{event_type:"buy"/"sell", token:{address,symbol}, cost_usd, timestamp}]}`
  **参数是 `--wallet`，不是 `--address`**；传错会静默返回空数组。可用于任意地址的交易历史。
- `token holders --chain bsc --address <CA> --limit 100 --raw` → `{list:[{address, amount_percentage, usd_value, ...}]}`（做聪明钱地址库交集用）
- 链名必须是 `sol` / `bsc` / `base` / `eth`，**`solana` 会报错**。
- 429 封禁：错误串里有 `Rate limit resets at ... (~Ns remaining)`；**每次重试会把封禁再延长 5 秒**（上限 5 分钟）。调用间隔 ≥6 秒，重试按提示等待。
