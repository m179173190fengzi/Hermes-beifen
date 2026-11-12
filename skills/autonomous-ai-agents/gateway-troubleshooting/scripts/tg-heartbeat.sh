#!/bin/bash
# Telegram 通道心跳告警 —— ALERT-ONLY（只发现，不重启）
#
# 为什么不能在这里重启网关：Hermes 的 cron 创建护栏 #30719 会拦掉任何含
# gateway restart/stop/kill 的 cron job（防 agent 驱动的 SIGTERM-respawn 循环）。
# 所以告警脚本只负责喊人，恢复动作由外部 shell 里的 restart 包装脚本执行：
#     bash ~/.hermes/scripts/restart_gateway.sh
#
# 部署方式（no_agent，零 token）：
#   cronjob(action=create, schedule='*/5 * * * *', no_agent=true,
#           script='tg_heartbeat.sh', deliver='telegram:<user_id>')
#   正常：无输出 → 不推送。异常：输出文本 → 推送到 TG。
#
# 覆盖的故障：服务停止 + 「进程 active 但 Telegram 适配器已死」（假活）。
# 只查 `systemctl is-active` 抓不到假活，必须扫 journald 里的致命标记。

set -u
TS=$(date '+%m-%d %H:%M')

_active() { systemctl --user is-active hermes-gateway 2>/dev/null | grep -q '^active$'; }

# ── 1. 服务挂了 ─────────────────────────────────────────
if ! _active; then
    echo "🔴 [$TS] Gateway 服务已停止 —— 现在收不到任何 TG 消息"
    echo "处理：在终端跑 bash ~/.hermes/scripts/restart_gateway.sh"
    exit 0
fi

# ── 2. 进程活着但 Telegram 适配器死了 ────────────────────
# 只认致命标记；普通代理重连 WARNING 是正常噪音，不报警。
DEAD=$(journalctl --user -u hermes-gateway --since "15 min ago" --no-pager 2>/dev/null \
    | grep -iE "could not reconnect after|Fatal .*adapter error|polling could not reconnect" \
    | tail -1)

if [ -n "$DEAD" ]; then
    echo "🔴 [$TS] Telegram 适配器掉线 —— 进程还在但收不到消息"
    echo "证据：$(echo "$DEAD" | sed 's/^.*python\[[0-9]*\]: //' | cut -c1-150)"
    echo "处理：在终端跑 bash ~/.hermes/scripts/restart_gateway.sh"
    exit 0
fi

# ── 3. 健康 → 静默 ──────────────────────────────────────
exit 0
