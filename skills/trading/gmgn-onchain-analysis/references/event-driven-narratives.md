# Event-Driven Narrative Detection

Not all meme coin narratives come from KOLs. Corporate/regulatory/exchange events can trigger token creation waves.

## Detection Flow

1. Monitor X for non-KOL triggers: corporate filings, trademark apps, exchange listings, regulatory news
2. Narrative is fresh — event just happened, no tokens yet (24h window)
3. Token creation wave follows within hours (same pattern as KOL narrative)
4. First wave tokens are almost always rugs — wait for 2nd-3rd wave with good metrics

## Example Signals

| Trigger | Token Response | Chain |
|:--------|:---------------|:------|
| Robinhood files "Time To Do Crypto" trademark | $HOOD tokens appear | Solana/BSC |
| Binance lists perpetual futures | Token name + "futures" or ticker copies | All chains |
| CZ tweets | CZ-related tokens pump | BSC (fourmeme) |
| Major exchange listing announcement | Copycats with similar tickers | All chains |

## Detection via Twitter CLI

```bash
twitter search "trademark filed crypto -is:retweet" 
twitter search "binance listing new -is:retweet"
twitter search "filing trademark application -is:retweet"
```

## Robinhood "Time To Do Crypto" Case Study (2026-07-09)

- **Event**: Robinhood filed USPTO trademark application for slogan "Time To Do Crypto"
- **Covers**: Advertising, financial services, crypto-related services
- **X reaction**: Russian/English crypto communities discussing bullish signal
- **Chain reaction at discovery**: No $HOOD tokens trending yet — narrative < 1 hour old
- **Expected**: Token creation wave within 24h on Solana pump.fun
- **Quality check**: Filter early rugs, wait for 2nd wave with Bundle<20%, Top10<50%, Smart Money>0

## Binance GME Futures Listing Signal

When Binance lists perpetual futures for a token (especially meme/stock tokens), it triggers:
1. The actual token price movement (stocks/crypto)
2. Copycat tokens on Solana/BSC with similar tickers
3. Narrative tokens referencing the listing event

## Quality Assessment for Event Tokens

The same scoring system applies (see meme-coin-scoring skill) but with adjusted expectations:
- First 2-4 hours: expect higher Bundle rates (snipers everywhere)
- First tokens = highest risk, high reward potential
- Look for tokens where smart money enters early despite high Bundle
