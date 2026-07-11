# Playwright MCP Setup

Install [Playwright MCP](https://github.com/microsoft/playwright-mcp) (`@playwright/mcp`) to give Hermes a real Chromium browser backend that can bypass Cloudflare and other bot-detection services.

## Installation

```bash
# 1. Install the npm package globally
npm install -g @playwright/mcp

# 2. Install Chromium browser
npx playwright install chromium
```

## Configuration

Add to `~/.hermes/config.yaml` under `mcp_servers`:

```yaml
mcp_servers:
  playwright:
    command: npx
    args:
    - @playwright/mcp@latest
    enabled: true
```

Or use the `hermes mcp add` CLI command:

```bash
echo "Y" | hermes mcp add playwright --command npx --args "@playwright/mcp@latest"
```

## What It Provides

23 browser automation tools including:
- `browser_navigate` — Navigate to URLs (real Chromium, bypasses Cloudflare)
- `browser_snapshot` — Accessibility-tree snapshots
- `browser_click`, `browser_type`, `browser_hover` — Interaction
- `browser_screenshot` — Visual output
- `browser_tabs` — Multi-tab management
- `browser_network_requests` — Network request inspection

## How It Differs From Default Browser Tools

| Aspect | Default Hermes browser | Playwright MCP |
|--------|----------------------|----------------|
| Backend | Browserbase/stealth (proxy-based) | Local Chromium |
| Cloudflare handling | Gets blocked on aggressive sites | Bypasses most Cloudflare sites |
| Network inspection | Limited | Full network request capture |
| Screenshots | Via separate vision pipeline | Native screenshot tool |
| File uploads | Not supported | `browser_file_upload` tool |
| Drag-and-drop | Not supported | `browser_drag` tool |

## Use Cases

- **Cloudflare-bypassed web search** — Search Google, Bing, DuckDuckGo through real browser
- **gmgn.ai / DexScreener access** — These sites block headless browsers but Playwright Chrome passes
- **Form filling** — `browser_fill_form` for multi-field forms
- **Network-level debugging** — Capture API responses with `browser_network_requests`

## New Session Required

After configuration, the user must start a **new session** (`/new`) to pick up Playwright MCP tools. They replace the default browser tools in the toolset.

## Known Issues

- On first launch, the `UNDICI-EHPA` warning about `EnvHttpProxyAgent` is harmless — it fires because the system `HTTP_PROXY` env var is set but Playwright handles its own proxy
- Headless shell (~114 MB) is downloaded alongside full Chrome (~177 MB) — both are needed
- `browser_run_code_unsafe` executes JavaScript in the Playwright server process — RCE-equivalent power, use with caution
