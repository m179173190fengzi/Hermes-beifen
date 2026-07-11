# GMGN MC > 200K Monitor (Solana + BSC)

Complete worked example for the recurring cron job that checks Solana and BSC for tokens with market cap > $200K and reports only new ones.

## State File

`~/.hermes/cron/mc200k_monitor.json`

Structure:
```json
{
  "last_updated": "ISO 8601 timestamp",
  "sol": [
    {"address": "token_addr", "symbol": "TICKER", "market_cap": 78935200, "volume": 60960100, "smart_degen_count": 58, "renowned_count": 28}
  ],
  "bsc": [
    {"address": "0x...", "symbol": "TICKER", ...}
  ]
}
```

## Cron Job Pattern

```python
import os, json, subprocess

store_dir = os.path.expanduser("~/.hermes/cron")
state_file = os.path.join(store_dir, "mc200k_monitor.json")
os.makedirs(store_dir, exist_ok=True)

# 1. Load previous state
prev = {}
if os.path.exists(state_file):
    with open(state_file) as f:
        prev = json.load(f)

# 2. Fetch current data from gmgn-cli
def fetch_chain(chain):
    cmd = f"gmgn-cli market trending --chain {chain} --interval 24h --min-marketcap 200000 --order-by marketcap --limit 20 --raw"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    # Extract minimal fields for diffing
    tokens = []
    for t in data.get("data", {}).get("rank", []):
        tokens.append({
            "address": t.get("address"),
            "symbol": t.get("symbol", t.get("name", "?")),
            "market_cap": t.get("market_cap", 0),
            "volume": t.get("volume", 0),
            "smart_degen_count": t.get("smart_degen_count", 0),
            "renowned_count": t.get("renowned_count", 0),
        })
    return tokens

current = {
    "last_updated": "2026-06-28T22:00:00Z",  # use datetime.now()
    "sol": fetch_chain("sol"),
    "bsc": fetch_chain("bsc"),
}

# 3. Delta compare by address
def new_tokens(current_list, prev_list):
    seen = {t["address"] for t in prev_list or []}
    return [t for t in current_list if t["address"] not in seen]

new_sol = new_tokens(current["sol"], prev.get("sol", []))
new_bsc = new_tokens(current["bsc"], prev.get("bsc", []))

# 4. Save state (atomic write)
tmp = state_file + ".tmp"
with open(tmp, "w") as f:
    json.dump(current, f, indent=2, ensure_ascii=False)
os.rename(tmp, state_file)

# 5. Report only deltas
if not new_sol and not new_bsc:
    print("[SILENT]")  # cron delivery protocol — suppress empty notification
else:
    # format and output the report
    ...
```

## Key Points

- **`--order-by marketcap`** — no underscore (`marketcap`, not `market_cap`). The API field name uses this format.
- **`--min-marketcap`** — also no underscore in the API (`min-marketcap`, not `min-market_cap`). However, the `gmgn-cli` CLI translates hyphenated flags to their API equivalents, so `--min-marketcap` works.
- **`--min-marketcap` is `200000`** (not `200k` or `200K`) — must be a full integer.
- **First run**: all tokens are "new" because no previous state exists.
- **Minimal store**: only `address` (for dedup) + display fields. Skip raw metadata.
- **Atomic write**: write to `.tmp` then `rename` to avoid corrupt state on crash.
