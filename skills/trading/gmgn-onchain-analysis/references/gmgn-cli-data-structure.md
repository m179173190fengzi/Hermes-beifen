# GMGN CLI — Trending Data Structure

## `gmgn-cli market trending --raw` Output

```json
{
  "code": 0,
  "data": {
    "rank": [
      { /* TokenObject */ }
    ]
  },
  "message": "",
  "reason": ""
}
```

## Key TokenObject Fields for Analysis

| Field | Type | Meaning |
|-------|------|---------|
| `symbol` / `name` | string | Token ticker / full name |
| `address` | string | Contract address (CA) |
| `market_cap` | float | Current market cap (USD) |
| `volume` | float | 24h trading volume (USD) |
| `liquidity` | float | Pool liquidity (USD) |
| `price` | float | Current price (USD) |
| `price_change_percent` | float | Total price change % |
| `price_change_percent1h` | float | 1h price change % |
| `price_change_percent5m` | float | 5m price change % |
| `buys` / `sells` | int | 24h buy/sell tx count |
| `swaps` | int | Total 24h swaps |
| `holder_count` | int | Number of holders |
| `top_10_holder_rate` | float (0-1) | Top 10 holder concentration |
| `smart_degen_count` | int | Smart money wallets holding |
| `renowned_count` | int | KOL wallets holding |
| `bundler_rate` | float (0-1) | Bundle-bot trading ratio |
| `entrapment_ratio` | float (0-1) | Entrapment trading ratio |
| `rug_ratio` | float (0-1) | Rug pull risk score |
| `renounced_mint` | 0/1 | Mint authority renounced |
| `launchpad` | string | e.g. "pump" for Pump.fun |
| `open_timestamp` | int | Unix timestamp of creation |
| `creator_token_status` | string | "creator_hold" / "creator_close" |
| `is_wash_trading` | bool | Wash trading flag |
| `rank` | int | GMGN ranking position |
| `gas_fee` | float | Total gas fees (SOL) |
| `twitter_username` | string | Associated X/Twitter |
| `telegram` | string | Telegram link (if any) |
| `website` | string | Website URL (if any) |
| `top70_sniper_hold_rate` | float (0-1) | Top 70 sniper holding ratio |
| `dev_team_hold_rate` | float (0-1) | Dev team holding ratio |
| `bot_degen_count` | int | Bot/degen wallet count |
| `visiting_count` | int | Unique visitors |

## Usage Pattern

```bash
gmgn-cli market trending --chain sol --interval 1h --limit 10 --raw | \
  python3 -c "
import json,sys
d = json.load(sys.stdin)
items = d['data']['rank']
for t in items:
    print(t['symbol'], t['market_cap'])
"
```

## Available Interval Options

- `1m` — Hottest right now (most volatile)
- `5m` — Short-term momentum
- `1h` — Default for trending analysis
- `6h` — Sustained trend
- `24h` — Daily overview

## Platform Filters

Solana: `Pump.fun`, `letsbonk`, `moonshot_app`, `meteora`
BSC: `fourmeme`, `openfour`, `flap`, `goplus_creator`
Base: `clanker`, `flaunch`, `zora`
ETH: `trench`, `clanker`, `klik`, `livo`, `pool_uniswap_v2`

---

## ⚠️ Hot-Searches vs Trending: 两种不同的数据结构

`gmgn-cli market hot-searches --raw` 的响应结构 **与 trending 完全不同**。这是最常见的解析错误来源。

| 命令 | 顶层结构 | Token 数组位置 | 解析路径 |
|------|----------|---------------|----------|
| `market trending --raw` | `{"code":0,"data":{"rank":[...]}}` | `data.rank` | `data['data']['rank']` |
| `market hot-searches --raw` | `[{"chain":"sol","tokens":[...]}]` | 顶层 list 的每个元素的 `tokens` 字段 | 直接遍历顶层 list |

### Hot-Searches 完整解析示例

```python
import json

with open("/tmp/sol_hot.json") as f:
    data = json.load(f)  # data 是一个 list

for block in data:
    chain = block["chain"]
    interval = block["interval"]
    tokens = block["tokens"]  # RankItem 数组
    for token in tokens:
        print(
            token["rank"],
            token["symbol"],
            token["market_cap"],
            token.get("visiting_count", 0)  # 热度的核心字段
        )
```

### Hot-Searches 特有字段

| 字段 | 说明 |
|------|------|
| `visiting_count` | 搜索/访问热度（排名依据，不像 `volume` 那样是交易量） |
| `rank` | 该 chain+interval 组内的排名（1-based） |

其余字段（`symbol`, `address`, `market_cap`, `volume`, `liquidity`, `smart_degen_count` 等）与 trending 的 `RankItem` 完全一致。
