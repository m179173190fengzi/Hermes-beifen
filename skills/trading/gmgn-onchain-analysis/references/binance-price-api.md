# Binance Price API Response Schemas (for Cron Reports)

When fetching BTC/ETH prices and 24h changes for the cron report, these two endpoints are used. Their response structures differ in field names — a common source of `KeyError` when parsing.

## Endpoint: `/api/v3/ticker/price`

```
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
```

**Response:**
```json
{"symbol": "BTCUSDT", "price": "63485.01"}
```

- Current price lives in the `price` field (string).
- Simple, one field to parse.
- **No 24h change data** — use the 24hr endpoint for that.

## Endpoint: `/api/v3/ticker/24hr`

```
GET https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT
```

**Response (key fields):**
```json
{
  "symbol": "BTCUSDT",
  "lastPrice": "63427.99",
  "priceChange": "-1858.01",
  "priceChangePercent": "-2.846",
  "openPrice": "65286.00",
  "highPrice": "65718.00",
  "lowPrice": "63059.39"
}
```

## ⚠️ Field Name Differences

| What you want | Field in `/ticker/price` | Field in `/ticker/24hr` |
|---------------|--------------------------|--------------------------|
| Current price | `price` | ⚠️ **`lastPrice`** — NOT `price` |
| 24h % change | ❌ N/A | `priceChangePercent` (string, e.g. `"-2.846"`) |
| 24h $ change | ❌ N/A | `priceChange` |
| 24h high | ❌ N/A | `highPrice` |
| 24h low | ❌ N/A | `lowPrice` |

**Common mistake:**
```python
# ❌ KeyError on /ticker/24hr — no 'price' key
d["price"]

# ✅ Works on both endpoints
d.get("lastPrice") or d.get("price")
```

## Quick Parsing Pattern (from saved file)

```python
# After: curl ... > /tmp/btc_24h.json
import json
with open("/tmp/btc_24h.json") as f:
    d = json.load(f)
last_price = float(d["lastPrice"])
change_pct = float(d["priceChangePercent"])
high = float(d["highPrice"])
low = float(d["lowPrice"])

# After: curl ... > /tmp/btc_price.json
with open("/tmp/btc_price.json") as f:
    d = json.load(f)
price = float(d["price"])  # 'price' here, not 'lastPrice'
```

## ETH Endpoint (same pattern)

```
GET https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT
```
Response: `{"symbol": "ETHUSDT", "price": "1875.08"}`

## Fallback: Blockchain.info (BTC only)

```
GET https://blockchain.info/ticker
```
Returns: `{"USD": {"15m": 63420, "last": 63428, "buy": 63427, "sell": 63429}, ...}`
Extract: `json.loads(output)["USD"]["last"]`
