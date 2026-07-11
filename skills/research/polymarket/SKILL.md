---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history."
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
platforms: [linux, macos, windows]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible

## AI Prediction Market Analysis

When a user asks about prediction market strategies (especially for high-volume events like the FIFA World Cup or US elections), apply this framework:

### Core Logic: Find Pricing Discrepancies

```
AI-calculated probability  ≠  Market price
        60%                ≠        45%
                    ↓
            Mispricing of 15% → potential edge
```

### Four Strategy Patterns

1. **Value investing (find under-priced outcomes):** Look for assets where market odds seem too low given fundamentals. Example: USA at 3.0% to win the 2026 World Cup as a co-host seems undervalued vs historical host advantage (~10-15%).

2. **Short over-priced outcomes:** Some markets have absurdly high "No" prices (99.9%) for impossible outcomes. These are low-yield but near-zero-risk trades.

3. **Event-driven arbitrage:** Major news (injuries, political scandals, economic data) instantly shifts probabilities. Monitor live feeds and compare to market prices before they adjust.

4. **Dynamic hedging:** If you hold a position and the price moves in your favor, take profit in tranches — don't hold to expiration.

### World Cup Market Example (June 2026, $3.2B volume)

| Team | Market Odds | AI Assessment |
|------|------------|---------------|
| France | 18.9% | Strongest on paper, but defending champion curse |
| Argentina | 15.2% | Recent winner, aging core? |
| Spain | 13.8% | Always competitive |
| England | 10.2% | Good squad, history of underperformance |
| Brazil | 5.5% | Seems low — historically always competitive |
| **USA** | **3.0%** | **Co-host — historical host advantage suggests 10-15%** |
| Minnows | 0.1-1% | Mathematically impossible for most |

**Key insight:** The biggest mispricing is usually in the mid-tier teams, not the favorites. The crowd overweights narratives (Messi, Ronaldo) and underweights structural advantages (host nation, group draw).

### When the user asks about prediction markets

1. Search Polymarket for the relevant event
2. Show current odds as percentages with volume
3. Identify the top 3-5 outcomes and offer AI analysis on which seem mispriced
4. Offer to set up a cron job to monitor specific markets periodically
