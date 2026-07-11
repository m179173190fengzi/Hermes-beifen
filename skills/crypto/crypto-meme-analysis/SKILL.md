---
name: crypto-meme-analysis
description: "Chain meme coin analysis: scan, score, narrative mapping, and auto-alert workflow for Solana/BSC/Robinhood Chain. Combines on-chain data with social sentiment and cross-chain imitation logic."
version: 1.0.0
author: Hermes
license: MIT
category: crypto
platforms: [linux, macos]
metadata:
  hermes:
    tags: [meme, token, scoring, gmgn, dexscreener, robinhood, solana, bsc]
---

# Crypto Meme Coin Analysis

Comprehensive framework for analyzing and trading meme coins across chains.

## When to Use

Run this workflow when the user asks:
- "分析这个地址" / "analyze this address"
- "扫Solana链" / "scan Solana chain"
- "Robinhood链有什么新币" / "new tokens on Robinhood"
- "这个币能不能打" / "is this token worth trading"

## Core Analysis Flow

### 0. Pre-check: Cross-Chain Imitation Logic

Before analyzing any chain, check the lead chain first:
- **Solana hype** (Ansem/KOL narrative) → **BSC imitates with CZ narrative**
- **Robinhood Chain** → independent narrative ecosystem (see Robinhood narrative reference)

Always ask: "What's hot on Solana right now?" before analyzing BSC.

### 1. Data Collection

Collect from all available sources:

```bash
# GMGN trending
gmgn-cli market trending --chain sol|bsc|robinhood --interval 1h --limit 30

# GMGN token info (if supported)
gmgn-cli token info --chain sol --address <ADDRESS>

# DexScreener via API
curl -s "https://api.dexscreener.com/latest/dex/search?q=<SYMBOL>"

# Twitter search
twitter search "<SYMBOL> <CHAIN> -is:retweet"

# Blockscout for Robinhood Chain
# https://robinhoodchain.blockscout.com/address/<ADDRESS>
```

### 2. Scoring System (0-100 composite)

Score each token across 4 dimensions:

| Dimension | Weight | Data Source |
|-----------|--------|-------------|
| **Deployer Quality** | 30% | GMGN: Bundle rate, creator history, renounced mint |
| **Smart Money Quality** | 25% | GMGN: smart_degen_count, renowned_count |
| **On-Chain Health** | 25% | GMGN: Top10%, liquidity, lock status |
| **Trading Activity** | 20% | GMGN: volume, buy/sell ratio, holder growth |

**Scoring thresholds:**
- 85-100: 🟢 HIGH CONFLUENCE — alert user
- 70-84: 🟡 WATCH — note for next scan
- 50-69: 🟠 OBSERVE — needs more data
- 0-49: 🔴 SKIP — too risky

**Scoring criteria:**

Deployer Quality:
- Bundle < 10% = 90pts, < 20% = 70pts, < 30% = 50pts, > 30% = 20pts
- Renounced mint = +10pts
- Creator closed/divested = +10pts

Smart Money Quality:
- 5+ smart = 90pts, 3-4 = 70pts, 1-2 = 50pts, 0 = 10pts
- Each KOL/renowned adds 5pts

On-Chain Health:
- Top10 < 20% = 90pts, < 40% = 70pts, < 60% = 50pts, > 60% = 20pts
- Liquidity > $50K = 90pts, > $20K = 70pts, > $10K = 50pts
- Locked liquidity = +10pts

Trading Activity:
- Volume/MC ratio > 1.0 = 90pts, > 0.5 = 70pts, > 0.1 = 50pts
- Buy/Sell ratio > 1.5 = 90pts, > 1.0 = 70pts
- Holder growth (increasing) = +10pts

### 3. Narrative Mapping

For Robinhood Chain, map to the 3-layer narrative framework:

**🟠 Pure Meme (89% of MC):** Robinhood self-reference
- Company lore: $CASHCAT, $JUGGERNAUT, $KITSU, $FIDEL, $WALLET, $1, $4663, $CONFETTI
- HOOD puns: $HOODRAT, $ROB, $MARIAN, $DIH
- WSB memory: $TENDIES, $GME

**🔵 HOOD Dual Meaning / Robinhood Legend (10%):** "Takes from the rich, gives to the poor"
**🟡 WSB Retail Memory (1%):** GME saga, 2021 nostalgia

For Solana: Check Ansem narrative (e.g., $SULTAN)
For BSC: Check CZ narrative (mirrors Solana narrative)

### 4. Trading Advice

**Entry:**
- MC < $1M: high risk/reward, small position
- MC $1-10M: moderate, can scale in
- MC > $10M: mature, less upside

**Stop-loss:** -20% hard stop (user's rule — NEVER waive)
**Take-profit:** 2x sell 1/3, 5x sell 1/3, 10x exit

### 5. Auto-Scan Cron Workflow

When setting up cron jobs, use **fixed times NOT intervals** (user preference):
- Timing: 6:00 / 11:00 / 15:00 / 19:00 / 22:00
- Data sources: GMGN trending + DexScreener + Twitter CLI + DeFiLlama TVL

## User Preferences (Critical)

- Communicates in Chinese, prefers Chinese responses
- Has V4 strategy: 6 MAs (SMA20/60/120+EMA20/60/120) — NEVER change periods
- 看大做小: check higher TF direction → descend to lower TFs for entry
- Bear market: short-only
- Sleeps 0-6 AM: all cron jobs paused
- Budget-conscious: prefers free tools over paid memberships
- Reference charts: BTC preferred, NOT ETH
- **NEVER connect to 智谱AI API** — user explicitly rejected this
- **NEVER suggest car/car-system topics** — user explicitly said "不要提这个话题"
- Direct replies, no sugar-coating, no over-explaining
- When corrected: STOP guessing, re-read literally
- No real-money trades without explicit approval

## References

See `references/` directory for:
- `robinhood-narrative-map.md` — Full Robinhood Chain narrative analysis
- `token-scan-checklist.md` — Detailed 8-step token evaluation checklist
- `cross-chain-imitation.md` — Solana→BSC→Robinhood narrative mirroring patterns
