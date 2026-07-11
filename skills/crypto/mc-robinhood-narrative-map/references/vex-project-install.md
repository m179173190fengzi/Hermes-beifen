# ProjectVex (VEX) — AI Trading Agent Desktop Runtime

## Overview

VEX is a **desktop AI trading agent runtime**, NOT a CLI tool or memecoin scanner. It runs on your local machine, executes trading missions under a safety gate, and records every decision locally.

- **Website**: https://www.projectvex.ai/
- **GitHub**: https://github.com/Vex-Foundation/Vex
- **Twitter/X**: @ProjectVEXai
- **Token CA**: `0x8ff92566f2e81bdd68edfaa8cde73942a723796b` (Robinhood Chain)

## Architecture

```
Your Desktop → VEX Runtime → Built-in AI Agent
                                  ↓
                  Connects to exchange APIs
                  Runs under safety gate (fail-closed)
                  Records all decisions to local log (hashed)
                  Keys encrypted AES-256-GCM, never leave machine
```

## Four Operating Modes

| Mode | Description |
|:-----|:------------|
| **Agent · Restricted** | User asks → agent analyzes → user approves → executes. Default. |
| **Agent · Full** | User asks → agent acts immediately. No pause. Speed trades approval. |
| **Mission · Restricted** | Autonomy on a leash. Plans/researches freely; money moves need user approval. |
| **Mission · Full** | Full autonomy. Runs unattended for days. Reports when done (deadline, capital depleted, max loss, no opportunity, or emergency stop). |

Each session sets two switches: **agent/mission** and **restricted/full**. Permission cannot widen mid-run. Unanswered approvals expire in 1 hour.

## Downloads (v0.1.2)

| Platform | File |
|:---------|:-----|
| **macOS (Apple Silicon)** | `Vex-0.1.2-mac-arm64.dmg` |
| **macOS (Intel)** | `Vex-0.1.2-mac-x64.dmg` |
| **Linux** | `Vex-0.1.2-linux-x86_64.AppImage` |
| **Linux (Debian/Ubuntu)** | `Vex-0.1.2-linux-amd64.deb` |

**No Windows release as of v0.1.2.**

## Linux Install

```bash
# Download AppImage
curl -sL "https://github.com/Vex-Foundation/Vex/releases/download/v0.1.2/Vex-0.1.2-linux-x86_64.AppImage" -o /tmp/Vex.AppImage
chmod +x /tmp/Vex.AppImage

# Or download .deb for Ubuntu/Debian
curl -sL "https://github.com/Vex-Foundation/Vex/releases/download/v0.1.2/Vex-0.1.2-linux-amd64.deb" -o /tmp/Vex.deb
sudo dpkg -i /tmp/Vex.deb
```

## Latest Release Info (as of 2026-07-10)

| Field | Value |
|:------|:------|
| Release tag | v0.1.2 |
| AppImage size | ~165 MB |
| Download source | GitHub releases: github.com/Vex-Foundation/Vex/releases/latest |

## Token Data

| Field | Value |
|:------|:------|
| Symbol | $VEX |
| Chain | Robinhood Chain |
| MC | $12.05M (-26.6% 1h) |
| Liquidity | $420,980 |
| Holders | 3,178 |
| Top10 | 51.72% ⚠️ |
| Smart Money | 18 ✅ |
| Bundle | 0.81% ✅ |
| Launchpad | Virtuals v2 |
| All-time high MC | $18.9M |

## Notes

- VEX is part of the **AI Agent Infrastructure** narrative layer on Robinhood Chain (alongside $RAXOL, $SPARKLE, $AXOL)
- This is a "semi-meme, semi-utility" category — longer lifespan than pure meme but still high volatility
- The foundation behind VEX (Vex-Foundation) is the same team maintaining the open-source GitHub repo
- Token traded on Virtuals v2 launchpad, not pump.fun
