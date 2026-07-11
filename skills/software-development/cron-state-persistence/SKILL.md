---
name: cron-state-persistence
description: State persistence pattern for Hermes cron jobs that need delta/diff reporting — file-based storage at ~/.hermes/cron/ when memory tools are unavailable in cron environments. Use when setting up a cron job that says "compare with previous results" or "only report new items since last run".
---

## Problem

Cron jobs that perform delta monitoring (e.g. "only report new tokens since the last check") need cross-run state. **Memory tools (`memory`, `session_search`) are not available in cron environments** — they require a live Hermes session.

Without state persistence, cron jobs either:
- Report everything every time (noise)
- Have no way to know what was previously reported

## Solution: File-Based State at `~/.hermes/cron/`

Store state in `~/.hermes/cron/<job_name>.json`. Read at start, write at end.

## Pattern

```python
import os, json

store_dir = os.path.expanduser("~/.hermes/cron")
os.makedirs(store_dir, exist_ok=True)
state_file = os.path.join(store_dir, "my_monitor.json")

# 1. Load previous state
previous = None
if os.path.exists(state_file):
    with open(state_file) as f:
        previous = json.load(f)

# 2. Fetch current data (from CLI or API)
current_data = [...]  # your data fetching logic

# 3. Delta compare
prev_addresses = {t["address"] for t in (previous or [])}
new_items = [t for t in current_data if t["address"] not in prev_addresses]

# 4. Save current state for next run
with open(state_file, "w") as f:
    json.dump(current_data, f)

# 5. Report only deltas — or stay silent
if new_items:
    # format and output the report
    pass
else:
    print("[SILENT]")  # cron delivery protocol — suppresses empty notifications
```

## Key Considerations

### First Run
No previous state exists → all items are "new". The first report is always a full snapshot. This is expected and fine — the user sees the baseline and subsequent runs only show additions.

### What to Store
Keep only the fields needed for comparison:
- Primary key: `address` (token contract address, PR number, etc.)
- Supporting context: `symbol`, `market_cap`, `volume` — whatever makes the report useful
- Skip: large raw data (timestamps, response metadata, logo URLs)

### Avoiding File Bloat
- If the job compares address-based uniqueness, `address` dedup is automatic
- For long-running jobs (months), consider sliding-window retention: keep only the last N snapshots, or purge addresses older than a reasonable window
- Typical size: 20–100 tokens × ~200 bytes each = 4–20KB per run — negligible

### Concurrency
If same-named cron jobs could overlap (rare for `*/15 * * * *` but possible if long network calls), use atomic writes:
```python
tmp = state_file + ".tmp"
with open(tmp, "w") as f:
    json.dump(current_data, f)
os.rename(tmp, state_file)
```

### Storing Additional Metadata
Include a `last_updated` timestamp to track staleness:
```python
{"last_updated": "2026-06-28T15:30:00", "sol": [...], "bsc": [...]}
```

## Usage Examples

### Token MC Monitor (Solana + BSC)
Stored as `~/.hermes/cron/mc200k_monitor.json`:
- Two keys: `sol` and `bsc`
- Each: array of token objects with `address`, `symbol`, `market_cap`, `volume_1h`, `smart_degen`, `renowned`
- On each run: compare addresses per chain independently
- New tokens on either chain trigger a notification

### Generic File Monitor
```python
# Checking for new/updated files
state_file = "~/.hermes/cron/file_watcher.json"
previous = json.load(open(state_file)) if os.path.exists(state_file) else {"seen": []}
current = [f for f in os.listdir("/some/path")]
new = [f for f in current if f not in previous["seen"]]
json.dump({"seen": current, "last_updated": "..."}, open(state_file, "w"))
```

## Reference: GMGN MC Monitor

See [`references/gmgn-mc200k-monitor.md`](references/gmgn-mc200k-monitor.md) for a complete worked example monitoring Solana + BSC tokens with market cap > $200K. Covers the full delta-reporting lifecycle: fetch from `gmgn-cli`, diff by address, atomic state write, and [SILENT] delivery protocol.

## Pitfalls

- **Do NOT use `memory()` in cron context** — it will silently fail (Memory is not available messages)
- **Do NOT use `session_search()` in cron context** — cron jobs run outside any session scope
- **First run is noisy** — inform the user once (off-cron) that the first report will be a full snapshot, then subsequent runs are incremental
- **File permissions**: `os.makedirs(store_dir, exist_ok=True)` creates with default umask; if the cron user differs from the Hermes user, set explicit `mode=0o700`
- **Schedule format determines repeat behavior**: Use cron syntax (`*/15 * * * *`) for `repeat: forever`. Human-readable schedules like `15m`, `30m`, or `every 2h` default to `repeat: once` (single execution), even though they describe periodic intervals. Always use cron-format strings (e.g. `*/15 * * * *` for every 15 minutes, `0 23 * * *` for daily at 23:00) when creating a recurring forever job. Test with `cronjob action=list` — if `repeat` shows `once` instead of `forever`, the schedule format is likely the problem.
