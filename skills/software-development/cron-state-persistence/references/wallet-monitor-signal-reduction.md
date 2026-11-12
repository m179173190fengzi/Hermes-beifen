# Script-Fed Wallet Monitor: Worked Example

Concrete companion to the "Script-Fed Monitor Crons" section of SKILL.md. Built for a request of the
shape: *"monitor the daily buys of platform X's top-5 monthly-profit wallets and alert me"*.

Working script: `~/.hermes/scripts/fomo_top5_monitor.py` (state: `~/.hermes/cron/state/fomo_monitor.json`).

---

## 1. Why the naive version fails

First cut pulled the last 24h of buys for the 5 ranked wallets and printed all of them:

- **86 rows in 24h.** Unreadable; the user stops reading after ~5 lines.
- One wallet produced **40+ distinct tokens at ~$145 each** — a spray-and-pray bot. Its individual buys carry no information.
- The genuinely interesting rows were the ones where **several ranked wallets bought the same token** (one token had 4 of 5 wallets in a 30-minute window).

Conclusion: the alert must be *derived*, not relayed. Reduce → then format.

## 2. Signal definitions used

| Signal | Rule | Rendered as |
|---|---|---|
| Consensus | same `chain:ca` bought by ≥2 of the tracked wallets within 48h | `🤝 X/5钱包 \| 合计 $Y \| 首次 N分钟前` |
| Big buy | newly-seen single-wallet buy ≥ `BIG_BUY_USD` (250) | `- $Y SYMBOL \| 钱包 0xabc… \| N分钟前` |
| Nothing | neither fired | `NO_NEW_BUYS` → agent replies `[SILENT]` |

Budgets: `TOP_N=5`, `LOOKBACK_H=24`, `CONSENSUS_WINDOW_H=48`, `CONSENSUS_MIN_WALLETS=2`,
`BIG_BUY_USD=250`, `MAX_CONSENSUS_ROWS=8`, `MAX_BIG_ROWS=6`, `POOL_CAP=120`, `SEEN_KEEP_DAYS=14`.

⚠️ The v1 numbers above were **too loose in both directions** — see §7 (tighten the window,
widen the pool) before reusing them.

## 3. Pipeline the script owns (agent adds nothing here)

1. **Harvest the wallet pool** — see §4. Merge into `pool` with first/last-seen; cap by `last_seen`.
2. **Rank by monthly profit** — per wallet `portfolio stats --period 30d`, store `profit30d` + `winrate` + `token_num`; skip wallets checked <20h ago; sleep ~0.4s between calls.
3. **Collect activity** — per ranked wallet `portfolio activity --type buy --limit 50`, keep rows newer than `LOOKBACK_H`, dedupe via `seen`.
4. **Update convergence state** — append `(wallet → ts)` into `token_buys[chain:ca]`, accumulate `meta[...].usd_running`.
5. **Emit** — consensus rows not in `alerted` (then mark them) + fresh big buys not in `alerted`; prune all maps; atomic save.

Everything network-facing carries the proxy prefix (`HTTPS_PROXY=http://127.0.0.1:7890`) — see the
skill's proxy notes; a bare call returns ECONNREFUSED.

## 4. Building a platform-scoped wallet pool (when no leaderboard exists)

`gmgn-cli` has **no wallet leaderboard subcommand**, and platform sites' leaderboards need login.
The workable substitute: harvest wallets out of live trade streams and filter by platform tag.

```bash
gmgn-cli track smartmoney --chain bsc --limit 200 --raw
# keep items where "fomo" (or the target platform) is in .maker_info.tags
```
Observed tag sets on BSC: `["fomo","smart_degen","gmgn_go","gmgn"]`, `["smart_degen","gmgn"]`,
`["kol","smart_degen","gmgn_go","wash_trader","top_followed","gmgn"]`. Platform names appear as
tags alongside quality tags — "wallets on platform X" means `maker_info.tags` contains `X`.

### Grow the pool by mining token holders (the trade stream alone is far too thin)

