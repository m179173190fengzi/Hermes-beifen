# Curator run — 2026-07-07T22:30:40.125382+00:00

Model: `deepseek-v4-flash` via `deepseek`  ·  Duration: 3m 36s  ·  Agent-created skills: 21 → 11 (-10)

## Auto-transitions (pure, no LLM)

- checked: 21
- marked stale: 0
- archived (no LLM, pure time-based staleness): 0
- reactivated: 0

## LLM consolidation pass

- tool calls: **47** (by name: patch=5, read_file=4, skill_view=30, terminal=8)
- consolidated into umbrellas: **9**
- pruned (archived for staleness): **1**
- new skills this run: **0**
- state transitions (active ↔ stale ↔ archived): **0**

### Consolidated into umbrella skills (9)

_These skills were **absorbed into another skill** during this run — their content still lives, just under a different name. The original directory was moved to `~/.hermes/skills/.archive/` for safety and can be restored via `hermes curator restore <name>` if the consolidation was wrong._

- `agent-reach` → merged into `multi-platform-search-cli` — Near-duplicate — same Agent Reach CLI install/config as the umbrella, with additional per-component install and Twitter auth fallback notes
- `crypto-market-data` → merged into `gmgn-onchain-analysis` — General market data (BTC/ETH price fetching) is complementary to GMGN's on-chain focus — blockchain.info/CoinGecko data sources and Chinese presentation format merged
- `freqtrade-install` → merged into `crypto-trading-bot` — Narrow install-only skill that is a sub-workflow of the broader crypto trading bot umbrella — install details, manual FreqUI, OKX auth, and FreqUI webserver sections merged
- `freqtrade-strategy` → merged into `crypto-trading-bot` — Strategy development is a core sub-domain of the crypto trading bot umbrella — workflow, indicator patterns, iteration optimization, and reference strategies merged
- `freqtrade-strategy-dev` → merged into `crypto-trading-bot` — Near-duplicate of freqtrade-strategy with same scope — merged content recycled and combined in the Strategy Development section with user-specific corrections (看大做小, MA parameters, timeframe evaluation)
- `gmgn-cli-setup` → merged into `gmgn-onchain-analysis` — Setup/config is a prerequisite sub-workflow of GMGN on-chain analysis — install guide, credential masking, DexScreener API, and cron monitoring patterns merged
- `meme-coin-analysis` → merged into `gmgn-onchain-analysis` — Meme coin analysis methodology is a usage pattern on top of GMGN data — BSC phase detection, entry/exit logic, cross-chain mirroring, and KOL tracking tools merged
- `multi-channel-search` → merged into `multi-platform-search-cli` — Near-duplicate — identical 14-channel search CLI setup, content merged as channel quick-reference table
- `ubuntu-power-optimization` → merged into `linux-power-optimization` — Near-duplicate — same power optimization workflow (CPU governor, kernel params, service pruning, Wayland display), variant script and display verification reference preserved

### Pruned — archived for staleness (1)

_These skills were archived without being merged into an umbrella (e.g. stale, unused, or judged irrelevant). Directories live under `~/.hermes/skills/.archive/`. Restore any via `hermes curator restore <name>`._

- `ssh-remote-access` — Truly stale — 0 activity/use/views since creation, never used, generic SSH setup content available in countless other sources with no unique experiential knowledge

## LLM final summary

All consolidations complete. Here's the full report:

---

## Consolidation Summary

### 5 clusters processed, 10 skills archived

**Cluster 1: Multi-Platform Search** — Consolidated 3 skills into `multi-platform-search-cli`
- `agent-reach` → merged as labeled sub-section + `references/agent-reach-session.md`
- `multi-channel-search` → merged as channel quick-reference table
- Umbrella patched with agent-reach-specific setup notes (per-component install, desktop autostart, Twitter auth fallback)

**Cluster 2: Linux Power Optimization** — Consolidated 2 skills into `linux-power-optimization`
- `ubuntu-power-optimization` → near-identical variant, merged completely
- Support files preserved: `scripts/ubuntu-setup-powersave.sh`, `references/display-verification.md`
- Umbrella patched with "Merged Skills" note

**Cluster 3: FreqTrade/Crypto Trading** — Consolidated 4 skills into `crypto-trading-bot`
- `freqtrade-install` → merged as "Installation Details" (+ OKX API auth, FreqUI webserver sections)
- `freqtrade-strategy` + `freqtrade-strategy-dev` → merged as "Strategy Development" (workflow, MA cluster/bearish alignment/smooth decline patterns, iterative optimization, timeframe sensitivity, pitfalls)
- Support files moved: `templates/freqtrade-startup.sh`, 3 reference strategy docs (six-ma-strategy, six-ma-cluster-strategy, dual-ma-crossover)

