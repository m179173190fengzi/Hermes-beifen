---
name: multi-platform-search-cli
description: "UMBRELLA — Install and configure multi-platform internet search/read CLI tools (Agent Reach, OpenCLI, twitter-cli) across 14+ channels: Twitter/X, Reddit, GitHub, YouTube, Bilibili, Xiaohongshu, Xiaoyuzhou, RSS, V2EX, LinkedIn, Xueqiu, and semantic web search. Absorbed agent-reach and multi-channel-search."
version: 1.0.0
author: Hermes Agent
tags: [search, social-media, web-scraping, cli-tools, multi-platform]
---

# Multi-Platform Search CLI Tools

Install and configure CLI tools that can search and read from multiple internet platforms.

## Tools Covered

- **Agent Reach** (`agent-reach`) — Python CLI, 14 internet channels
- **OpenCLI** (`opencli`) — Browser-session-based access to Twitter, Reddit, Xiaohongshu, etc.
- **twitter-cli** (`twitter`) — Twitter/X search and timeline

## Agent Reach Installation

```bash
# 1. Install the Python CLI from GitHub
pipx install git+https://github.com/Panniantong/agent-reach.git

# 2. Install all optional channels
agent-reach install --channels=all --env=local

# 3. Verify status
agent-reach doctor
```

## Channel Dependencies

| Channel | Dependency | Install | Additional Setup |
|---------|-----------|---------|-----------------|
| GitHub | gh CLI | `sudo apt-get install gh` | `gh auth login` + `gh auth setup-git` |
| YouTube/audio | yt-dlp | `pipx install yt-dlp` | — |
| Semantic search | mcporter + Exa MCP | `npm install -g mcporter && mcporter config add exa https://mcp.exa.ai/mcp` | — |
| Bilibili | bili-cli | auto-installed by `agent-reach install` | — |
| Twitter/X | OpenCLI | auto-installed | Need Chrome extension + logged into x.com |
| Reddit | OpenCLI | auto-installed | Need Chrome extension + logged into reddit.com |
| Xiaohongshu | OpenCLI | auto-installed | Need Chrome extension |
| Podcast transcription | Groq API key | `agent-reach configure groq-key gsk_xxxx` | Get key from https://console.groq.com |

## Twitter/X Search via OpenCLI

Requires: Chrome extension installed AND user logged into x.com in Chrome with the tab still open:

```bash
opencli twitter search "query" --limit 10
opencli twitter search "query" --from username
opencli twitter search "query" --type top
```

**Pitfall:** `twitter-cli` (standalone) needs browser cookies or auth tokens. OpenCLI is more reliable for desktop use since it reuses the browser session.

**Common OpenCLI auth issues:**
- `AUTH_REQUIRED: Not logged into x.com (no ct0 cookie)` → user needs to open x.com in Chrome and log in, then keep the tab open
- Even after user says \"I'm logged in\", verify with `opencli twitter search \"test\" --limit 1` — don't assume it works
- If OpenCLI can't access browser cookies, the terminal runs headless and can't see the browser profile. The user must have Chrome open with x.com active
- **Session expiration:** OpenCLI works for one command but then subsequent commands time out (`[Command timed out after Ns]`) → the browser session likely went idle or the extension disconnected. Ask the user to reopen Chrome with x.com active and try again.
- **Timing out vs auth error:** A timeout (exit 124) after `[UNDICI-EHPA]` warning usually means OpenCLI can reach the browser extension but the X API request itself timed out. An explicit `AUTH_REQUIRED` error means the extension can't find cookies. Treat these differently — timeout = retry with user re-opening browser; auth error = user needs to log in to x.com.\n- **twitter-cli vs OpenCLI:** These use completely different auth paths. `twitter-cli` extracts browser cookies via keyring/subprocess (often fails headless, but on desktop with an active browser session it can be more reliable). OpenCLI uses the Chrome extension bridge which can time out even with the browser open. If one fails, try the other — they use separate credential stores and one may work when the other doesn't.\n- **Recovery pattern:** If the first command works but subsequent ones timeout, the browser session may have idled. Each browser-wake cycle may only support one successful search. Batch searches into a single command when possible.

**Usage patterns from real session:**
- Chinese crypto keywords: `opencli twitter search "solana 土狗 喊单" --limit 10` works in Chinese
- By specific KOL: `opencli twitter search "\$ansem solana" --limit 10`
- Time-specific: tweets from today (June 28, 2026) showed Ansem pumping $ANSEM from 200K to 80M+ MC

## Chinese Crypto Twitter Search Patterns

When searching for Chinese crypto KOL activity and meme coin shilling on Solana:

