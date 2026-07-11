# Market Maker (做市商) Shadow Wallet Tracking

## Concept: The Shadow Trading System

Popularized by crypto YouTubers (e.g., 链求君's "影子交易系统" membership), this tracks **market maker wallet activity** to front-run their accumulation/distribution.

**Core insight:** Market makers (Wintermute, Amber Group, GSR, DWF Labs) must:
1. Buy tokens **before** they can pump them (accumulation phase)
2. Sell tokens **before** they can exit (distribution phase)
3. Use **shadow wallets** (multiple hidden addresses) to disguise their moves

This creates a **72-hour informational advantage** — if you see them accumulating before the public announcement/pump, you can enter before retail.

## Known Market Makers (Publicly Tagged)

| Market Maker | Primary Chain | Known For | Arkham Entity Label |
|:-------------|:--------------|:----------|:-------------------:|
| **Wintermute** | ETH/Solana | Largest, deepest liquidity | ✅ Labeled |
| **Amber Group** | ETH/Solana | OTC + market making | ✅ Labeled |
| **GSR** | ETH/Solana | High-frequency market making | ✅ Labeled |
| **DWF Labs** | ETH/Solana | Aggressive, newer | ✅ Labeled |
| **Flow Traders** | ETH | Traditional finance MM | ⚠️ Partial |
| **Jump Trading** | ETH/Solana | High-speed MM | ✅ Labeled |
| **Cumberland/DRW** | ETH | Institutional MM | ✅ Labeled |

## How to Find Wallet Addresses

### Method A: Arkham Intelligence (Most Accurate)

Arkham has entity-labeled wallets for all major market makers.

```
https://platform.arkhamintelligence.com/explorer/entity/wintermute
https://platform.arkhamintelligence.com/explorer/entity/amber-group
https://platform.arkhamintelligence.com/explorer/entity/gsr
https://platform.arkhamintelligence.com/explorer/entity/dwf-labs
```

However, Arkham has aggressive Cloudflare protection — browser automation may be blocked.

### Method B: GMGN Search (Works Best for User's Workflow)

The user's primary tool is GMGN. Search directly on gmgn.ai:

```
GMGN search bar → type "Wintermute"
→ GMGN tags known wallet addresses automatically
→ Click "追踪" (Track) to monitor wallet trades
```

Repeat for Amber Group, GSR, DWF Labs.

### Method C: DeBank/Etherscan (Fallback)

Some addresses are publicly documented (not 100% reliable — may be outdated):

```
Wintermute (known public):
- 0x0b34f4aebcf430a7f028a01cb1f4cfa435de0fea
- 0xDb8999354FcF61D4e27B4f5C0E4a55c7b7E2c2a
```

**Recommendation:** Use Method B (GMGN search) for the most up-to-date, reliably tagged addresses.

## Signals to Watch For

### Accumulation Signals (Bullish)

| Signal | Chain Data | Action |
|:-------|:-----------|:-------|
| **Single wallet accumulating** | MM wallet buys token without selling | Enter on pullback |
| **Shadow wallets buying** | Multiple linked addresses buy same token simultaneously | Strong buy signal |
| **Net accumulation** | Buy volume - sell volume > 0 over 7+ days | Accumulate position |
| **MM enters newly launched token** | MM appears in top holders within hours of launch | High conviction entry |

### Distribution Signals (Bearish)

| Signal | Chain Data | Action |
|:-------|:-----------|:-------|
| **Split selling** | MM breaks large sell into 50+ small transactions over days | Exit immediately |
| **Shadow wallet selling** | Multiple addresses sell same token | Exit — peak has passed |
| **Net distribution** | Sell volume > buy volume over 3+ days | Do not re-enter |
| **MM removes liquidity** | MM withdraws LP from token pool | Rug risk — exit NOW |

### Nuance — Shadow Wallet Detection

Market makers don't use one wallet. They use a **network of shadow wallets**:

```
MM Main Wallet → distributes funds to
   ├── Shadow Wallet A (accumulation)
   ├── Shadow Wallet B (accumulation)  
   ├── Shadow Wallet C (distribution — appears as "normal" activity)
   └── ... 10-30+ more
```

**How to detect shadow wallets:**
1. Look at the MM's main wallet → fund flow → find addresses receiving ETH/SOL from the main wallet
2. Check if those addresses make similar trades (same tokens, correlated timing)
3. Cross-reference with GMGN's wallet analysis

## GMGN CLI Commands for Tracking

```bash
# Check KOL trade records (includes some MM)
gmgn-cli track kol --chain sol --limit 20

# Check Smart Money trade records
gmgn-cli track smartmoney --chain sol --limit 20

# Check your followed wallets
gmgn-cli track follow-wallet --chain sol --limit 20
```

**Important:** GMGN's `track follow-wallet` command is **read-only** — it shows trades from wallets you've already followed. To add new wallets to follow, use the GMGN **website** (gmgn.ai → search wallet address → "追踪" button).

## What GMGN Cannot Do (vs Paid Systems)

| Capability | GMGN (Free) | Paid Shadow System ($800/yr) |
|:-----------|:-----------:|:----------------------------:|
| Track MM main wallets | ✅ Manual search | ✅ Auto |
| Shadow wallet discovery | ❌ Manual cross-referencing | ✅ AI-linked |
| Split sell detection | ❌ Raw tx data only | ✅ Detection algorithm |
| Combined net accumulation score | ❌ | ✅ Multi-wallet aggregate |
| Auto copy-trade | ✅ gmgn swap (manual trigger) | ✅ One-click |
| Push notifications | ✅ GMGN bot | ✅ Telegram |

## Workflow Integration

```
User sees a token is hot
        ↓
Check GMGN → does any MM wallet hold this token?
        ↓
YES → Check if MM is accumulating (buy > sell over 7d)
        ↓
YES → Strong signal, enter with position management rules
        ↓
NO → MM distribution detected → avoid / exit
        ↓
MONITOR → Daily: check GMGN follow-wallet for new MM activity
```

## Known Limitations

- ⚠️ **Wallet addresses change** — Market makers rotate wallets. Addresses found today may be cold in 3 months.
- ⚠️ **MM bots trade fast** — By the time GMGN indexes the tx, the opportunity may be gone for retail entries.
- ⚠️ **False signals** — MM may accumulate for weeks before any price movement.
- ⚠️ **Delisting risk** — Some tokens tracked by MMs are low-liquidity and may be rugpulled.
- ⚠️ **This does NOT replace narrative analysis** — MM accumulation on a dead narrative = dead money.
