#!/bin/bash
# Gateway + Telegram 通道看门狗（每 5 分钟，no_agent）
# 正常：完全静默（无输出 = 不推送）
# 异常：自动重启 + 输出报告
#
# 为什么需要它：2026-10-19 00:31 Telegram 适配器在 Pool timeout 后彻底死亡，
# 日志写了 "Restarting gateway" 但进程没真重启，systemd 仍显示 active，
# bot 静默失联 9 小时。只查 systemctl is-active 抓不到这种"活着但不干活"的状态。

set -u

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
TS=$(date '+%m-%d %H:%M')
OUT=""

_service_active() { systemctl --user is-active hermes-gateway 2>/dev/null | grep -q '^active$'; }

_restart() {
    systemctl --user restart hermes-gateway 2>/dev/null || true
    sleep 8
    if ! _service_active; then
        # 兜底：kill -TERM 让 systemd 自己拉起
        PID=$(systemctl --user show -p MainPID --value hermes-gateway 2>/dev/null)
        [ -n "$PID" ] && [ "$PID" != "0" ] && kill -TERM "$PID" 2>/dev/null
        sleep 8
    fi
}

# ── 1. 服务挂了 ────────────────────────────────────────────
if ! _service_active; then
    OUT="[$TS] ⚠️ Gateway 服务不在运行，已尝试重启"
    _restart
    if _service_active; then
        OUT="$OUT → ✅ 成功"
    else
        OUT="$OUT → ❌ 失败，需手动处理：systemctl --user restart hermes-gateway"
    fi
    echo "$OUT"
    exit 0
fi

# ── 2. 进程活着但 Telegram 适配器已死（核心场景）──────────
# 只认"致命"标记，普通代理重连 WARNING 不报警
DEAD_MARK=$(journalctl --user -u hermes-gateway --since "20 min ago" --no-pager 2>/dev/null \
    | grep -iE "could not reconnect after|Fatal .*adapter error|polling could not reconnect" \
    | tail -2)

if [ -n "$DEAD_MARK" ]; then
    OUT="[$TS] ⚠️ Telegram 适配器掉线（进程仍在，但收不到消息），已自动重启"
    _restart
    if _service_active; then
        OUT="$OUT → ✅ 已重启，PID $(systemctl --user show -p MainPID --value hermes-gateway)"
    else
        OUT="$OUT → ❌ 重启失败"
    fi
    echo "$OUT"
    echo "证据: $(echo "$DEAD_MARK" | tail -1 | cut -c1-160)"
    exit 0
fi

# ── 3. 一切正常 ────────────────────────────────────────────
exit 0
