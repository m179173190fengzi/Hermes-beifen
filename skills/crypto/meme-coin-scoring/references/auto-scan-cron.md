# Multi-Chain Auto‑Scan Cron Job

## Overview
Periodic scan of Solana + BSC + Robinhood Chain for new token opportunities. Uses `gmgn-cli` for on-chain data and `twitter` CLI for social sentiment. Scores each token via meme-coin-scoring, delivers only ≥75 alerts.

## Cron Schedule
```
schedule="0 6,11,15,19,22 * * *"
name="三链自动扫描+评分推送"
```

## Per‑Tick Flow
1. Solana trending top 20 → save JSON → score via `scripts/score_trending.py` → filter ≥75
2. BSC trending top 20 → save JSON → score → filter ≥75
3. Robinhood trending top 20 → save JSON → score → filter ≥75
4. Report each chain independently (do NOT combine into one list)
5. Optionally cross-check Twitter social velocity for ≥75 scorers

**Always use `--interval 1h`** with `gmgn-cli market trending` — it is a required flag.

```bash
gmgn-cli market trending --chain sol --interval 1h --limit 20 --raw > /tmp/sol.json
python3 /path/to/scripts/score_trending.py sol /tmp/sol.json
```

## GMGN Version
| Chain | Min Version |
|-------|------------|
| sol, bsc, base, eth | any |
| robinhood | **≥ v1.5.2** (`npm update -g gmgn-cli`) |

## Twitter CLI
```bash
pipx install twitter-cli          # command: twitter
twitter search "关键词 -is:retweet"  # works without OAuth
```

## Output Format

Per-chain sections, each with chain emoji header. Never combine chains.

```
🟣 SOLANA (20 tokens)
─────────────────────────
No tokens ≥75

🟡 BSC (20 tokens)
─────────────────────────
🔥 ≥75:
  $SYMBOL (0x...4444) — 78分
    Deployer:72 | Smart:80 | Health:75 | Activity:82
    MC:$200K | Bundle:5% | Smart:21 | ...

🟢 ROBINHOOD (20 tokens)
─────────────────────────
No tokens ≥75
```

## Pitfalls
- `--interval` is **required** for `market trending`; omission silently errors
- Robinhood: no token info → mark as "受限评分", use only trending fields
- Private X accounts unreachable — skip silently
- Tick latency ~30–60 s; if a chain errors, skip it (don't block)
- Lock_percent is null for pump.fun tokens (Solana); use `float(v or 0)`
