# GMGN CLI `--raw` Data Shapes

Each GMGN CLI subcommand returns a different JSON shape when `--raw` is used.
Always check the shape before accessing fields.

## `market trending --raw`

```python
result = json.loads(raw_json)
# result is a DICT
rank = result.get("data", {}).get("rank", [])
# If result is not a dict or has no "data", fallback:
if isinstance(result, dict):
    rank = result.get("data", result).get("rank", [])
else:
    rank = []
```

## `market signal --raw`

```python
result = json.loads(raw_json)
# result is a FLAT LIST (not a dict)
if isinstance(result, list):
    signals = result
else:
    signals = result.get("data", [])
# Each item has: token_address, signal_type, trigger_mc, signal_times
# Symbol is in: item.get("data", {}).get("symbol", "?")
```

## `market hot-searches --raw`

```python
result = json.loads(raw_json)
# result can be either:
#   FLAT LIST — each block is {interval, chain, tokens: [...]}
#   DICT with "data" key — data is the array of blocks
if isinstance(result, list):
    blocks = result
elif isinstance(result, dict):
    blocks = result.get("data", [])
else:
    blocks = []

# Extract tokens from blocks
tokens = []
for block in blocks:
    if isinstance(block, dict):
        tokens.extend(block.get("tokens", []))

# Tokens are RankItem shape (same as market trending)
```

## `market trenches --raw`

```python
result = json.loads(raw_json)
# ROOT-LEVEL keys: "new_creation", "pump" (near_completion), "completed"
# NOT wrapped in "data"
new_creation = result.get("new_creation", [])
pump = result.get("pump", [])         # corresponds to --type near_completion
completed = result.get("completed", [])
```

## `token info --raw`

```python
result = json.loads(raw_json)
# result is a DICT (not wrapped in data)
# Fields: address, symbol, name, price (object), liquidity, holder_count, etc.
# Access current price via: result["price"]["price"] (nested object)
# Market cap = float(result["price"]["price"]) * float(result["circulating_supply"])
```

## `token security --raw`

```python
result = json.loads(raw_json)
# result is a DICT (not wrapped in data)
# Fields: is_honeypot, open_source, owner_renounced, rug_ratio, etc.
```

## `token holders --raw` / `token traders --raw`

```python
result = json.loads(raw_json)
# result is a DICT with "list" key
holders = result.get("list", [])
```

## `track smartmoney --raw` / `track kol --raw`

```python
result = json.loads(raw_json)
# result is a DICT with "list" key (NOT "data" — verified 2026-07-28)
items = result.get("list", [])
# ⚠️ Do NOT use result.get("data", {}) — that returns empty

# Each item fields:
#   base_token.symbol    — token symbol (NOT top-level "symbol")
#   base_address         — contract address (NOT "address")
#   maker_info.tags      — wallet tags (e.g. ["smart_degen", "axiom"])
#   amount_usd           — trade amount in USD
#   side                 — "buy" / "sell"
#   maker                — wallet address
```
