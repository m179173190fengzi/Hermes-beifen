# Telegram Missing Extras — Example Transcript

## Scenario

Hermes gateway is running, Telegram is configured in `config.yaml` and `.env` with a valid bot token and allowed users, but the bot does not respond to messages.

## `hermes gateway status` Output

```
● hermes-gateway.service - Hermes Agent Gateway - Messaging Platform Integration
     Loaded: loaded (~/.config/systemd/user/hermes-gateway.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-06-24 21:23:01 CST; 24min ago
   Main PID: 14963 (hermes)
```

Gateway appears healthy. The `running` status is misleading — it only means the process is alive, not that any platform adapter loaded.

## Gateway Log (`~/.hermes/logs/gateway.log`)

```
WARNING gateway.platform_registry: Platform 'Telegram' requirements not met (pip install 'hermes-agent[telegram]')
ERROR gateway.run: Platform 'telegram' is registered but adapter creation failed (check dependencies and config)
WARNING gateway.run: No adapter available for telegram
WARNING gateway.run: No adapter could be created for any of the 1 configured platform(s).
  Check that required dependencies are installed and credentials are set.
  Gateway will continue for cron job execution.
```

## Config Check (`hermes config`)

Shows `Telegram: configured` under "Messaging Platforms" — this only confirms the YAML section exists, not that the adapter loaded.

## `.env` Values

```
TELEGRAM_BOT_TOKEN=887530...ghmQ
TELEGRAM_ALLOWED_USERS=7706985861
TELEGRAM_HOME_CHANNEL=7706985861
```

Credentials are present and valid. The issue is purely the missing Python package.

## Fix

```bash
pipx install --force 'hermes-agent[telegram]'
systemctl --user restart hermes-gateway
```

## Lesson

**Never trust `configured` status alone.** A platform can be "configured" in the YAML sense while having zero functional adapters. The key diagnostic step is always: grep gateway.log for "adapter", "requirements", "failed".