```bash
# Generic "shilling" / "pumping" search (Chinese)
opencli twitter search "solana 土狗 喊单" --limit 10

# Specific token shill
opencli twitter search "\$ansem solana" --limit 10

# By KOL name (search mentions, not from:)
opencli twitter search "blknoiz06" --limit 10

# Today's hot topics
opencli twitter search "solana memecoin pump" --type top --limit 10
```

### OpenCLI-specific usage patterns

- **The `from:` operator causes timeouts**: `opencli twitter search "from:cz_binance"` consistently times out. Search by username mention instead (`opencli twitter search "cz_binance" --limit 5`).
- **Session expiration between commands**: OpenCLI may work for one search but subsequent commands timeout. The Chrome/browser extension session went idle. Ask the user to reopen Chrome with x.com active, then retry immediately.
- **Recovery pattern**: If first command works but subsequent ones timeout → one successful search per browser-wake cycle. Batch multiple searches into a single command when possible.
- **Proxy warning is normal**: The `[UNDICI-EHPA] Warning: EnvHttpProxyAgent is experimental` at OpenCLI startup is normal behind a proxy — ignore it.
- **twitter-cli vs OpenCLI** use completely different auth paths. **twitter-cli v0.8.5+ now works WITHOUT OAuth** — uses built-in guest API token, not browser cookies. This is the **preferred** method for X searches as it works in headless/cron environments without any auth setup. Try twitter-cli FIRST before OpenCLI. OpenCLI uses the Chrome extension bridge (needs browser open). If one fails, try the other — they use separate auth paths.

### Known-working KOLs to track

| Twitter Handle | Name | Significance |
|---|---|---|
| `blknoiz06` | Ansem 🐂🀄️ | Solana meme coin top KOL, pumped $ANSEM from 200K to 80M+ MC |
| `cz_binance` | CZ | Binance founder |
| `heyibinance` | He Yi | Binance co-founder |

## Agent-Reach-Specific Setup Notes

The following details were absorbed from the separate `agent-reach` skill.

### Per-Component Installation (if `--channels=all` fails)

```bash
# GitHub CLI
sudo apt install gh

# YouTube (yt-dlp)
pipx install yt-dlp

# Semantic Web Search (Exa MCP via mcporter)
npm install -g mcporter
mcporter config add exa https://mcp.exa.ai/mcp

# pi-agent-reach (Native Hermes integration, optional)
npm install -g @yrfns/pi-agent-reach
```

### Desktop Autostart (open x.com + gmgn.ai on boot)

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

### Twitter/X Auth Fallback Pattern

The `twitter` CLI and `opencli` have **different auth mechanisms**. If one doesn't work, try the other:

| Tool | Auth method | When it works |
|------|-------------|---------------|
| `twitter` CLI (pipx) | Browser cookie extraction | User logged into x.com, browser keyring unlocked |
| `opencli` | Chrome extension + browser bridge | Extension installed, x.com logged in, browser tab open |

**Diagnostic flow when Twitter access fails:**
1. Try `twitter search "query" --type top` — cookies may be accessible headlessly
2. Try `opencli twitter search "query" --limit 5` — needs browser open
3. If both timeout → tell user to open Chrome → log into x.com → keep tab open → retry

### Session Reference

A detailed install + verify session log from 2026-06-28 is available at `references/agent-reach-session.md`.

## Channel Quick-Reference Table

Absorbed from the `multi-channel-search` skill for a compact channel overview:

| Channel | Auth Required | Notes |
|---------|:------------:|-------|
| web (Exa AI) | No | Semantic search, free tier |
| youtube | No | Subtitles + audio transcription |
| github | gh CLI auth | Repos, issues, PRs |
| bilibili | No | bili-cli (search only without login) |
| v2ex | No | Public API |
| rss/atom | No | Feed reading |
| jina reader | No | Any URL via Jina |
| twitter/x | OpenCLI + Chrome ext | Browser login session |
| reddit | OpenCLI + Chrome ext | Browser login session |
| xiaohongshu | OpenCLI + Chrome ext | Browser login session |
| xiaoyuzhou | Groq API key | Podcast transcription |
| linkedin | OpenCLI | Browser login session |
| xueqiu | OpenCLI | Stock market |

## Important Notes

- Agent Reach is a **Python CLI** (`pipx install` from GitHub), not an npm package
- `@yrfns/pi-agent-reach` is a separate **pi extension** wrapping Agent Reach — only useful if you use the `pi` CLI
- OpenCLI requires a Chrome extension: https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
- GitHub auth needs both `gh auth login` AND `gh auth setup-git` + `git config` for full functionality
