---
name: cross-chain-meme-kol-analysis
description: Cross-chain KOL imitation pattern for meme coin trading. Solana KOL narratives (Ansem/Sultan/etc.) drive BSC CZ-counterpart copies. Includes conspiracy pump detection, GMGN data workflow, and user's preferred analysis style.
version: "2.0"
author: hermes
tags:
  - meme
  - KOL
  - cross-chain
  - solana
  - bsc
  - conspiracy-pump
  - sentiment
trigger: User asks about trending meme coins, BSC/Solana market analysis, or "what's the angle" on a hot token.
---

# Cross-Chain Meme KOL Analysis

## Core Pattern: KOL Imitation Across Chains

The user taught this pattern. It is NOT obvious from raw market data — it requires knowing the social layer:

```
Solana hot narrative (KOL: Ansem/安塞姆, Sultan)
        ↓
BSC community identifies the CZ-counterpart
        ↓
Tokens minted on fourmeme (BSC pump.fun equivalent)
        ↓
Cross-chain imitation drives the hype cycle
```

### Examples
- **Solana**: Ansem / Sultan / KOL-driven narratives
- **BSC counterpart**: CZ / CZ ARMY / HEYI / The Final Form Bull
- **Timing**: BSC tokens appear within hours of Solana narrative heating up

### Analysis Workflow

1. **Check Solana first** — What KOL narrative is trending? (GMGN trending Solana)
2. **Identify the KOL** — Ansem, Sultan, etc. Which persona is being hyped?
3. **Check BSC for CZ-counterpart** — Same narrative but CZ-branded
4. **Evaluate the BSC copy** — Use GMGN data:
   - Top10 holder rate (if >50% = conspiracy pump risk)
   - Bundle rate
   - Smart Money count
   - Age (newer = higher risk)
   - Buy/Sell ratio

### 看大做小 — Gradual Descent Framework

The user explicitly taught this as a **gradual descent** pattern — NOT a fixed timeframe ladder like "4h→1h→15m":

1. Identify the macro narrative direction (Solana KOL → BSC CZ counterpart)
2. Find ALL tokens under that narrative on BSC  
3. Filter by quality metrics (Bundle < 20%, Top10 < 50%, Smart Money > 0, Liq > $10K)
4. Descend through timeframes until finding a smooth entry (no fixed combination — it depends on the chart)
5. Entry at the micro level on the cleanest token
6. Exit on volume collapse (-80% from peak) or -20% stop loss

**Key correction:** No "check 4h first then 1h then 15m" — just drill down gradually. The right timeframe is whatever the chart shows, not a predetermined ladder.

## 4-Stage Conspiracy Pump Lifecycle

Every conspiracy pump follows this lifecycle. Stage 4 is the exception, not the rule.

| Stage | Timing | Price Action | Volume Pattern | User Action |
|:------|:-------|:-------------|:---------------|:------------|
| **1. Pre-pump** | Days/hours before | Low & stable ($0.0001-0.0002 range) | $500-8K/candle, no anomalies | Watch only |
| **2. The Pump** | 04:00-07:00 BJT | Vertical 1000-34000% in 1-2h | 100-1000x baseline, crescendo | DO NOT FOMO in |
| **3. The Dump** | Peak + 15min to 2h | -30% to -90% from peak | Sell volume exceeds buy volume at peak | If bought, sell into strength |
| **4. Aftermath** | Hours to days post-dump | Crash to near-zero OR recovery | Volume returns to baseline or grows | Watch for survivor patterns |

### Stage 4 — Survivability Signals (unusual but possible)

**Exception:** CZ (Final Form Bull) — conspiracy pump at 05:00 BJT, yet:
- Price recovered **above** pump peak ($0.050 vs $0.041)
- Holders doubled (4,636 → 10,633)
- Liquidity grew ($600K → $888K)
- Narrative (CZ/BSC) was strong enough to overcome conspiracy stigma

**When to treat a conspiracy pump as a potential survivor:**
1. Narrative strength — is the meme culturally sticky? (CZ/BSC ✓)
2. Holder growth — holders keep entering post-dump
3. Liquidity trend — not exiting but growing
4. Price holds above pre-pump baseline, not just pump peak

## Conspiracy Pump Detection Checklist

Classify as "阴谋盘" (conspiracy pump) when **3+ of these** are true:

| Signal | Indicator |
|:-------|:----------|
| ⏰ **Timing** | Pump initiated during 04:00-07:00 Beijing time (low retail activity) |
| 📈 **Magnitude** | >1000% vertical move in <2 hours |
| 💧 **Volume anomaly** | 100x+ increase from baseline volume |
| 👑 **Concentration** | Top10 holder rate >60% |
| 📊 **Pre-pump baseline** | Low liquidity (<$50K) and tiny volume before pump |
| 🎯 **Immediate sell-off** | Dump starts within 1-2 hours of peak |
| 🔗 **Cross-chain copy** | Token is a BSC copy of a Solana KOL narrative |