**Cluster 4: GMGN Ecosystem** — Consolidated 4 skills into `gmgn-onchain-analysis`
- `gmgn-cli-setup` → merged as "GMGN CLI Setup Guide" (install, key gen, credential masking, DexScreener, cron monitoring)
- `meme-coin-analysis` → merged as "BSC Market Phase Detection" + "Cross-Chain Meme Analysis" (entry/exit logic, KOL tracking)
- `crypto-market-data` → merged as "General Market Data" (blockchain.info, CoinGecko, Chinese presentation format)
- 8 reference files relocated (dexscreener-api-usage, credential-masking-workaround, cz-final-form-bull-pump-analysis, bsc-market-phase-analysis, data-sources, solana-meme-research, bsc-meme-trading)

**Pruning**: `ssh-remote-access` — 0 activity/use/view since creation, generic SSH setup advice, no unique value

### Remaining standalone skills (11) — left alone because they are already class-level umbrellas or don't share clusters:
- `cron-state-persistence` — unique cross-cutting cron pattern, no siblings
- `gateway-troubleshooting` — unique Hermes gateway diagnostics, no siblings
- `hermes-analytics-reporting` — unique Hermes usage reporting, no siblings
- `okx-onchainos-workflow` — unique OKX onchainOS setup, no siblings
- `openwrt-bypass-router` — unique router setup, no siblings
- `provider-config-boundaries` — unique Hermes config guardrails, no siblings
- `ubuntu-chinese-input-setup` — unique desktop setup, no siblings
- `gmgn-cooking`, `gmgn-market`, `gmgn-portfolio`, `gmgn-swap`, `gmgn-token`, `gmgn-track` — hub-installed (skipped per rule)
- `v4-bearish-alignment-strategy` — hub-installed (skipped)
- All `okx-*` skills — hub-installed (skipped)

## Structured summary (required)

```yaml
consolidations:
  - from: agent-reach
    into: multi-platform-search-cli
    reason: Near-duplicate — same Agent Reach CLI install/config as the umbrella, with additional per-component install and Twitter auth fallback notes
  - from: multi-channel-search
    into: multi-platform-search-cli
    reason: Near-duplicate — identical 14-channel search CLI setup, content merged as channel quick-reference table
  - from: ubuntu-power-optimization
    into: linux-power-optimization
    reason: Near-duplicate — same power optimization workflow (CPU governor, kernel params, service pruning, Wayland display), variant script and display verification reference preserved
  - from: freqtrade-install
    into: crypto-trading-bot
    reason: Narrow install-only skill that is a sub-workflow of the broader crypto trading bot umbrella — install details, manual FreqUI, OKX auth, and FreqUI webserver sections merged
  - from: freqtrade-strategy
    into: crypto-trading-bot
    reason: Strategy development is a core sub-domain of the crypto trading bot umbrella — workflow, indicator patterns, iteration optimization, and reference strategies merged
  - from: freqtrade-strategy-dev
    into: crypto-trading-bot
    reason: Near-duplicate of freqtrade-strategy with same scope — merged content recycled and combined in the Strategy Development section with user-specific corrections (看大做小, MA parameters, timeframe evaluation)
  - from: gmgn-cli-setup
    into: gmgn-onchain-analysis
    reason: Setup/config is a prerequisite sub-workflow of GMGN on-chain analysis — install guide, credential masking, DexScreener API, and cron monitoring patterns merged
  - from: meme-coin-analysis
    into: gmgn-onchain-analysis
    reason: Meme coin analysis methodology is a usage pattern on top of GMGN data — BSC phase detection, entry/exit logic, cross-chain mirroring, and KOL tracking tools merged
  - from: crypto-market-data
    into: gmgn-onchain-analysis
    reason: General market data (BTC/ETH price fetching) is complementary to GMGN's on-chain focus — blockchain.info/CoinGecko data sources and Chinese presentation format merged
prunings:
  - name: ssh-remote-access
    reason: Truly stale — 0 activity/use/views since creation, never used, generic SSH setup content available in countless other sources with no unique experiential knowledge
```

## Recovery

- Restore an archived skill: `hermes curator restore <name>`
- All archives live under `~/.hermes/skills/.archive/` and are recoverable by `mv`
- See `run.json` in this directory for the full machine-readable record.
