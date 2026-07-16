# Token Scan Checklist

Source: User-provided detailed workflow adapted for Hermes automation.
Last updated: 2026-07-10

---

## Full Token Evaluation Checklist

Follow this order when evaluating a new token on any chain.

### Step 1: Age Check
- Age < 30 minutes: 🟢 Fresh, good opportunity
- Age < 6 hours: 🟡 Moderate, some upside left
- Age > 24 hours: 🔴 Too late, skip

### Step 2: Narrative Check
Search X for `$<SYMBOL> <CHAIN>` using twitter CLI:
- Strong social mentions? (GME, official-related, cat/dog memes best)
- Multiple influencers talking about it?
- Matches current chain narrative cycle?

### Step 3: Data Check (GMGN/DexScreener)
- Volume increasing + buying pressure
- Holder count growing rapidly
- Low market cap (ideal: $10K-$1M early, $1M-$10M mid)

### Step 4: On-Chain Verification
Use chain explorer (Blockscout for Robinhood, Solscan for Solana):
- Check holder distribution: Top 10 not too concentrated
- Check creator wallet: NOT selling, not deploying multiple tokens/day
- Verify contract: not a honeypot, no suspicious functions

### Step 5: GMGN Confirmation
- Smart money buying? (smart_degen_count >= 2 is good)
- Any rug warnings?
- Bundle rate low? (< 20% is good)

### Step 6: Position Entry
- Start with 1-2% of total funds
- Scale in if signals improve

### Step 7: Risk Monitoring
Stop trading immediately if:
- Creator/developer wallet continuously selling
- Holder distribution extremely concentrated or sniper bundling
- No social presence / fake volume
- Liquidity can be removed at any time
- Honeypot or high tax detected

### Step 8: Exit Strategy
- Take profit: 2x → sell 30%, 5x → sell 30%, 10x → sell remaining
- Stop loss: -50% hard stop (for meme coins; stricter -20% for user's V4 system)
- Don't get greedy: fast up = fast down
- Diversify: watch 3-5 coins simultaneously, never all-in-one

## Deployer Quality Assessment

When evaluating a deployer wallet, check (on GMGN):
1. How many contracts has this wallet deployed?
2. Were previous launches successful? (alive > 24h?)
3. Did tokens die within hours?
4. Did liquidity disappear?
5. Did the deployer sell immediately?
6. Does this wallet create new coins daily?

If the founder keeps pumping garbage, the next one is likely garbage too.

## Liquidity vs Market Cap

Don't be fooled by high MC with low liquidity.

**Example:**
- Token A: MC $1M, Liq $100K → 🟢 Better price discovery
- Token B: MC $100K, Liq $10K → 🟠 Thinner but still okay
- Token C: MC $500K, Liq $2K → 🔴 Cannot exit position

Rule of thumb: Liquidity should be >10% of market cap for safe exits.

## Mental Framework

Always remember:
- New chain early = 99% of memecoins go to zero
- Small test positions + batch operations
- Set stop-loss/take-profit discipline
- Act fast but verify everything
- Survive long enough to catch the 100x
