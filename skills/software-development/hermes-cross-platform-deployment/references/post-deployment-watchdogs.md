# Post-Deployment Infrastructure Watchdogs

## Why Watchdogs

Hermes infrastructure can fail silently — no error log, no crash, just silence:
- TG bot token revoked via @BotFather → gateway hangs on connect forever
- API key quota exhausted → model responses fail, user sees nothing
- Gateway process dies → all messaging channels dead
- Cron job context overflow → jobs report `last_status: error` with empty output

Watchdogs provide proactive alerts so the user knows before they try to send a message.

## no_agent Watchdog Pattern

Recommnded for most infra checks:

```bash
#!/bin/bash
# 1. Check the thing
if check_passed; then
  exit 0    # SILENT — no delivery
else
  echo "🚨 Alert: ..."
  exit 1    # Non-zero → message delivered
fi
```

### Cron setup
```bash
cronjob action=create \
  name='Descriptive Name' \
  schedule='0 10,16,22 * * *' \
  script='script_name.sh' \
  no_agent=true
```

### Rules
- **Exit 0 + no stdout** = [SILENT] — user never sees it
- **Non-zero + stdout** = alert delivered to user
- **Transient network failures** → exit 0 (don't false-alarm)
- Only alert on **definitive failures** (HTTP 401, process dead, disk full)

## TG Token Check — Reference Implementation

Script: `~/.hermes/scripts/tg_token_check.sh`

Checks `https://api.telegram.org/bot<TOKEN>/getMe`:
- HTTP 200 → token valid → silent
- HTTP 401 → token dead → alert
- Any other → transient issue → silent

## Gateway Health Check

```bash
#!/bin/bash
STATE=$(systemctl --user is-active hermes-gateway 2>/dev/null)
if [ "$STATE" = "active" ]; then
  exit 0
else
  echo "🚨 Hermes Gateway is $STATE (expected: active)"
  exit 1
fi
```

## Cron Job Health Check

Use `cronjob action=list` or check the session DB for recent errors.

## Pitfalls

- **Do NOT check too frequently** — every 6h is fine for token validity, every 1h for gateway
- **Do NOT set `notify_on_complete` on watchdogs** — no_agent scripts already handle their own alert logic
- **Script must be in `~/.hermes/scripts/`** — cron references it by filename only
- **First run produces no state** — that's fine for watchdogs (no state needed)
- **Avoid watchdogs for transient conditions** — only monitor things that are "stuck dead" until fixed
