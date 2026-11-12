#!/bin/bash
# TG 通道心跳告警（每 5 分钟，no_agent，静默模式）
# 正常：无输出（不推送）。异常：输出文本 → 推送 Telegram。
# 只检测不动作 —— 重启动作由人/agent 在网关外执行。

set -u
TS=$(date '+%m-%d %H:%M')

_active() { systemctl --user is-active hermes-gateway 2>/dev/null | grep -q '^active$'; }

if ! _active; then
    echo "🔴 [$TS] Gateway 服务已停止 —— 现在收不到任何 TG 消息"
    echo "处理：在终端跑 bash ~/.hermes/scripts/restart_gateway.sh"
    exit 0
fi

DEAD=$(journalctl --user -u hermes-gateway --since "15 min ago" --no-pager 2>/dev/null \
    | grep -iE "could not reconnect after|Fatal .*adapter error|polling could not reconnect" \
    | tail -1)

if [ -n "$DEAD" ]; then
    echo "🔴 [$TS] Telegram 适配器掉线 —— 进程还在但收不到消息"
    echo "证据：$(echo "$DEAD" | sed 's/^.*python\[[0-9]*\]: //' | cut -c1-150)"
    echo "处理：在终端跑 bash ~/.hermes/scripts/restart_gateway.sh"
    exit 0
fi

exit 0
