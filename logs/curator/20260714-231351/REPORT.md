# Curator run — 2026-07-14T23:13:51.979815+00:00

Model: `deepseek-v4-flash` via `deepseek`  ·  Duration: 2m 49s  ·  Agent-created skills: 16 → 14 (-2)

## Auto-transitions (pure, no LLM)

- checked: 16
- marked stale: 0
- archived (no LLM, pure time-based staleness): 0
- reactivated: 0

## LLM consolidation pass

- tool calls: **34** (by name: patch=3, read_file=5, search_files=1, skill_manage=2, skill_view=16, skills_list=1, terminal=6)
- consolidated into umbrellas: **2**
- pruned (archived for staleness): **0**
- new skills this run: **0**
- state transitions (active ↔ stale ↔ archived): **0**

### Consolidated into umbrella skills (2)

_These skills were **absorbed into another skill** during this run — their content still lives, just under a different name. The original directory was moved to `~/.hermes/skills/.archive/` for safety and can be restored via `hermes curator restore <name>` if the consolidation was wrong._

- `cross-chain-meme-kol-analysis` → merged into `gmgn-onchain-analysis` — Narrower sibling covering same Solana→BSC KOL narrative analysis domain; unique content (angle analysis, position rules, event narratives, market maker tracking) absorbed as labeled subsection + reference files
- `crypto-meme-analysis` → merged into `gmgn-onchain-analysis` — Narrower sibling covering same meme-coin analysis domain; unique content (0-100 scoring system, Robinhood narrative map, token checklist) absorbed as labeled subsection + reference files

## LLM final summary

Both skills are confirmed removed from the active index. The consolidation is complete. Here's the summary.

---

## Curator Summary

### Cluster Processed: Crypto Meme/Chain Analysis

The dominant cluster in the 16-agent-created-skills was the **crypto on-chain analysis** domain, where three skills existed at near-identical scope:

| Skill | Lines | Refs | Domain |
|-------|:-----:|:----:|--------|
| `gmgn-onchain-analysis` | 628→759 | 19→27 | GMGN data + cross-chain mirroring + conspiracy pumps + user preferences |
| `cross-chain-meme-kol-analysis` | ~400 | 9 | KOL patterns + angle analysis + event narratives + position rules |
| `crypto-meme-analysis` | ~250 | 3 | Scoring system + Robinhood narrative + token checklist |

`gmgn-onchain-analysis` was already the rightful class-level umbrella (had absorbed 5 prior skills). The other two were narrower siblings covering the same domain — each with some unique content not yet in the umbrella.

**What was done:**
1. **`gmgn-onchain-analysis`** (v1.1.0 → v1.2.0) — Patched with two major new sections:
   - *KOL Analysis & Event-Driven Narratives* section absorbing angle-analysis workflow, 4-stage conspiracy pump lifecycle, position management rules, event-driven narratives, market maker shadow tracking, YouTube crypto search/download, and BSC sentiment timing model
   - *Token Scoring & Robinhood Narrative* section absorbing the 0-100 composite scoring system and quick assessment workflow
2. **Reference files moved** into `gmgn-onchain-analysis/references/`:
   - From `cross-chain-meme-kol-analysis`: 5 unique files (kept), 4 superseded/stale files (not carried over)
   - From `crypto-meme-analysis`: 3 files (1 renamed to avoid collision)
3. **Both old skills archived** to `~/.hermes/skills/.archive/`

### Skills Left as Standalone (all at proper class level)

The remaining 14 agent-created skills are either already broad umbrellas (`multi-platform-search-cli`), in genuinely distinct domains (`openwrt-bypass-router`, `crypto-trading-bot`, `okx-onchainos-workflow`, `ubuntu-chinese-input-setup`), or complementary-but-distinct Hermes operations skills (`gateway-troubleshooting`, `hermes-analytics-reporting`, `hermes-cross-platform-deployment`, `hermes-web-access`, `community-skills`, `cron-state-persistence`, `provider-config-boundaries`, `linux-power-optimization`). No further clustering meets the "would a maintainer write this as one skill" bar.

```yaml
consolidations:
  - from: cross-chain-meme-kol-analysis
    into: gmgn-onchain-analysis
    reason: Narrower sibling covering same Solana→BSC KOL narrative analysis domain; unique content (angle analysis, position rules, event narratives, market maker tracking) absorbed as labeled subsection + reference files
  - from: crypto-meme-analysis
    into: gmgn-onchain-analysis
    reason: Narrower sibling covering same meme-coin analysis domain; unique content (0-100 scoring system, Robinhood narrative map, token checklist) absorbed as labeled subsection + reference files
prunings: []
```

## Recovery

- Restore an archived skill: `hermes curator restore <name>`
- All archives live under `~/.hermes/skills/.archive/` and are recoverable by `mv`
- See `run.json` in this directory for the full machine-readable record.
