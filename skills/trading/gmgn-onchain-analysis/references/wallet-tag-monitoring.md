# Platform-Tagged Wallet Monitoring (fomo / gmgn / axiom …)

GMGN API realities for the request shape *"monitor what platform X's top wallets are buying"*.

## Platform tags are wallet tags, not a data source

Trading-app names appear inside `maker_info.tags` alongside quality tags. Observed on BSC
(`track smartmoney --chain bsc --limit 200`):

```
["smart_degen"]
["gmgn_go","smart_degen","gmgn"]
["fomo","smart_degen","gmgn_go","gmgn"]
["kol","smart_degen","gmgn_go","wash_trader","top_followed","gmgn"]
["gmgn_go","launchpad_smart","smart_degen","gmgn"]
```
So "wallets on fomo.family" = records whose `maker_info.tags` contains `fomo`. Matching is exact
lowercase; there is no CLI filter for platform tags — fetch the stream and filter locally.

## There is no leaderboard command — use the harvest → rank pipeline

`gmgn-cli track` exposes only `follow-tokens` / `follow-token-groups` / `follow-wallet` / `kol` /
`smartmoney`; `gmgn-cli portfolio` is single-wallet (`holdings` / `activity` / `stats` / `info` /
`token-balance` / `created-tokens`). Platform sites' own leaderboards require login, and their API
hosts (`api.` / `app.` / `web.` / `backend.<platform>`) do not resolve publicly.

Working substitute:

```bash
# 1. harvest a candidate pool from the live smart-money stream
gmgn-cli track smartmoney --chain bsc --limit 200 --raw     # keep records whose maker_info.tags has the platform
# 2. rank the pool by monthly profit, ONE WALLET PER CALL
gmgn-cli portfolio stats --chain bsc --period 30d --raw --wallet <addr>
# 3. their recent buys
gmgn-cli portfolio activity --chain bsc --wallet <addr> --type buy --limit 50 --raw
```
First-run pool is small (measured 7 wallets across sol+bsc); it accumulates on later runs.

## Verified field behaviour (three traps)

**1. `portfolio stats` ignores all but the first wallet.** The help text says "supports multiple
wallets" and `--wallet` is variadic (`--wallet A B C`), but the response contains a **single
object** — the first address only. Passing 2 addresses or 6 addresses both return just the first.
Loop one wallet per call (`sleep ~0.4`); weight 3, and 7 sequential calls did not hit 429.

**2. Activity records use `tx_hash`, not `transaction_hash`.** Top-level keys of a `portfolio
activity` record:
```
tx_hash, token{address,symbol,logo,total_supply}, token_amount, cost_usd, timestamp, wallet,
quote_token, quote_address, price, price_usd, is_open_or_close, launchpad,
launchpad_platform, dex_usd, gas_usd, from_address, to_address, event_type
```
Reading the documented `transaction_hash` yields `None` → any `if not tx: continue` guard drops
every row → the monitor silently reports "nothing new" while dozens of buys exist. Always
`tx = a.get("tx_hash") or a.get("transaction_hash")`, with a synthetic `wallet:ca:ts` fallback key.

**3. `stats` numbers worth reading:** `realized_profit` (USD string), `realized_profit_pnl` (ratio),
`pnl_stat.winrate` (0–1), `pnl_stat.token_num`, `buy`/`sell` counts, `common.tags` (confirms the
platform tag survived the round trip), `common.fund_from` (funding source label — "Binance: Hot
Wallet 11", "FixedFloat: Hot Wallet" indicate CEX-funded bot wallets).

A ranked wallet can be **net negative over 30d** while still sitting in the top 5 of a small pool
(measured: `-$3644` at rank 5, `-$4447`). Flag that in the report — its buys are weak evidence even
when several wallets converge.

## ⚠️ Ranking by absolute profit selects churn bots, not snipers

Sorting the pool by `realized_profit` (USD, absolute) is the obvious first implementation and it is
**misleading**. Measured on a BSC fomo pool, the rank #2 wallet was:

```
realized_profit  $2735   realized_profit_pnl  +1.09%   成本 $291,022
buy 1887 / sell 2198     pnl_stat.token_num  1941
```

+1% on $291K of turnover across ~1900 tokens is a **volume-churning bot**, not a skilled sniper — it
ranks high purely because it trades enormous size. Ranking by absolute profit therefore systematically
surfaces whoever turns over the most money, and in a small pool the tail can even be net-negative
(two BSC wallets ranked in the top 5 while down `-$3644` / `-$4447`).

Better ranking inputs (all in the same `stats` payload, no extra calls):

- `realized_profit_pnl` — return ratio; the actual skill signal
- `pnl_stat.winrate` — hit rate (0–1)
- `pnl_stat.token_num` — sample size; a big ratio on 5 tokens is luck, on 500+ is a process
- `buy` / `sell` counts — turnover, to spot the churn bots above

Practical composite: require `realized_profit > 0` **and** rank on `realized_profit_pnl` gated by a
minimum `token_num` (and/or winrate), rather than raw profit. Report the metric you ranked on next to
each wallet so the user can see why it sits where it does.

### Pool size honesty

"Top 5" out of a 5–7 wallet pool is not a ranking, it is the entire pool. Say so rather than
presenting it as a leaderboard, and grow the pool across runs before trusting the order. Candidate
expansion sources:

- `track smartmoney` is the confirmed source (`--limit 200`); it accumulates on later runs.
- **`token holders` on trending tokens** is a candidate second source — holder rows carry an
  app/platform tag too, so you can harvest wallets from the hottest tokens' holder lists.
  ⚠️ **The holder field is `tags`, NOT `wallet_tags`.** `token holders --raw` returns `tags` (e.g.
  `["sandwich_bot"]`, `["gmgn","fomo"]`, `["kol","gmgn","wash_trader"]`) plus a separate
  `maker_token_tags` (`["top_holder"]`, `["bundler"]`, …). Filtering on a non-existent `wallet_tags`
  key silently yields **zero** matches — an empty harvest that looks like "no such wallets exist".
  When a harvest returns 0 rows, print the raw `keys` of one record before concluding anything.
  (Trending output itself uses `.data.rank[]` — see `gmgn-cli-raw-data-shapes.md`.)

## BSC holder concentration: exclude the launchpad pool contract

`token holders --limit N --order-by amount_percentage` can show a Top1 address holding **77%**.
Check `addr_type` and `exchange` before calling it a whale:

- `addr_type: 2` + `exchange: "flap"` → the bonding-curve **pool contract**, `buy_tx=0 sell_tx=0`.
- GMGN's own `stat.top_10_holder_rate` already excludes it: same token reported `14.5%` there vs
  `75.6%` raw. Judge concentration from `top_10_holder_rate`; exclude `addr_type == 2` from any
  local computation.
- While a token is ungraduated (`launchpad_status: 0`, `launchpad_progress < 1`) the pool-held
  supply is locked in the curve by construction — that is not evidence of "LP locked" either way.

## Chain scoping

`portfolio stats` / `portfolio activity` are **per chain** — a wallet's BSC and Solana histories are
separate. When a user narrows scope to one chain, filter the harvested pool to that chain and fetch
only there; a stale multi-chain pool otherwise keeps producing wrong-chain rows and wasted calls.
