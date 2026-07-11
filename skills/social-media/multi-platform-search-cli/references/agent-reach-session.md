# Agent Reach Session Reference (2026-06-28)

## Exact Install Commands Used

```bash
# Step 1: Install core CLI
pipx install git+https://github.com/Panniantong/agent-reach.git
# → agent-reach 1.5.0

# Step 2: Install per-component dependencies
sudo apt install -y gh           # GitHub CLI 2.46.0
pipx install yt-dlp              # YouTube extractor 2026.6.9
npm install -g mcporter          # MCP porter for Exa search

# Step 3: Configure Exa MCP
mcporter config add exa https://mcp.exa.ai/mcp

# Step 4: Install all optional channels
agent-reach install --channels=all --env=local

# Step 5: Configure Groq for podcast transcription
agent-reach configure groq-key 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
```

## GitHub Auth Flow

```bash
# Interactive browser login
gh auth login
# Selections: GitHub.com → HTTPS → Yes (auth git) → Login with web browser
# Then copy 8-character code, press Enter, authorize in browser

# Set up git credentials
gh auth setup-git
git config --global user.name "username"
git config --global user.email "username@users.noreply.github.com"
```

## Result After Full Install

```
11/13 channels available:
  ✅ GitHub       (full: read, search, Fork, Issue, PR)
  ✅ YouTube      (subtitles + audio transcribe via groq)
  ✅ V2EX         (public API)
  ✅ RSS/Atom     (feed reader)
  ✅ Semantic Web (mcporter + Exa, free)
  ✅ Web Pages    (Jina Reader)
  ✅ Twitter/X    (OpenCLI, browser session)
  ✅ Reddit       (OpenCLI)
  ✅ B站          (bili-cli)
  ✅ 小红书       (OpenCLI)
  ✅ 小宇宙       (groq-whisper transcription)
  ❌ 雪球, LinkedIn
```

## OpenCLI Twitter Search Workflow

Used for crypto alpha hunting (finding shilled tokens on Solana).

```bash
# Search Chinese crypto Twitter for calls
opencli twitter search "solana 土狗 喊单" --limit 10

# Search by token symbol
opencli twitter search "\$ANSEM solana" --limit 10

# Search from a specific KOL
opencli twitter search "solana memecoin" --from blknoiz06 --limit 10
```

**Prerequisites:** User must have x.com open and logged in Chrome with OpenCLI extension installed.

**Output fields of interest:** author, text, likes, views, created_at, quoted_tweet (for retweet chains), media_urls.

## User Profile

- GitHub username: m179173190fengzi
- Groq API key prefix: gsk_ECzT2... (configured)
- Uses proxy: 127.0.0.1:7890
- Chinese locale, prefers Chinese responses
