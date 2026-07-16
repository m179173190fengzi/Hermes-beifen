#!/bin/bash
# TG Bot Token 有效性检查
# 每天检查一次，token失效时推送告警

ENV_FILE="$HOME/.hermes/.env"
VAL=$(grep '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2-)

if [ -z "$VAL" ]; then
  echo "⚠️ TG 告警：未找到 TELEGRAM_BOT_TOKEN 环境变量"
  exit 1
fi

RESULT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "https://api.telegram.org/bot${VAL}/getMe" 2>&1)

if [ "$RESULT" = "200" ]; then
  exit 0
elif [ "$RESULT" = "401" ]; then
  echo "🚨 TG Bot Token 已失效！HTTP 401 Unauthorized"
  exit 1
fi
exit 0