The trade-stream harvest yields only a handful of wallet addresses (measured: 7 after one run) —
statistically useless for a "top 5" ranking. Mine holders of the chain's trending tokens instead:

```bash
gmgn-cli market trending --chain bsc --interval 6h --limit 12 --raw          # → token addresses
gmgn-cli token holders --chain bsc --address <CA> --limit 100 --raw          # → per-holder tags
# keep holder.address where the platform name is in holder.tags
```
Measured effect: **12 trending tokens × 100 holders → +106 new pool wallets in one run**
(pool then capped at `POOL_CAP`). Run both harvesters — holders for volume, the trade stream for
freshly-active wallets.

⚠️ **Field trap:** the holders endpoint exposes **`tags`**, not `wallet_tags`. Reading
`.wallet_tags` returns `null` for every row and the harvest silently finds zero wallets. (Aliasing
it in a one-off `jq` — `{wallet_tags: .tags}` — is what makes this mistake easy to repeat later.)

## 5. Field traps that cost real debugging time

| Symptom | Cause | Fix |
|---|---|---|
| Script reports "no new buys" although buys demonstrably exist | Activity records expose **`tx_hash`**, not `transaction_hash`. Reading the documented name yields `None`, so a `if not tx: continue` guard silently drops every row | `tx = a.get("tx_hash") or a.get("transaction_hash")`, plus a synthetic `wallet:ca:ts` fallback key so dedupe still works |
| Batch ranking returns one wallet | `portfolio stats` accepts multiple `--wallet` values (variadic) but returns **only the first** wallet's stats | Loop one wallet per call (weight 3 each; 7 sequential calls caused no 429) |
| Holder-tag harvest finds nothing | holders endpoint uses `tags`, not `wallet_tags` (§4) | filter on `.tags` |
| A "whale" holding 70%+ of supply looks like extreme concentration | Top1 is the launchpad **bonding-curve pool contract** (`addr_type: 2`, `exchange: "flap"`), not a wallet | Judge concentration from GMGN's own `stat.top_10_holder_rate` (it already excludes the pool) and exclude `addr_type == 2` when computing anything locally |

## 6. Prompt (the agent half)

The cron prompt states: the scope (chain), the stdout contract (`NO_NEW_BUYS` → `[SILENT]`), what to
fetch per consensus token (`token info --raw` → narrative, MC/LP/holders/6h, socials, dev status),
the item template (every token must carry its **full CA** plus a `📋 叙事` line — never data only),
and the caveat to surface a ranked wallet that is **net negative over 30d** (its buys are weak
evidence even when they converge).

---

## 7. v2: ranking by absolute profit is not a wallet-quality filter

### The trap, measured

Ranking purely by 30d **absolute realized profit** puts wash/spray traders on the podium:

| Wallet | 30d profit | 30d cost | PnL | tokens traded (30d) | verdict |
|---|---|---|---|---|---|
| A | +$5,370 | large | low single digit % | 1,193 | high-frequency sprayer |
| B | +$2,735 | $291K | **+1%** | **1,941** | churn, not skill |
| C | **−$3,644** | — | negative | 458 | ranked #5 anyway |

A platform tag is not a quality tag either: a *usage* tag (which app the wallet traded through)
appears on an enormous population — 42 of one token's top-100 holders carried it. The tag builds the
**candidate pool**; the filters do the work.

### Tiered qualification (calibrated, don't hard-AND the windows)

Fetch **both** `--period 7d` and `--period 30d`, then:

- **Hard gates (both tiers):** `winrate_7d ≥ 0.45`, `trades_7d ≥ 50`, `avg_holding_period ≥ 60s`,
  `profit_30d > 0`.
- **A-level** (entry-grade): `winrate_7d ≥ 0.50` **and** `trades_7d ≥ 100` **and** `profit_7d > 0`.
- **B-level** (watch-grade): passes the hard gates but had a red week.

