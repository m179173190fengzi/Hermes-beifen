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

### no_agent Health Check Watchdog

For **pure script-based health checks** that run without any LLM (no tokens consumed), see:

➡ `references/no-agent-health-check-watchdog.md`

Covers the pattern and script contract for monitoring API keys, tokens, and external service endpoints (TG token expiry, GMGN API health, etc.) via `no_agent=true` cron jobs. The script stays silent on success and alerts on failure.

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

## Script-Fed Monitor Crons (script stdout → agent prompt)

For monitors that must *reduce noise before the LLM sees it* (wallet/whale buy alerts, leaderboard tracking), use the script-fed shape rather than a pure agent prompt:

```python
cronjob(action='create', name='...', schedule='0 21 * * *',
        script='my_monitor.py',            # runs each tick
        enabled_toolsets=['terminal'],     # agent only needs tools to enrich + format
        prompt='<...stdout contract...>')
```
- The script's stdout is injected into the agent's prompt as context every tick. The script owns fetching, state, dedupe and reduction; the agent only enriches (token info / narrative) and formats the last mile.
- Script lives in `~/.hermes/scripts/`, state in `~/.hermes/cron/state/` — that subdir does **not** exist by default, create it.
- **Declare an explicit stdout contract and repeat it in the prompt**: `NO_NEW_BUYS` → reply exactly `[SILENT]`; `DATA_UNAVAILABLE: ...` → `[SILENT]`; otherwise a report block. Never leave "nothing found" as an empty string the agent has to interpret.

### Reduce raw streams before alerting — consensus, not volume

Raw activity from top wallets is unusable as an alert stream. Measured on a real top-5 monitor: **5 tracked wallets → 86 buys in 24h**, one wallet alone sprayed 40+ different tokens at ~$145 each. Keep only the rows that carry information:

- **Consensus** — same token bought by ≥2 of the tracked wallets inside a rolling window (48h). By far the strongest signal; report wallet count, summed USD, first-buy age, and which wallets.
- **Fresh big buy** — a *newly seen* single-wallet buy above a size floor (e.g. ≥$250). Everything below the floor is spray noise.
- Cap both lists (≈8 consensus / ≈6 big) and sort by (wallet count, USD).

### State schema that survives cross-run consensus

```json
{ "pool":       {"<addr>":   {"chain": "bsc", "first_seen": 0, "last_seen": 0}},
  "ranking":    {"<addr>":   {"chain": "bsc", "profit30d": 0, "winrate": 0, "checked": 0}},
  "seen":       {"<tx_key>": 0},
  "token_buys": {"<chain>:<ca>": {"<wallet>": 0}},
  "alerted":    {"<chain>:<ca>": 0},
  "meta":       {"<chain>:<ca>": {"symbol": "...", "usd_running": 0}} }
```
- ⚠️ **Do NOT use a flat `seen` set as the only dedupe.** Marking every raw buy as seen destroys future convergence detection: a token bought by wallet A today and wallet B tomorrow could never cluster. `token_buys` (rolling per-token buyer map) is the consensus source; `seen` only answers "already processed".
- Prune per map by its own window: `token_buys` 48h, `alerted` 24h (anti-repeat), `seen` 14d, `pool` capped by `last_seen` (keep most recent N).
- Atomic write (`tmp` + `os.replace`) as usual.
- Ranking refresh can be throttled (`checked` timestamp, skip if <20h) so the expensive per-wallet stats calls happen once a day, not every tick.

### Scope filters belong in the script, not only in the prompt

When the user narrows scope ("only BSC buys", "drop chain X"), enforce it in the script — a chain allowlist checked in harvest, ranking **and** the activity-fetch loop — *and* restate it in the prompt. Prompt-only filtering leaves stale other-chain entries inside the cached pool and keeps burning API calls on them.

### Keeping alternative versions of a cron prompt

- Store canonical prompt backups under `~/.hermes/cron/prompts/<name>.md` — **not `/tmp`**: an in-turn `/tmp` backup was already gone before the same session ended. `~/.hermes/cron/` is durable and synced by the GitHub backup cron.
- To preserve an alternate variant "for later use", create the job and immediately `cronjob(action='pause')` it: it can't fire by accident, and reviving it is one command. Cheaper than deleting and reconstructing from session history.
- Extract any job's full prompt for editing with **jq**, not python (inline `python3 -c` is frequently blocked by command approval):
  ```bash
  jq -r '.jobs[] | select(.id=="<job_id>") | .prompt' ~/.hermes/cron/jobs.json > /tmp/prompt.txt
  ```
  `cronjob action=list` only returns a truncated `prompt_preview`, so this is the only reliable way to see the text you are about to `update`.
