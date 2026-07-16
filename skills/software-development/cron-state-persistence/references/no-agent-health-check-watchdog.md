# no_agent Health Check Watchdog Pattern

A recurring no_agent cron job that checks an external API/service health and alerts only on failure. Silent when healthy.

## When to Use

- Monitor API keys and tokens for expiration
- Check if an external service is reachable
- Periodic connectivity/health checks (Telegram, GMGN, OKX, etc.)
- Any "keep testing until it breaks" scenario where the script is the entire brains of the job

## Pattern

```
cron no_agent=true script=health_check.sh schedule="0 10,16,22 * * *"
            │                                    │
            ▼                                    ▼
     Script runs, no LLM              3x daily check
     tokens consumed
            │
            ▼
     stdout → delivered to user
     (silent on exit 0, alert on exit 1)
```

## Script Contract

| Exit | stdout behavior | User sees |
|------|----------------|-----------|
| `0` | empty (or anything) | **Silent** — nothing delivered |
| `1` | alert message | Alert delivered immediately |

## Telegram Bot Token Example

This is the canonical use case — TG tokens can be revoked by BotFather with no warning, which silently kills the gateway:

```bash
#!/bin/bash
# tg_token_check.sh
ENV_FILE="$HOME/.hermes/.env"
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" | head -1 | cut -d= -f2-)

[ -z "$TOKEN" ] && { echo "⚠️ TG token not found in .env"; exit 1; }

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "https://api.telegram.org/bot${TOKEN}/getMe")

if [ "$HTTP_CODE" = "200" ]; then
  exit 0                         # healthy — silent
elif [ "$HTTP_CODE" = "401" ]; then
  echo "🚨 TG Bot Token expired or revoked! HTTP 401"
  exit 1
fi
exit 0                           # transient network error — stay silent
```

Cron setup:
```bash
cronjob action=create \
  name='TG Token health check' \
  schedule='0 10,16,22 * * *' \
  script=tg_token_check.sh \
  no_agent=true
```

## GMGN API Key Example

Same pattern for GMGN API key health:

```bash
#!/bin/bash
API_KEY=$(grep '^GMGN_API_KEY=*** ~/.hermes/.env | head -1 | cut -d= -f2-)
[ -z "$API_KEY" ] && { echo "⚠️ GMGN API key not found"; exit 1; }

RESULT=$(gmgn-cli token info --chain sol \
  --address So11111111111111111111111111111111111111112 2>&1)

if echo "$RESULT" | grep -q "401\|AUTH_SIGNATURE_INVALID\|Bad credentials"; then
  echo "🚨 GMGN API key invalid! Needs re-binding"
  exit 1
fi
exit 0
```

## When NOT to Use no_agent

| Scenario | Use agent-driven instead |
|----------|------------------------|
| Need to compare with previous results | `cron-state-persistence` + agent |
| Need to format/interpret/summarize data | Agent prompt with `enabled_toolsets` |
| Need to decide whether to alert based on context | Agent prompt |
| Script output is raw data that needs LLM interpretation | Agent prompt |

## Pitfalls

- **Script must be in `~/.hermes/scripts/`** — cron only accepts the filename, not absolute/relative paths
- **Non-zero exit = alert** — don't exit 1 for transient errors unless you want false alarms. Prefer `exit 0` on transient failures (another check soon will catch the real problem)
- **First run tests the cron setup** — always run the script manually once to verify: `bash ~/.hermes/scripts/tg_token_check.sh; echo $?`
