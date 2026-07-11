# Curator run — 2026-06-30T22:26:44.773973+00:00

Model: `deepseek-v4-flash` via `deepseek`  ·  Duration: 51s  ·  Agent-created skills: 16 → 16 (+0)

## Auto-transitions (pure, no LLM)

- checked: 16
- marked stale: 0
- archived (no LLM, pure time-based staleness): 0
- reactivated: 0

## LLM consolidation pass

- tool calls: **0** (by name: none)
- consolidated into umbrellas: **0**
- pruned (archived for staleness): **0**
- new skills this run: **0**
- state transitions (active ↔ stale ↔ archived): **0**

## LLM final summary

API call failed after 3 retries: Connection error.

## Recovery

- Restore an archived skill: `hermes curator restore <name>`
- All archives live under `~/.hermes/skills/.archive/` and are recoverable by `mv`
- See `run.json` in this directory for the full machine-readable record.