## BSC Sentiment Timing Model (Market-Cycle View)

The BSC meme market moves through sentiment phases. Each phase has specific characteristics:

| Phase | Sentiment | Buy/Sell Ratio | New Token Inflow | Action |
|:------|:----------|:--------------:|:----------------:|:-------|
| **🟢 Ignition** | Fresh FOMO | >1.5 | 3-5+ new tokens/hot in top 20 | Early entries on narrative leaders |
| **🟡 Peak Frenzy** | Max hype | >2.0 | Many copycats, CZ narratives dominate | Hold/partial exit; no new entries |
| **🔴 Cooldown** | Fatigue | ~1.0-1.3 | 0-1 new tokens in top 20, volume shrinking | Wait; CZ narratives retrace 50-70% |
| **⚫ Capitulation** | Fear | <0.8 | All tokens red, zero new entries | Watch for next ignition signal |

### Phase Indicators (GMGN Data)

```bash
# Phase = Cooldown signals:
# - Buy/Sell ratio ~1.25 (buying still slightly > selling, no urgency)
# - 0 new tokens under 2h old in top 20
# - Volume declining across the board
# - CZ narratives retracing (1h change mostly negative)
# This means: market is resting, next narrative needed

# Phase = Ignition signals:
# - Buy/Sell ratio >1.5
# - Fresh tokens <2h old appearing in top 20
# - Volume growing, not shrinking
```

**Key insight (user-taught):** BSC sentiment mirrors Solana's KOL cycle with a delay. When Solana starts heating up a new KOL narrative (Ansem, Sultan, etc.), BSC's CZ-counterpart phase follows within hours. Check Solana trending first, then map to BSC.

## Event-Driven Narratives (Non-KOL)

Not all hot narratives come from KOLs. Some are triggered by **corporate or regulatory events** that generate meme coin hype:

### Signal Types

| Trigger | Example | Chain Response |
|:--------|:--------|:---------------|
| Corporate branding | Robinhood files "Time To Do Crypto" trademark | Tokens named $HOOD appear on Solana/BSC |
| Exchange listing | Binance/Coinbase lists a token | Copycats and ecosystem tokens pump |
| Regulatory news | SEC approves/denies something | Narrative tokens around the event |
| Celebrity tweet | Elon/Trump/Musk mentions crypto | Immediate token creation wave |

### Detection Workflow

1. **Check X searches** for non-KOL triggers: corporate filings, trademark apps, exchange news
2. **Narrative is still fresh** — the event just happened, no real tokens yet
3. **Token creation wave follows within hours** — same pattern as KOL narrative but the trigger is an event, not a person
4. **First tokens to launch may be rugs** — wait for the 2nd-3rd wave where quality filters matter

### Example — Robinhood "Time To Do Crypto" Trademark (2026-07-09)

- **Trigger**: Robinhood filed USPTO trademark application for the slogan "Time To Do Crypto"
- **What it signals**: Robinhood is actively positioning for crypto/meme coin adoption; the filing covers advertising and financial services related to crypto
- **X reaction**: Russian and English crypto communities discussing the bullish signal; not yet a mass narrative
- **Chain reaction at time of discovery**: No $HOOD tokens trending on Solana/BSC trenches yet — narrative very fresh (< 1 hour old)
- **Expected**: Token creation wave within 24h; first tokens likely rugs, wait for 2nd-3rd wave with cleaner metrics
- **GMGN detection**: Search trenches for symbol "HOOD" or name containing "Robinhood"; tokens typically on pump.fun (Solana) or fourmeme (BSC)

## 4-Stage Conspiracy Pump Lifecycle

- Event: Robinhood filed a trademark for the slogan, indicating crypto/meme coin push
- X reaction: Russian/English communities discussing the bullish signal
- Chain reaction: *Still waiting for tokens to appear* — narrative very fresh
- Expected: $HOOD tokens on Solana pump.fun within 24h

## Position Management for Meme Coins

### The #1 Rule (from user's $400 CZ loss)

```
NEVER average down on a meme coin.
NEVER hold past -20%.
These are NOT trend trades — they are narrative pumps.
```

### Position Sizing

| Account Size | Per-Trade Max | Stop Loss |
|:-------------|:-------------:|:---------:|
| $100-500 | 2-5% ($2-25) | -20% |
| $500-2000 | 2-3% ($10-60) | -15% |
| $2000+ | 1-2% ($20-40) | -10% |