- Full worked example of a script-fed wallet monitor — pool mining via token holders, **tiered wallet qualification** (why 30d absolute profit ranks wash traders #1), tier-aware consensus windows + independence checks, BSC token hard filters (GoPlus, because honeypot.is 404s on fresh pairs), **per-run API budgets**, and GMGN field traps: [`references/wallet-monitor-signal-reduction.md`](references/wallet-monitor-signal-reduction.md)

### Cost discipline — the user cancels monitors that burn tokens

A script-fed monitor is only worth keeping if each tick is cheap. A design that grew a mandatory
per-token enrichment stage was cancelled outright: **"取消算了，太费token了"**.

- The script owns **100% of the deterministic work** (fetch, gate, score, cluster, dedupe) — zero tokens. The agent stage must be **formatting only**, over an already-reduced list.
- **No per-item enrichment fan-out** ("for each of the top N, fetch token info and run a rubric"). If a per-token check is unavoidable, cap N (≤3) or move the check into the script.
- Cap every list (`MAX_*_ROWS`). An 86-row alert is unreadable *and* expensive.
- Budget the script itself: cap expensive calls per run (`MAX_STATS_PER_RUN`), cache per entity with a TTL, and prioritise never-checked items so the pool converges over a few runs instead of stalling one run for 9+ minutes.
- When iterating, do **one** end-to-end verification run — resetting state to re-test buys another full multi-minute pipeline pass each time.

## Cron Job Prompt Editing: Section-Level Modifications

When a user says "取消" or "remove" with numbered/bulleted items, they often mean **removing those sections from a cron job's prompt content** — NOT deleting the entire cron job. Misinterpreting this is destructive (the job is gone and must be recreated).

### Protocol

1. **Check context**: If the user lists items like "2️⃣ 链上热点 3️⃣ 聪明钱动向" with "取消", first verify whether these are:
   - Sections within a single cron job's prompt (→ update the prompt, keep the job)
   - Separate cron jobs (→ delete/disable specific jobs)
2. **When in doubt, describe the action before executing**: "是去掉链上合成报告里的这几项内容？" — one sentence confirmation avoids deletion mistakes.
3. **If you already deleted the wrong job**: recover by loading the deleted job's full prompt from `session_search()` (the cron session stores it as the user message), then recreate it identically via `cronjob(action='create')`.

### Handling Clarity

When multiple cron jobs cover overlapping topics (e.g. "每日Alpha合成简报" and "链上合成报告"), a user referring to one by its content sections ("链上热点/热搜对比") could mean either job. Quick check:

- List the cron jobs explicitly
- Map the named sections to the prompt that contains them
- Confirm before deleting

### "恢复成这样" = Restore the Format That Produced a Pasted Output

When the user pastes an **old report output** and says "恢复成这样" / "恢复成这个格式", they mean: update the current cron job's prompt so it produces that exact format again. This usually means a previous prompt edit trimmed sections out, and now the user wants them back.

Recovery path (works even if the old job was deleted):

1. The pasted output often carries the old job's identity (e.g. "每日Alpha合成简报 (job_id: 227c12f6518b)").
2. Find the full old prompt via `session_search(query='<job name or key phrase from output>', role_filter='user')` — cron sessions store the complete prompt as the user message (the `[IMPORTANT: You are running as a scheduled cron job...]` block contains the exact prompt text).
3. `cronjob(action='update', job_id=<current job>, prompt=<restored full prompt>)`, then `cronjob(action='run')` to verify the restored format.
4. If the old prompt references helper scripts, check they still exist — `/tmp` is wiped on reboot.

### ⚠️ A section the prompt "deleted" can come back — injected by a *skill doc*

**Measured failure:** the user asked to remove the 「观察名单」 section from a report cron. The prompt was
edited to "只列 ≥70 分准推级". The very next report **still contained 观察名单**.

Root cause: that section was never in the prompt — it came from a **skill the cron loads**
(`gmgn-onchain-analysis` documents "观察名单可下探 55-59" / "准推不足 3 条时用观察名单补齐"),
and the agent obeyed the skill over the prompt.

**Fix — add an explicit override clause that names the skill's behaviour:**

```
6. 🚫 禁止输出观察名单：只列 ≥70 分的准推级标的，60-69/55-59 一律不列不提。
   ⚠️ 这条【优先于任何 skill 文档里的规则】——skill 里可能写"观察名单可下探 55-59"
   "按分数列出 60-69 观察级""准推不足时用观察名单补齐"，本 prompt 一律不执行。
```

- **Diagnosis order when an unwanted section reappears:** `grep <section keyword> ~/.hermes/cron/jobs.json`
  → 0 hits means it is *not* the prompt; then read the cron's `skills` list and grep those skill docs
  (hits = skill injection). `cronjob action=list` shows the loaded skills per job.
- Generalising: **prompt ↔ injected skill-doc conflicts are only won by an explicit "overrides skill docs" clause
  in the prompt.** Deleting the line is not enough.

### Adding a data section: let the script emit a verbatim block

For **LLM-driven** report crons (the agent writes the report), do *not* ask the agent to go fetch and summarise
the data — give it a script that prints a finished block and tell it to paste the block unchanged:

```
{把 `python3 ~/.hermes/scripts/<block>.py` 的输出【原样整段粘贴】，它自带标题；
 末尾加一行 📊 解读（一句话，没有呼应就写"无呼应"）}
```

Rules to state in the prompt: **(a) 原样粘贴，不重排不重算；(b) 脚本输出"暂不可用"时保留该行，禁止编造；
(c) 解读最多一句话且允许"无呼应"** — no room for invented narrative. List the script in Workflow step 1
so the agent doesn't skip it. Full worked example (fomo 热门榜 / 推特热议 blocks):
`multi-platform-search-cli` → `references/report-embedding-blocks.md`.

## Pitfalls

- **⚠️ DANGER: "取消" + numbered items usually means prompt edits, NOT job deletion.** When a user says "2️⃣ X 3️⃣ Y 取消" or lists items with "取消", they almost always mean *remove those sections from that cron job's prompt content*. Deleting the entire job is destructive and forces you to reconstruct it from session_search. Always verify intent before cronjob(action='delete'): "是要去掉这个任务里的这几项内容，不是删掉整个任务？"
- **⚠️ Cron helper scripts must live in a persistent path, NOT `/tmp`.** `/tmp` is wiped on reboot; a cron job referencing `/tmp/foo.py` will silently lose that data source after the next reboot. Put scripts under `~/.hermes/scripts/` (e.g. `~/.hermes/scripts/tvl_monitor.py`) and reference the absolute path in the prompt. When restoring an old cron prompt, verify its script paths still resolve.
- **Recovery after wrong deletion**: use session_search(query='cron_<job_id>') — cron sessions store the full prompt as the user message (the [IMPORTANT: You are running as a scheduled cron job...] message contains the exact prompt text). Recreate via cronjob(action='create') with prompt copied from there.
- **When cron jobs overlap in topic** (e.g. "每日Alpha合成简报" and "链上合成报告" both cover on-chain analysis), a user referring to a section by content keywords ("链上热点") could mean either job. Quick-check: list active jobs and map section names to prompts before acting.
- **Do NOT use `memory()` in cron context** — it will silently fail (Memory is not available messages)
- **Do NOT use `session_search()` in cron context** — cron jobs run outside any session scope
- **First run is noisy** — inform the user once (off-cron) that the first report will be a full snapshot, then subsequent runs are incremental
- **File permissions**: `os.makedirs(store_dir, exist_ok=True)` creates with default umask; if the cron user differs from the Hermes user, set explicit `mode=0o700`
- **Schedule format determines repeat behavior**: Use cron syntax (`*/15 * * * *`) for `repeat: forever`. Human-readable schedules like `15m`, `30m`, or `every 2h` default to `repeat: once` (single execution), even though they describe periodic intervals. Always use cron-format strings (e.g. `*/15 * * * *` for every 15 minutes, `0 23 * * *` for daily at 23:00) when creating a recurring forever job. Test with `cronjob action=list` — if `repeat` shows `once` instead of `forever`, the schedule format is likely the problem.
