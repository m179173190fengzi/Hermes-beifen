---
name: crypto-market-data
category: research
description: Fetch and analyze cryptocurrency market data (BTC, ETH, altcoins) from public APIs. Present concise Chinese-language analysis with multi-currency pricing and market context.
triggers:
  - User asks for "行情", "币圈", "BTC", "Bitcoin", "crypto price", or any coin ticker
  - User requests market analysis or price checks on cryptocurrencies
---

# Crypto Market Data

Fetch real-time cryptocurrency prices and produce concise, Chinese-language market analysis.

## Data Sources (Preference Order)

### 1. Blockchain.info Ticker — **Primary** (no API key, always works)
```
curl -s --max-time 10 "https://blockchain.info/ticker"
```
Returns `{CURRENCY: {15m, last, buy, sell, symbol}}` for 30+ fiat currencies.
- No rate limiting issues, lightweight, returns raw JSON
- BTC only (not altcoins)
- Directly pipable to Python for reformatting

### 2. CoinGecko API (if available)
```
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,cny&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true"
```
- Returns 24h change %, volume, market cap
- Supports altcoins (ethereum, solana, etc.)
- May be rate-limited or blocked depending on proxy/env

### 3. Blockchain.info Stats (if available)
```
curl -s "https://api.blockchain.info/stats"
```
- Market cap, trade volume, hash rate,难度
- BTC only

## Presentation Format

Use a **table** for multi-currency price display, then **concise bullet-point analysis**.

### Required currencies for Chinese-speaking users
| Currency | Label |
|----------|-------|
| USD      | $     |
| CNY      | ¥     |
| EUR      | €     |
| JPY      | ¥     |
| HKD      | HK$   |
| KRW      | ₩     |
| GBP      | £     |
| SGD      | S$    |

### Analysis structure (keep brief)
1. Current price level and key support/resistance levels
2. Distance from ATH (All-Time High)
3. Market sentiment signal
4. Key factors to watch

## User Preferences

- User communicates in Chinese → respond in Chinese
- Keep analysis concise, no verbose explanations
- Present raw data directly with minimal filler text
- User may block arbitrary external API calls; prefer blockchain.info as fallback

## Pitfalls

- CoinGecko has Cloudflare protection when accessed via browser
- Binance.com returns empty page without JS rendering
- CoinMarketCap loads slowly and requires dynamic content
- User may deny repeated curl commands — batch all fetches in one call
- Browser-based approaches are slow and prone to timeout for data-fetching tasks; prefer curl to JSON APIs

## Solana On-Chain / Meme Coin Research

For Solana meme coin / 土狗 research — social alpha hunting via X/Twitter, on-chain supply queries, and Rugcheck risk scoring — see:

📄 `references/solana-meme-research.md`  
📄 `references/data-sources.md` — 含 DexScreener 代币名称搜索

## BSC Meme / Cross-Chain Imitation

**BSC meme trading is NOT standalone — it's a cross-chain copy of Solana narratives.** See:

📄 `references/bsc-meme-trading.md` — 跨链模仿逻辑、CZ 对位分析、BSC 特有工具

## Verification

After fetching data, always confirm:
- Price is recent (blockchain.info is near real-time)
- At minimum present BTC/USD and BTC/CNY for Chinese users

## Cross-Chain Meme Analysis Verification

When using BSC reference file for meme analysis:
1. **Always check Solana first** — BSC copies Solana narratives, not the other way around
2. **分层筛选** — Not all CZ tokens are equal; use the 3-layer framework
3. **Conspiracy pump check** — Check volume profile and time of day before recommending any 1h+500% token
