#!/bin/bash
# Gateway 通道健康检查脚本
# 每5分钟由 cron 调度，检查 Telegram gateway 是否正常运行
# 正常时静默退出（无输出 = 不通知），异常时输出报告

set -e

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
LOG_DIR="$HERMES_HOME/logs"
WATCHDOG_LOG="$LOG_DIR/gateway-watchdog.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 1. 检查 systemd 服务状态
SERVICE_STATUS=$(systemctl --user is-active hermes-gateway 2>/dev/null || echo "unknown")

if [ "$SERVICE_STATUS" != "active" ]; then
    echo "[$TIMESTAMP] ⚠️ Gateway 服务状态: $SERVICE_STATUS，尝试重启..."

    # 尝试重启
    systemctl --user restart hermes-gateway 2>/dev/null || true
    sleep 5

    # 再次检查
    RETRY_STATUS=$(systemctl --user is-active hermes-gateway 2>/dev/null || echo "unknown")
    if [ "$RETRY_STATUS" = "active" ]; then
        echo "[$TIMESTAMP] ✅ Gateway 重启成功！"
    else
        echo "[$TIMESTAMP] ❌ Gateway 重启失败，状态: $RETRY_STATUS"
        echo "[$TIMESTAMP] 📋 最近日志:"
        journalctl --user -u hermes-gateway --no-pager -n 10 2>/dev/null || echo "无法获取日志"
    fi
    exit 0
fi

# 2. 检查最近日志中是否有严重错误（只关注最近10分钟）
# 注意：WARNING 级别（如代理重连）在网络环境下属正常，不报警
if [ -f "$LOG_DIR/gateway.log" ]; then
    TEN_MIN_AGO=$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M')
    RECENT_ERRORS=$(grep -i "ERROR\|CRITICAL\|Traceback" \
        "$LOG_DIR/gateway.log" 2>/dev/null | \
        awk -v since="$TEN_MIN_AGO" '$0 ~ since || ($1" "$2) >= since' | \
        tail -5)

    if [ -n "$RECENT_ERRORS" ]; then
        echo "[$TIMESTAMP] ⚠️ Gateway 运行中，但最近10分钟内有异常:"
        echo "$RECENT_ERRORS"
        exit 0
    fi
fi

# 3. 一切正常 — 静默退出
exit 0