### Exit Strategy

| Scenario | Action |
|:---------|:-------|
| +30% on pump | Sell 50% |
| +100% on pump | Sell remaining 50% |
| -10% after entry | Tighten stop |
| -20% from entry | ❌ **SELL. No exceptions.** |
| Volume drops >80% from peak | Exit — nobody left to buy |

### When NOT to Add

- ❌ You're already down >10% (that means you were wrong)
- ❌ Volume is declining (narrative fading)
- ❌ Top10 concentration is >50% on a fresh token
- ❌ More than 6 hours since launch (the good entry passed)

### What the CZ Final Form Bull Loss Taught

User bought at ~$0.037 ($37M MC), added on the way down. The token went from conspiracy pump peak ($0.041) to consolidation ($0.0127). At 65% down with 98% volume collapse:

- **Adding more was throwing money into a dead narrative** — volume $173K vs peak $11M
- **Meme coins don't bounce like blue chips** — they either pump again or go to zero
- **The only hope was CZ himself tweeting** — relying on external factors = bad strategy
- **Correct play**: cut at -20%, re-enter if volume comes back with a new catalyst

## X/Twitter Crypto Trending Monitoring

See `references/x-twitter-crypto-monitoring.md` for the Playwright + cookie injection technique to monitor X.com crypto trending topics without an API key.

### YouTube Crypto Content Search

See `references/youtube-crypto-search.md` for searching YouTube for crypto-related tutorials, discussions, and videos via Playwright. 

**Known limitations (2026-07 update):**
- `youtubetranscript.com` — YouTube blocks this API
- `youtube-transcript-api` pip package — v1.2.4 has broken/incompatible API signatures
- Playwright click on YouTube's transcript button — the element is `hidden` in the DOM
- ✅ Search and extract metadata works reliably
- ❌ Full transcript extraction is NOT possible without dedicated YouTube API credentials

Use this when:
- User mentions a specific YouTube tutorial ("油管上有个视频说...")
- User asks about crypto content on YouTube
- Need to find video proof/educational content for a narrative

## YouTube Video Download

See `references/youtube-download-workflow.md` for downloading YouTube videos (including member-only content) using yt-dlp with Chrome cookies.

## Event-Driven Narratives

See `references/event-driven-narratives.md` for tracking non-KOL triggers: corporate filings (Robinhood trademark), exchange listings (GME futures), and regulatory news that generate token waves.

## X/Twitter Search via CLI

See `references/twitter-cli-workflow.md` for using the `twitter search` command (no OAuth needed) for automated periodic X monitoring in cron jobs. This replaced the Playwright+cookie injection approach.

## Market Maker (做市商) Shadow Wallet Tracking

See `references/market-maker-shadow-tracking.md` for the full methodology on tracking Wintermute, Amber Group, GSR, DWF Labs wallet activity on-chain.

**Key insight:** Market makers use shadow wallets (multi-address networks) to hide accumulation/distribution. GMGN can track known addresses, but shadow wallet discovery requires manual cross-referencing. Paid systems (影子交易系统, ~$800/yr) automate this; GMGN free version does not.

**GMGN limitation:** `gmgn-cli track follow-wallet` is **read-only** (shows trades from already-followed wallets). To add wallets to follow, use the GMGN **website** (gmgn.ai → search wallet address → click "追踪").

## GMGN CLI Data Pipeline

```bash
# 1. Check BSC trending (use --raw for scriptable output)
gmgn-cli market trending --chain bsc --interval 1h --limit 15 --raw

# 2. Get detailed token info
gmgn-cli token info --chain bsc --address <ADDRESS>

# 3. Deep dive: 15m kline for conspiracy pump detection
#    Choose time range covering last 24-48h to catch pre-pump baseline + pump window
#    15m resolution shows the exact candle where the pump started
gmgn-cli market kline --chain bsc --address <ADDRESS> --resolution 15m --from <TIMESTAMP> --to <TIMESTAMP>

# 4. Check signals (smart money buys, large buys, price spikes)
gmgn-cli token signal --chain bsc --address <ADDRESS>

# 5. Quick token quality scan for trenches (new launches)
gmgn-cli market trenches --chain sol --limit 30 --raw | python3 -c "
import json,sys
d=json.load(sys.stdin)
for t in d.get('data',{}).get('rank',d.get('data',[])):
    s=t.get('symbol','?')
    mc=float(t.get('market_cap',0)); vol=float(t.get('volume',0)); liq=float(t.get('liquidity',0))
    top10=float(t.get('top_10_holder_rate',0)); bundler=float(t.get('bundler_rate',0)); smart=int(t.get('smart_degen_count',0))
    buys=int(t.get('buys',0)); sells=int(t.get('sells',0)); holders=int(t.get('holder_count',0))
    # Filter pass-through logic
    if bundler < 0.2 and top10 < 0.5 and smart >= 1 and liq > 5000:
        print(f'{s} | MC:\${mc:,.0f} | Vol:\${vol:,.0f} | Liq:\${liq:,.0f} | B:{buys}/S:{sells} | H:{holders} | T10:{top10:.0%} | B:{bundler:.0%} | S:{smart}')
"
```

