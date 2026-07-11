---
name: meme-coin-analysis
description: >
  Multi-chain meme coin market analysis — cross-chain narrative flow (Solana KOL → BSC CZ imitation),
  conspiracy pump (阴谋盘) detection via kline data, KOL/smart-money tracking, and entry/exit logic.
  Uses GMGN CLI + DexScreener API for on-chain data.
---

# Meme Coin Market Analysis

## Core Rule: Cross-Chain Narrative Imitation

BSC meme coin narratives **imitate** Solana hot narratives with a chain-specific figure:

| Chain | Hot Narrative Figure | Role |
|:------|:--------------------|:-----|
| **Solana** | **Anselm** (Ansem) / KOL cluster | Origin — narrative leader |
| **BSC** | **CZ** (Binance) | Mirror — same playbook, CZ-branded |

**Trigger pattern:** When a Solana KOL/narrative token starts pumping → within hours, BSC coins with CZ naming appear copying the same angle (e.g., Sultan on Sol → Sultan on BSC labeled with CZ theme).

**Required workflow before analyzing BSC:**
1. Check what's hot on Solana first (which KOL/narrative is driving it)
2. Predict the BSC CZ-clone of that narrative
3. Scan BSC trending for matching CZ tokens

## Conspiracy Pump (阴谋盘) Detection

### Red flags to look for in 15m kline data:

| Signal | What to check |
|:-------|:-------------|
| **Timing** | Pump at 04:00~06:00 Beijing time = retail asleep, orchestrated |
| **Volume spike** | Normal $500/candle → sudden $100K+ = not organic |
| **Vertical move** | >500% in <2 hours = coordinated |
| **Top10 holder rate** | >70% = controlled by few wallets |
| **Immediate dump** | Sell volume within 1 hour of peak = profit taking |

### GMGN kline query pattern:
```bash
gmgn-cli market kline --chain {bsc|sol} --address <token_address> --resolution 15m --from <unix_ts> --to <unix_ts> --raw
```

### Key quality metrics from GMGN trending:
- `top_10_holder_rate` — >50% is dangerous; <20% is healthy distribution
- `bundler_rate` — % of bundled buys at launch; <10% is clean
- `smart_degen_count` — smart money wallets in the coin; >10 is positive
- `renounced_mint` — 1 = mint revoked (good), 0 = can still print (dangerous)
- `entrapment_ratio` — insider/dev trap ratio; >0.7 is bad

## BSC Market Phase Detection

BSC cycles through three phases. Detect which phase you're in before making recommendations:

| Phase | Buy/Sell | Fresh Tokens (<2h) in Top20 | CZ Leader | Action |
|:------|:--------:|:---------------------------:|:----------|:-------|
| **CZ Frenzy** | > 2.0 | 3+ | +50%~+500% | Hunt low-cap CZ clones |
| **Cooling** | 1.0~1.3 | 0~1 | -5%~-15% | DON'T chase — wait for next narrative |
| **Vacuum** | ≈ 1.0 | 0 | Flat/slow bleed | Skip BSC, watch Solana |

**Quick judgment flow when user says "BSC怎么样":**
1. Check Buy/Sell ratio from trending data
2. Check age distribution of top tokens (are there fresh <2h tokens?)
3. Check CZ leader price direction (up, down, flat?)
4. Classify the phase, then adjust recommendation

See `references/bsc-market-phase-analysis.md` for full framework.

## KOL / Smart Money Tracking Tools

| Tool | What it shows | Best for |
|:-----|:-------------|:---------|
| **GMGN** (gmgn.ai / gmgn-cli) | Smart money buys, trending, token signals, wallet tracking | Real-time on-chain data, signals |
| **Scopechat** (0xScope) ⭐ | **KOL wallet labels on X/Twitter** (🐋Whale, 👑SmartMoney, 🎙️KOL) | 🔴 **KOL verification on social — this is the one the user uses** |
| **DexScreener** | Multi-chain DEX data, token search | Initial discovery, price data |
| **Birdeye Extension** | Wallet labels on X + charts | Alternative to Scopechat |

⚠️ **User note:** The user does NOT use GMGN's browser extension. When they say "X名人插件" they mean **Scopechat (0xScope)**, not GMGN. Do NOT suggest GMGN Extension for Twitter KOL labels — it's been corrected before. Scopechat is the correct tool (Chrome Web Store ID: `akbkkmniehbjngifggfadbgmojbgonmf`).

## Entry/Exit Logic (meme coin)

Applying "看大做小" to meme coins:
1. **Higher TF confirmation** — Check Solana trending first for narrative direction
2. **Descend to BSC** — Find the CZ clone of the same narrative
3. **Quality check** — Low Top10 rate + high smart money + renounced mint
4. **Entry** — After first pump dump, look for consolidation at support level
5. **Exit** — Monitor for declining volume or Top10 holders distributing

## Cross-chain analysis: BSC always references Solana

When asked about BSC market:
- DON'T just list BSC trending tokens in isolation
- DO first check what KOL/narrative is driving Solana
- THEN map which BSC tokens are the CZ-clone of that narrative
- Explain the connection explicitly in the analysis

## References

- `references/cz-final-form-bull-pump-analysis.md` — Full kline breakdown of the CZ (Final Form Bull) Jul 4 conspiracy pump
- `references/bsc-market-phase-analysis.md` — BSC 市场情绪三阶段模型：狂潮期/冷却期/真空期判断框架
