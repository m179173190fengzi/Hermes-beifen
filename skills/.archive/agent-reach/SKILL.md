---
name: agent-reach
description: "Install and configure Agent Reach CLI — gives AI agents internet search across 14 channels (GitHub, YouTube, Twitter, Reddit, B站, 小红书, RSS, V2EX, 小宇宙, etc.)"
version: 1.0.0
author: Hermes Agent
tags: [agent-reach, search, social-media, web-scraping, research]
---

# Agent Reach CLI Setup

[Agent Reach](https://github.com/Panniantong/agent-reach) — CLI tool that gives AI agents access to 14 internet channels for search, read, and status operations.

## Installation

**⚠️ User preference: Do everything yourself — never ask user to copy/paste terminal commands.** All `pipx`, `npm`, `apt` installs should be executed directly by the agent. Exception: browser OAuth flows (gh auth login, etc.) require user interaction for the browser step.

```bash
# Install from GitHub (not on PyPI)
pipx install git+https://github.com/Panniantong/agent-reach.git
```

## All-in-One Channel Setup

```bash
agent-reach install --channels=all --env=local
```

This installs everything: gh CLI, yt-dlp, mcporter (Exa MCP for semantic search), bili-cli, twitter-cli, OpenCLI, and transcription tools.

## Verify Status

```bash
agent-reach doctor
```

## Required Manual Steps (must tell user)

After `install --channels=all`, the following still need user action:

1. **GitHub** — `gh auth login` (then select GitHub.com → HTTPS → browser login)
2. **Chrome Extension** (for Reddit/小红书/Twitter) — install from Chrome Web Store:
   `https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk`
3. **Groq API Key** (for 小宇宙 podcast transcription) — get free key at https://console.groq.com then:
   ```bash
   agent-reach configure groq-key gsk_xxxxx
   ```

## Per-Component Installation (if --channels=all fails)

### GitHub CLI
```bash
sudo apt install gh
```

### YouTube (yt-dlp)
```bash
pipx install yt-dlp
```

### Semantic Web Search (Exa MCP via mcporter)
```bash
npm install -g mcporter
mcporter config add exa https://mcp.exa.ai/mcp
```

### pi-agent-reach (Native Hermes integration, optional)
```bash
npm install -g @yrfns/pi-agent-reach
```

## Chat Channels Status

11/13 channels typically available after full install. Remaining: 雪球 (Xueqiu), LinkedIn.

## Common Issues

| Problem | Fix |
|---------|-----|
| `gh auth login --with-token` fails with `missing required scope 'read:org'` | Generate token with `read:org` scope, OR use browser login flow instead |
| Cloudflare blocks browser search | Use curl with proxy (`-x http://127.0.0.1:7890`) or API endpoints directly |

## Twitter/X Auth Fallback Pattern

The `twitter` CLI and `opencli` have **different auth mechanisms**. If one doesn't work, try the other:

| Tool | Auth method | When it works |
|------|-------------|---------------|
| `twitter` CLI (pipx) | Browser cookie extraction | User logged into x.com, browser keyring unlocked |
| `opencli` | Chrome extension + browser bridge | Extension installed, x.com logged in, browser tab open |

**Diagnostic flow when Twitter access fails:**
1. Try `twitter search "query" --type top` — cookies may be accessible headlessly
2. Try `opencli twitter search "query" --limit 5` — needs browser open
3. If both timeout → tell user to open Chrome → log into x.com → keep tab open → retry

**Useful commands:**
```bash
# Search tweets
twitter search "solana" --type top
# From specific user
twitter search "from:cz_binance" --type latest
# OpenCLI version (needs Chrome extension)
opencli twitter search "solana memecoin" --limit 10
```

## Desktop Autostart Pattern

To auto-open x.com + gmgn.ai in Chrome on boot:

```ini
[Desktop Entry]
Type=Application
Name=Open Twitter/X & GMGN
Exec=/usr/bin/google-chrome --new-window https://x.com https://gmgn.ai
Icon=google-chrome
Categories=Network;
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
```

Save to `~/.config/autostart/twitter.desktop`.

## Usage Patterns

For detailed search patterns, OpenCLI Twitter usage, and Chinese crypto KOL tracking, see the `multi-platform-search-cli` skill (social-media category) which covers agent-reach + OpenCLI + twitter-cli usage with real session examples.
