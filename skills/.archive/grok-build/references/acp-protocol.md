# Grok Build ACP Protocol Reference

Discovered by probing `grok agent stdio` with a JSON-RPC initialize message.

## Protocol Probe

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":1,"capabilities":{},"clientInfo":{"name":"test","version":"1"}},"id":1}' | grok agent stdio
```

## Key Response Fields

| Field | Value |
|-------|-------|
| protocolVersion | 1 |
| agentVersion | 0.2.112 |
| currentModelId | grok-4.5 |
| contextWindow | 500K tokens |
| agentType | grok-build-plan |
| supportsReasoningEffort | true |
| defaultEffort | high |

## Auth Methods

- `cached_token` — uses ~/.grok/auth.json
- `grok.com` — browser OAuth

## Available Models

Single model family returned: grok-4.5, with 3 reasoning effort levels:
- high (default) — "Highest implementation quality with extensive reasoning"
- medium — "Balanced effort with standard implementation and testing"
- low — "Quick, fast implementations"

## Capabilities

- `loadSession: true`
- `promptCapabilities.image: false` (no image input)
- `promptCapabilities.audio: false`
- `mcpCapabilities.http: true`
- `mcpCapabilities.sse: true`
- `sessionCapabilities: {}` (basic)
- `auth: {}` (browser OAuth)

## Custom x.ai Extensions

Under `_meta`:
- `x.ai/fs_notify` — filesystem notifications
- `x.ai/hooks` — blocking events (pre_tool_use, stop, subagent_stop), decisions (deny, block), stop signals (continue, stopReason, additionalContext)
- `x.ai/capabilities.toolOverrides` — x_keyword_search, x_semantic_search, x_user_search (false), x_thread_fetch (false)
- `x.ai/mcp/sdk` — MCP SDK integration
- `x.ai/pluginDirs` — plugin directory loading

## Available Commands (TUI Slash Commands via ACP)

| Command | Description |
|---------|-------------|
| compact | Compress conversation history |
| always-approve | Toggle auto-approve mode |
| context | Show context window usage |
| session-info | Session details (model, turns, context) |
| deep-research | Multi-agent research with cited report |
| workflow | Launch/manage saved workflows |
| goal | Set autonomous goal with token budget |

## Known Limitation

The `delegate_task` tool with `acp_command="grok"` and `acp_args=["agent","stdio"]` did not successfully route through the ACP transport — the Hermes subagent system fell back to the default subagent instead. This may require an update to Hermes' ACP client implementation or a different invocation method.
