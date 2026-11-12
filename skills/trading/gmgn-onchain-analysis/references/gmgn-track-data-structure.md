# GMGN Track Command — Response Field Reference

The `gmgn-cli track smartmoney` and `gmgn-cli track kol` commands return real-time transaction-level data for smart money / KOL wallets. This doc covers the response structure.

## `track smartmoney` / `track kol` Response

**Top-level:** `{"list": [...]}` — array of trade events, newest first.

### Transaction Fields (each item in `list`)

| Field | Type | Description |
|-------|------|-------------|
| `transaction_hash` | string | Solana/BSC transaction signature |
| `maker` | string | Wallet address that executed the trade |
| `side` | string | `"buy"` or `"sell"` |
| `amount_usd` | float | USD value of this trade |
| `price_usd` | float | Price per token in USD at trade time |
| `base_amount` | float | Total token units traded |
| `quote_amount` | float | Quote token amount (SOL/BNB/etc.) |
| `buy_cost_usd` | float | Total USD cost of buy (0 for sells) |
| `timestamp` | int | Unix seconds of the transaction |
| `is_open_or_close` | int | `0` = live/open market, `1` = close/migration |
| `base_address` | string | **Token contract address** |
| `balance` | float | Wallet's remaining token balance after this trade |

### `base_token` Sub-object

| Field | Type | Description |
|-------|------|-------------|
| `base_token.symbol` | string | Token ticker symbol |
| `base_token.logo` | string | Token logo URL |
| `base_token.total_supply` | string | Total supply (string) |
| `base_token.launchpad` | string | Launchpad platform (e.g. `"pump"`) |

### `maker_info` Sub-object

| Field | Type | Description |
|-------|------|-------------|
| `maker_info.avatar` | string | Wallet avatar URL |
| `maker_info.name` | string | Wallet display name |
| `maker_info.tags` | array of strings | Wallet tags (e.g. `["smart_degen", "axiom"]`, `["fresh_wallet", "smart_degen"]`) |
| `maker_info.twitter_username` | string | Twitter/X handle |
| `maker_info.twitter_name` | string | Twitter display name |

### Common Wallet Tag Combinations

| Tags | Meaning |
|------|---------|
| `["smart_degen", "gmgn"]` | GMGN-tagged smart money wallet |
| `["fresh_wallet", "smart_degen", "axiom"]` | Relatively new wallet, smart money tagged, traded via Axiom bot |
| `["smart_degen", "axiom"]` | Smart money wallet, Axiom bot user |
| `["kol"]` | KOL/influencer wallet |
| `["renowned"]` | GMGN-tagged renowned/KOL wallet |

## `track kol` Same Structure

`gmgn-cli track kol --chain sol --limit 20` returns the identical response shape — just scoped to KOL wallets. Use the same field mapping.

## Usage Example — Parse in Python

```python
import json, subprocess

r = subprocess.run(["gmgn-cli", "track", "smartmoney", "--chain", "sol",
                     "--side", "buy", "--limit", "20", "--raw"],
                    capture_output=True, text=True)
data = json.loads(r.stdout)

for item in data.get("list", []):
    symbol = item.get("base_token", {}).get("symbol", "?")
    addr = item.get("base_address", "")
    usd = item.get("amount_usd", 0)
    price = item.get("price_usd", 0)
    tags = item.get("maker_info", {}).get("tags", [])
    maker = item.get("maker", "")[:8]
    print(f"${symbol} | ${usd:.2f} | ${float(price):.8f} | tags:{tags} | {maker}")
    print(f"   CA: {addr}")
```

## Pitfall — Low Dollar Amounts Are Normal

Smart money test entries are often $30–$150. A $72 buy doesn't mean low conviction — it means the wallet is taking a small position to monitor the token. The signal is *that they entered at all*, not the dollar size. High-conviction plays show multiple entries from the same wallet across several minutes (accumulation).
