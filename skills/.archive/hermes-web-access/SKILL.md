---
name: hermes-web-access
description: "Run Hermes Agent in a web browser — via built-in dashboard or ttyd terminal. Covers setup, troubleshooting, and production deployment on headless/cloud machines."
version: 1.1.0
author: Hermes Agent
tags: [hermes, web, browser, dashboard, ttyd, self-hosting]
---

# Hermes Web Access

Run Hermes in a browser instead of a terminal. Two approaches:

1. **Built-in Dashboard** — `hermes dashboard` (config/sessions management UI)  
   `hermes dashboard --tui` (full chat in browser via PTY/WebSocket)
2. **ttyd fallback** — lightweight web terminal when dashboard is unavailable

## Built-in Dashboard

```bash
# Config/sessions management UI (no chat)
hermes dashboard

# Full chat in browser (requires fastapi + uvicorn)
hermes dashboard --port 9119 --host 127.0.0.1 --tui

# Don't auto-open browser
hermes dashboard --no-open

# Check/stop running instances
hermes dashboard --status
hermes dashboard --stop
```

### Prerequisites
```bash
pip install fastapi uvicorn jinja2
```

### Known Issues
- `hermes dashboard --tui` requires `hermes_cli.dashboard_auth` module
  - v0.15.2 may crash with `ModuleNotFoundError: No module named 'hermes_cli.dashboard_auth'`
  - Workaround: use `--skip-build` if the frontend is already built, or use ttyd instead
  - This module is a plugin (`plugins/dashboard_auth/nous/`). If it's missing, the plugin may not have been included in your pipx install

## ttyd Fallback (Recommended for Reliability)

[ttyd](https://github.com/tsl0922/ttyd) is a lightweight tool that exposes any CLI program in a browser via WebSocket. It handles PTY properly, so Hermes's prompt_toolkit UI works perfectly.

### Install

```bash
# Download latest x86_64 binary
curl -sS -L -o /tmp/ttyd \
  https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64
chmod +x /tmp/ttyd
sudo mv /tmp/ttyd /usr/local/bin/ttyd
```

### Start

```bash
# Basic: Hermes in browser on port 7681
ttyd -p 7681 -W hermes

# With dark theme matching Hermes TUI
ttyd -p 7681 -W \
  -t fontSize=14 \
  -t theme='{"background": "#1e1e2e", "foreground": "#cdd6f4", "cursor": "#f5e0dc"}' \
  hermes

# Bind to all interfaces (DANGEROUS — exposes your terminal on network)
ttyd -p 7681 -W -i 0.0.0.0 hermes
```

Flags:
- `-p PORT` — HTTP port (default 7681)
- `-W` — write-only (browser can't send terminal data back through GET/POST; WebSocket still works for input)
- `-t fontSize=N` — font size
- `-t theme='{...}'` — JSON theme object
- `-i 0.0.0.0` — listen on all interfaces (use with caution)

Then open **http://localhost:7681** in Chrome.

### Background Service

```bash
# Start as background process (server/daemon pattern)
ttyd -p 7681 -W hermes &

# Or using systemd (create service file)
# ~/.config/systemd/user/hermes-web.service
# [Unit]
# Description=Hermes Web Terminal
# [Service]
# ExecStart=/usr/local/bin/ttyd -p 7681 -W /home/wei/.local/bin/hermes
# Restart=always
# [Install]
# WantedBy=default.target
```

## Which to Choose

| Situation | Recommendation |
|-----------|---------------|
| Just want web UI | Try `hermes dashboard --tui` first |
| dashboard --tui crashes | Use ttyd |
| Need config/sessions UI only | Use `hermes dashboard` (no --tui) |
| Cloud server, remote access | ttyd (more reliable, less dependencies) |
| Want to build custom frontend | Use Hermes API Server (port 8642) |

## Pitfalls

- **ttyd creates a NEW Hermes session, not the current one.** Opening `http://localhost:7681` launches a fresh `hermes` process — a completely independent session with zero memory of the current conversation. Users often ask "你现在还是你吗" (are you still you?) confused about this. If they want to continue a prior session, use `/resume <session-name>` in the ttyd session. The browser session and the CLI session are different processes and cannot share context.
- **`hermes dashboard --tui` fails with `ModuleNotFoundError: No module named 'hermes_cli.dashboard_auth'`.** See `references/dashboard-tui-troubleshooting.md` for details and workarounds.
- **API Server is independent of dashboard.** Even when dashboard --tui crashes, the API Server on port 8642 (if enabled in config.yaml) keeps running and can serve custom frontends.
- **No auth on ttyd by default.** ttyd on port 7681 has no authentication — anyone who can reach the port can run Hermes commands. In production/cloud environments, either bind to 127.0.0.1 only (default), add ttyd credential auth (`-c user:pass`), or use SSH tunneling.

## Hermes API Server

Hermes has an API Server configured in `config.yaml`:

```yaml
api_server:
  enabled: true
  port: 8642
  max_concurrent_runs: 10
```

This is used by Open WebUI and custom frontends. The API Server is independent of the dashboard.