### 15m Kline Conspiracy Pump Analysis

When analyzing 15m candles for conspiracy pump detection, filter for pump candles (volume > $100K OR price change > 5%) and look for:

| Indicator | What It Reveals |
|:----------|:----------------|
| Pre-pump baseline volume | Normal candles < $10K → pump candle > $100K = 10-1000x anomaly |
| Vertical spike timing | Pump starts 04:00-07:00 Beijing (retail asleep) |
| Immediate dump pattern | Peak volume followed within 1-2 hours by larger sell-volume candles |
| Consecutive price range | 30%+ single-candle moves that reverse completely within hours |

**Example — CZ (Final Form Bull) 2026-07-04:**
```
Time(BJ)  Price             Change    Volume       Pattern
05:00     0.00012→0.0010    +743%     $148K        First pump candle (50x baseline)
05:15     0.0010→0.0030     +194%     $995K        Continued pump
05:30     0.0030→0.0061     +103%     $1.4M        Peak FOMO
05:45     0.0061→0.0199     +224%     $2.1M        Peak price
06:00     0.0199→0.041(h)   +31%      $3.4M        Absolute peak
06:15     0.041→0.018       -31%      $4.0M        Dump starts (largest volume candle)
06:30     0.018→0.008       -54%      $4.5M        Continued dump
```
**Conclusion:** Pre-pump volume $500-$8K/candle → pump $148K-$3.4M = 18-425x anomaly. Timing 5AM BJT. Peak sell volume ($4.5M) exceeds peak buy volume ($3.4M). Classic orchestrated pump.

## User Preferences

- **Direct, data-driven** — present key metrics (MC, Vol, Top10%, Bundle%, Smart Money count, Buy/Sell ratio) in a compact table
- **No fluff** — don't explain memecoin basics or KYC/AML warnings unless asked
- **Always check Solana first** before analyzing BSC — the cross-chain context is essential
- **Reference pairs** — compare current token metrics against the user's reference examples (CZ Final Form Bull at peak: $0.041, 74% Top10, 12% Bundle)

## Pitfalls

- ❌ **Don't ignore KOL narrative context** — When user asks "XX是什么角度", the "角度" is the KOL narrative being mirrored or the community angle, NOT a technical trading setup. See `references/angle-analysis-workflow.md` for the standard workflow.
- ❌ **Don't analyze BSC in isolation** — always check what Solana KOL narrative is driving it
- ❌ **Don't present raw DexScreener data** without filtering for top-volume pairs and quality metrics
- ❌ **Don't recommend entry/exit prices** — the user makes their own decisions
- ❌ **Don't explain basic crypto concepts** — the user is experienced
- ❌ **Never suggest 智谱AI (ZhipuAI/GLM)** — user explicitly rejected this and got angry when I tried connecting to it. Stick with DeepSeek.
- ❌ **Can't access protected/private X accounts** — `twitter search` (via twitter-cli) only works for public accounts. If the user wants to read a protected account's tweets, tell them they need to either (a) follow the account and get approved, then copy/paste tweets, or (b) use the Playwright browser with their own logged-in session. Don't suggest workarounds that don't exist.
- ❌ **When user asks "能不能做/能不能抓" for paid/会员 content** — Don't try to bypass paywalls. Instead: extract the free/public methodology from the sales page, and offer to replicate the core approach using the user's existing tools (GMGN + Freqtrade + Hermes). The user respects this and has explicitly chosen to build vs buy.
- ❌ **When user corrects a factual guess ("不是xxx"), do NOT keep cycling through more guesses** — Instead: acknowledge the correction, then ask/verify with the user what they actually mean. Repeated wrong guesses frustrate the user ("谁他妈要你连智普AIapi的").
- ❌ **Don't recommend paid membership content as "you should buy this"** — Instead: extract the free/public methodology and offer to replicate it with the user's existing tools if feasible.
- ✅ **Quick acknowledgment** — when researching (browser searches, chain lookups), acknowledge immediately with a brief status ("查一下","正在看","好的") rather than going silent
- ✅ **Do validate assumptions** — when the user corrects you, the lesson is a trading pattern, not a trivial preference
