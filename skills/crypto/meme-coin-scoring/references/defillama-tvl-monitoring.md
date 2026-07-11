# DeFiLlama Chain TVL Monitoring

## API Endpoint

```bash
curl -s "https://api.llama.fi/chains"
```

Returns JSON array of chains with TVL data. Key fields:
- `name` — chain name (Solana, BNB Chain, Ethereum, Robinhood Chain, etc.)
- `tvl` — total value locked in USD

**Volume data is NOT available** from this endpoint.

## Target Chains (Confirmed Working 2026-07)

| Chain | TVL | API Name Match |
|:------|:---:|:---------------|
| Solana | $11.04B | `Solana` |
| BNB Chain | $6.79B | `Binance` (NOT "BSC" — match "binance" in lowercase name) |
| Robinhood Chain | $108.72M | `Robinhood Chain` (IS listed, previous docs outdated) |
| Ethereum | $84.61B | `Ethereum` |

**Robinhood Chain IS listed** in DeFiLlama as of 2026-07 (previous documentation saying it wasn't is outdated). It has a TVL of ~$108M.

## Python Script

See `scripts/tvl_monitor.py` for the reusable comparison script that fetches, filters, formats, and prints TVL comparison with bar visualization. Handles chain name matching (e.g. "Binance" not "BNB Chain").

## Cron Job Integration

Runs at 6/11/15/19/22 (user's preferred schedule). Output is piped into the daily briefing:
- Solana TVL growing = capital flowing into Solana
- Robinhood Chain TVL growing = new chain traction
- Declining TVL = capital exiting

## Known Issues

- No volume data from this endpoint (use DexScreener or GMGN)
- No 24h change rate (the `/chains` endpoint returns basic TVL snapshot only)
- Chain name matching: "Binance" not "BNB Chain" in the API response
