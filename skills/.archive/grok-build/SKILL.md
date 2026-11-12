---
name: grok-build
description: "Delegate coding to SpaceXAI's Grok Build CLI (features, refactoring, code review)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Grok, xAI, Code-Review, Refactoring, ACP]
    related_skills: [claude-code, codex, opencode]
---

# Grok Build — Hermes Orchestration Guide

Delegate coding tasks to [Grok Build](https://x.ai/cli) (SpaceXAI/xAI's autonomous coding agent CLI). Grok runs as a full-screen TUI or in single-turn text mode. It uses **grok-4.5** with up to 500K context tokens and supports reasoning effort levels, MCP servers, and subagents.

## Prerequisites

```bash
# Install
curl -fsSL https://x.ai/cli/install.sh | bash
```
⚠️ The binary is ~200MB. In Hermes, use `background=true` or a generous timeout (120s+). Foreground mode times out mid-download.

```bash
# After install, binary at ~/.local/bin/grok and ~/.grok/bin/grok
# First launch opens browser for OAuth — complete the login flow
grok --version        # verify
```

- **Auth:** browser OAuth on first `grok` launch. Already-authorized tokens live in `~/.grok/auth.json`.
- **Config:** `~/.grok/config.toml`
- **Update:** re-run the install script or `grok update` (if available)
- No npm/cargo needed — prebuilt binary

## Mode 1: Single-turn Text (`--single` / `-p`) — PREFERRED

Runs a one-shot text query, returns the response, and exits. No PTY needed. Fast and clean for questions, explanations, code generation output.

```bash
grok --single "Explain how Solana token metadata works"
grok -p "Write a Python function that fetches token holders from Solscan API"
```

**When to use:** quick Q&A, code explanation, generating code snippets to stdout, any task where you just need the answer text.

**Limitation:** `--single` mode returns text only and does NOT execute tools (no file writes, no shell). Verified working.

## Mode 2: TUI (Interactive)

Full-screen terminal UI with slash commands, tool execution, file editing, and shell access.

```bash
grok                          # launch TUI
grok "Refactor the auth module"  # TUI with initial prompt
grok --cwd /path/to/project   # start in specific directory
```

**Requires a real terminal** — cannot run in background/headless Hermes terminal sessions.

### TUI Slash Commands (selected)

| Command | Purpose |
|---------|---------|
| `/tutorial` | Interactive tutorial (Elon's recommended first step) |
| `/compact` | Compress conversation to save context |
| `/context` | Show context window usage |
| `/help` | Show all commands |
| `/model` | Switch model mid-session |
| `/effort` | Set reasoning effort (low/medium/high) |
| `/deep-research` | Multi-agent research with cited report |
| `/goal` | Set autonomous goal with token budget |
| `/workflow` | Launch a saved workflow |
| `always-approve on/off` | Toggle auto-approve mode |

### Keyboard Shortcuts (TUI)

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel |
| `Ctrl+D` | Exit |
| `Ctrl+R` | Search history |
| `Esc Esc` | Rewind/summarize |
| `Alt+P` | Switch model |
| `Shift+Enter` | Newline (multiline input) |

## Mode 3: ACP stdio (`grok agent stdio`) — Subagent Integration

Grok exposes an ACP-compatible stdio transport for programmatic tool-calling. Supports initialization with protocol version 1, JSON-RPC messaging, and full tool execution (file read/write, bash, web search).

```bash
# Protocol probe
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":1,"capabilities":{},"clientInfo":{"name":"hermes","version":"1"}},"id":1}' | grok agent stdio
```

**Response includes:**
- agentVersion, agentId, currentModelId (`grok-4.5`)
- Available models with reasoning effort support
- Session capabilities (loadSession, mcp, hooks)
- Auth methods (cached_token, grok.com)

**Hermes delegate_task integration attempt:**
```
delegate_task(acp_command="grok", acp_args=["agent", "stdio"], ...)
```
⚠️ **Known pitfall:** `delegate_task` with `acp_command="grok"` did NOT route through the ACP transport properly in testing. The subagent fell back to the default Hermes subagent instead. This may require an update to the Hermes ACP client or a different invocation pattern. Until resolved, use terminal with pty=true for Grok tasks instead.

## Model & Capabilities

| Property | Value |
|----------|-------|
| Default model | `grok-4.5` |
| Context window | 500K tokens |
| Reasoning effort | low, medium, high (high=default) |
| Agent type | `grok-build-plan` |
| MCP support | http + sse transports |
| Auth | OAuth (browser) + cached token |
| OS support | macOS, Linux, Windows |

## Pitfalls & Gotchas

1. **Install script TIMES OUT in foreground mode** — the binary is ~200MB. Always use `background=true, notify_on_complete=true` when installing via Hermes terminal. Foreground mode with even 120s timeout fails mid-download.
2. **`grok --single` is text-only** — no tool execution (no file writes, no bash). For tasks requiring tool use, use the TUI mode with `pty=true`.
3. **`grok agent stdio` ACP mode** — protocol is custom JSON-RPC (not standard MCP or OpenAI ACP). The `delegate_task` tool's `acp_command` parameter may not bridge correctly.
4. **No `--output-format json`** — unlike Claude Code, Grok `--single` mode outputs plain text only. No structured JSON result envelope.
5. **Auth is required** — first run opens browser. If headless, need to manually copy auth token or use deployment key (`GROK_DEPLOYMENT_KEY` env var).
6. **TUI requires real terminal** — cannot run in Hermes background terminal sessions. Use `grok --single` for headless automation.
7. **Config location** — `~/.grok/config.toml`, not project-local. No equivalent of CLAUDE.md/AGENTS.md auto-loading from project root (yet).
