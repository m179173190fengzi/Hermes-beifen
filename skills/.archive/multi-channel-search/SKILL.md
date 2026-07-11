---
name: multi-channel-search
description: Install and use multi-platform search CLI tools for searching/reading content across 14 internet channels — Twitter, Reddit, Bilibili, 小红书, YouTube, GitHub, RSS, V2EX, LinkedIn, web (Exa AI), and more.
version: 1.0.0
author: Hermes Agent
tags: [search, social-media, cli, agent-reach, web-scraping]
---

# Multi-Channel Search Tools

Installs and uses **Agent Reach** — a Python CLI that gives AI agents internet search/read capabilities across 14 platforms.

## Installation

### From GitHub (not on PyPI)

```bash
pipx install git+https://github.com/Panniantong/agent-reach.git
```

### All-in-One Channel Install (recommended after base install)

```bash
agent-reach install --channels=all --env=local
```

Options:
- `--channels=all` — install all optional channels (twitter, reddit, xiaohongshu, bilibili, xiaoyuzhou, linkedin)
- `--env=local` — local machine mode (detects browser for cookie import)
- `--proxy http://127.0.0.1:7890` — set proxy for agents to use
- `--safe` — dry-run, show what's needed without making changes

### Verify

```bash
agent-reach --help
agent-reach doctor   # check channel availability
```

## Post-Install Configuration

### GitHub Auth (for GitHub channel)

```bash
# Interactive browser login
gh auth login
# Select: GitHub.com → HTTPS → Yes (auth git) → Login with browser

# Set up git credentials through gh
gh auth setup-git

# Configure git identity
git config --global user.name "your-username"
git config --global user.email "your-email"
```

### Groq API Key (for 小宇宙 podcast transcription)

```bash
agent-reach configure groq-key gsk_xxxxx
```
Get a free key at https://console.groq.com

### Browser Extension (for OpenCLI channels: Twitter, Reddit, 小红书)

Must be done manually — Chrome Web Store:
https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk

After installing, run `opencli doctor` to verify.

### Additional Dependencies Installed Automatically

| Dependency | Purpose | Install Method |
|-----------|---------|---------------|
| `gh` (GitHub CLI) | GitHub repos/PRs/issues | `apt install gh` |
| `yt-dlp` | YouTube subtitles/audio | `pipx install yt-dlp` |
| `mcporter` | Exa AI semantic web search | `npm install -g mcporter` then `mcporter config add exa https://mcp.exa.ai/mcp` |
| `opencli` | Browser-session backend for Twitter/Reddit/小红书 | auto by agent-reach |
| `bili-cli` | B站 search/video/audio | auto by agent-reach |
| `ffmpeg` | Podcast transcription | auto by agent-reach |

## Quick Start

```bash
# Check which channels are configured
timeout 30 agent-reach doctor
```

Note: `agent-reach` CLI (v1.5.0) has no built-in `search` or `read` commands — those are exposed through the [pi extension](https://github.com/YrFnS/pi-agent-reach). Base CLI commands: `setup`, `install`, `configure`, `doctor`, `uninstall`, `skill`, `format`, `transcribe`, `check-update`, `watch`, `version`.

To get search/read tools in an agent platform, install the pi extension:

```bash
npm install -g @yrfns/pi-agent-reach
# Then use: pi install npm:pi-agent-reach
```

## Channels Available

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

## Pitfalls

- **Exa MCP not auto-configured** after `npm install -g mcporter` — must run `mcporter config add exa https://mcp.exa.ai/mcp` separately
- **Chrome extension is manual** — OpenCLI channels won't work without it, no way to automate
- **agent-reach not on PyPI** — must install from GitHub: `pipx install git+https://github.com/Panniantong/agent-reach.git`
- **GitHub token scope** — `gh auth login` token needs `repo`, `workflow`, `read:org` scopes; a classic PAT without `read:org` will fail with "error validating token: missing required scope 'read:org'"
- **GitHub auth via browser** — after running `gh auth login`, the user MUST complete the browser flow (enter 8-digit code, authorize) before `gh auth status` shows logged in
- **agent-reach doctor hangs** occasionally — use `timeout 30 agent-reach doctor` to avoid blocking
