# Crypto Data Source Reference

## blockchain.info/ticker — 已验证可用

**Endpoint:** `GET https://blockchain.info/ticker`

**验证时间:** 2026-06-24

**返回示例 (节选):**
```json
{
  "USD": {"15m": 62596.94, "last": 62596.94, "buy": 62596.94, "sell": 62596.94, "symbol": "$"},
  "CNY": {"15m": 425778.14, "last": 425778.14, "buy": 425778.14, "sell": 425778.14, "symbol": "¥"},
  "EUR": {"15m": 55257.76, "last": 55257.76, "buy": 55257.76, "sell": 55257.76, "symbol": "€"},
  "JPY": {"15m": 10123913.03, "last": 10123913.03, "buy": 10123913.03, "sell": 10123913.03, "symbol": "¥"},
  "HKD": {"15m": 490754.39, "last": 490754.39, "buy": 490754.39, "sell": 490754.39, "symbol": "HK$"},
  "KRW": {"15m": 96845599.68, "last": 96845599.68, "buy": 96845599.68, "sell": 96845599.68, "symbol": "₩"},
  "GBP": {"15m": 47618.25, "last": 47618.25, "buy": 47618.25, "sell": 47618.25, "symbol": "£"},
  "SGD": {"15m": 81317.81, "last": 81317.81, "buy": 81317.81, "sell": 81317.81, "symbol": "S$"}
}
```

**Notes:**
- 30+ fiat currencies returned
- `15m` = 15-minute delayed price, `last` = last trade price (near real-time)
- Buy/sell prices are identical in this API
- No API key needed
- BTC only — does not support altcoins
- Fast, lightweight, no Cloudflare

## CoinGecko API — 可能被拦截

**Endpoint:** `GET https://api.coingecko.com/api/v3/simple/price`

**参数示例:**
```
ids=bitcoin&vs_currencies=usd,cny&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true
```

**Notes:**
- 支持多币种（bitcoin, ethereum, solana, dogecoin 等）
- 提供 24h 涨跌幅、成交量、市值等丰富数据
- CoinGecko 网页端有 Cloudflare 防护
- API 请求在部分代理环境下可能被用户拒绝

## blockchain.info/stats — 待验证

**Endpoint:** `GET https://api.blockchain.info/stats`

**Notes:**
- 返回 BTC 的总市值、交易量、算力等
- 可能被用户拒绝，视环境而定

## Sites with Bot Detection (避免使用浏览器爬取)

| 站点 | 问题 |
|------|------|
| CoinGecko | Cloudflare 人机验证 |
| CoinMarketCap | 动态加载 + 速度慢 |
| Binance | 空页面，需 JS 渲染 |
| OKX /price/* | 404 页面 |
| bitcoin.com | 超时 |

## DexScreener API — 已验证可用（代币/合约名称搜索，需代理）

**Endpoint:** `GET https://api.dexscreener.com/latest/dex/search?q={query}`

**验证时间:** 2026-07-01

**说明:**
- 按名称/符号搜索代币（如 `sultan`, `TATE`, `DADDY`），返回所有链上配对
- 无需 API Key，无 Cloudflare 防护
- 有 GFW 代理时加 `--proxy http://127.0.0.1:7890`
- 适合搜"不知道合约地址、只知道名字"的场景

**使用示例:**
```bash
curl -s --proxy http://127.0.0.1:7890 \
  "https://api.dexscreener.com/latest/dex/search?q=sultan" \
  -H "User-Agent: Mozilla/5.0"
```

**关键返回字段（按24h交易量降序排列的 pairs[]）:**
| 字段 | 说明 |
|------|------|
| `chainId` | 链（solana / bsc / ethereum） |
| `dexId` | DEX 名称 |
| `baseToken.address` / `.symbol` / `.name` | 代币信息 |
| `priceUsd` | 当前价格 |
| `fdv` | 完全稀释市值 |
| `liquidity.usd` | 流动性 |
| `volume.h24` | 24h 交易量 |
| `txns.h24.buys/.sells` | 24h 买卖笔数 |
| `priceChange.h1/.h6/.h24` | 涨跌幅 |
| `pairCreatedAt` | 创建时间（毫秒） |
| `info.socials` | 社交链接 |

**注意事项:**
- 同名不同合约可能混在结果里，需自行分析主盘
- 流动性极低（<$5K）的币交易量可能是刷的
- `pairCreatedAt` 是毫秒级，需 `/1000` 转秒