⚠️ **Calibration lesson:** a first pass required `profit_7d > 0 AND profit_30d > 0` as a hard AND and
rejected **every wallet in an 80-wallet pool** — including one at **30d +$88,606 / PnL +29%** whose
7d happened to be −$1,717. A single red week is normal variance, not disqualification. Use the 7d
window as a **tier/score penalty** (A vs B), never as a hard AND with the 30d window. Expect a
small qualified set — this is honest signal, not a bug.

Score (transparent, so the user can sanity-check it):
`win7*100 + clamp(pnl30_pct, -50, 200)*0.3 + min(trades_7d, 1000)*0.05 + (10 if tier == A)`.

### Consensus must be tier-aware and window-tight

- **STRONG / entry-grade:** ≥2 A-level wallets, **or** ≥3 wallets with ≥1 A-level, all buying the
  same token inside a **60-minute** window.
- **OBSERVE / no-entry:** ≥2 wallets inside 24h. Reported, never acted on.
- **Independence check:** a cluster whose buyers share one funding source (`common.fund_from`) is
  probably one operator → flag `⚠️资金源关联(可能协同)` and downgrade. Distinct sources = independent.
- 48h windows are too long for meme flow: they fuse "A bought today, B bought tomorrow" into fake
  consensus.

### Follow the exit side too

Track `--type sell` for the same wallets and warn when a qualified wallet **sells a token you
previously alerted on** (state key `alerted` + `exit_seen` with a 12h re-alert TTL). "跟买不跟卖"
is a classic way to ride a position to zero.

### Token-level hard filters (BSC) — run at alert time

`honeypot.is` **404s on fresh pairs** ("pair not found"), which is exactly when you need it. Use
GoPlus instead — it works on brand-new BSC tokens and returns the fields that matter:

```bash
curl -s "https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses=<CA>"
```
Reject on: `is_honeypot`, `cannot_sell_all`, `cannot_buy`, `hidden_owner`,
`can_take_back_ownership`, `owner_change_balance`, `transfer_pausable`, `is_blacklisted`.
Warn on: `buy_tax`/`sell_tax` > 0.05 (>0.10 = reject), `creator_percent` > 0.05,
`owner_address` ≠ `0x000…0` (not renounced), `is_mintable`, `is_proxy`.
Pair with `token info`: liquidity < $10K = structurally fragile, < $50K = don't chase (a 10–30s
follow delay pushes entry 3–5×); 24h volume ÷ liquidity > 5 = suspected manipulation;
token age < 24h = extreme risk; `dev.creator_open_count ≥ 3` (serial launcher) = downgrade;
no website = downgrade hard.

## 8. Per-run budget: cap the work, checkpoint the state

Adding pool mining and 7d+30d stats made a full refresh **9+ minutes with no output** — and because
state was only written at the end, an interrupted run lost everything.

- Cap refreshes per run (`MAX_STATS_PER_RUN = 40`): sort candidates by `(last_checked, -last_seen)`
  so never-checked and stalest wallets go first; the rest converge over the next runs.
- Cache per wallet (`checked` + `STATS_REFRESH_H = 20h`) so the expensive calls happen ~daily.
- **Schema-migration guard:** when qualification starts depending on a new field, treat records
  missing it as stale (`if prev and "tier" in prev and now - prev["checked"] < TTL: continue`).
  Otherwise a field added this session is silently ignored for a whole refresh window.

## 9. Cost discipline (user-facing constraint)

A monitor like this is cancelled fast if each tick burns tokens. The user's words on v2:
**"取消算了，太费token了"** — after the design grew a mandatory per-token enrichment stage.

- The **script does 100% of the deterministic work** (fetch, gate, score, cluster, dedupe) — it
  costs nothing. The agent stage must be **formatting only**, over an already-reduced list.
- Do not add "for each of the top N tokens, fetch token info / run a rubric" fan-out. If a per-token
  check is genuinely needed, keep N ≤ 3 and say so, or move the check into the script.
- Cap every list in the report (`MAX_*_ROWS`). An 86-row alert is both unreadable and expensive.
- When iterating on the design, prefer one end-to-end verification run over repeatedly re-running a
  multi-minute pipeline; resetting state to re-test costs a full pipeline pass each time.
