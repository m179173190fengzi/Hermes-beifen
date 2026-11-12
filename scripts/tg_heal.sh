#!/bin/bash
# Telegram 通道自愈（systemd timer 每 5 分钟调用；不依赖 gateway 自身）
#
# 背景：Hermes 的 telegram 适配器掉线后会打 "Restarting gateway"，但进程并不退出，
# systemd Restart=always 因此永远不触发 → bot 静默失联数小时。
#
# 2026-11-09 修正两个问题：
#   1) 原来用固定 "15 分钟窗口" 判断故障 → 同一条 fatal 日志会在之后 3 次巡检里
#      反复命中，每 5 分钟重启一次网关（09:14 / 09:20 / 09:26 三连重启就是这么来的）。
#      改为：只检查「上次自愈之后」的日志，并加 5 分钟冷却。
#   2) 成功自愈不再推送 Telegram（用户要求后台静默），只写本地日志。
#      失败仍会推送 🔴（否则 bot 挂了没人知道）。

set -u

ENVF="$HOME/.hermes/.env"
TOKEN=$(grep -m1 '^TELEGRAM_BOT_TOKEN=' "$ENVF" 2>/dev/null | cut -d= -f2- | tr -d '"'"'"' \r')
CHAT="${TG_ALERT_CHAT:-7706985861}"
PROXY="http://127.0.0.1:7890"
TS=$(date '+%m-%d %H:%M')

STATE_DIR="$HOME/.hermes/cron/state"
mkdir -p "$STATE_DIR"
STATE="$STATE_DIR/tg_heal.last"
LOG="$HOME/.hermes/logs/tg_heal.log"

NOW=$(date +%s)
LAST=$(cat "$STATE" 2>/dev/null || echo 0)
case "$LAST" in ''|*[!0-9]*) LAST=0 ;; esac
[ "$LAST" -eq 0 ] && LAST=$((NOW - 600))   # 首次运行只看最近 10 分钟

log() {
    printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG"
    # 只保留最近 200 行
    tail -n 200 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
}

send() {
    [ -z "${TOKEN:-}" ] && return 0
    curl -s --max-time 25 -x "$PROXY" \
        "https://api.telegram.org/bot${TOKEN}/sendMessage" \
        -d "chat_id=${CHAT}" -d "disable_web_page_preview=true" \
        --data-urlencode "text=$1" >/dev/null 2>&1
}

active() { systemctl --user is-active hermes-gateway 2>/dev/null | grep -q '^active$'; }

restart_gw() {
    systemctl --user restart hermes-gateway 2>/dev/null || true
    sleep 10
    if ! active; then
        PID=$(systemctl --user show -p MainPID --value hermes-gateway 2>/dev/null)
        [ -n "${PID:-}" ] && [ "$PID" != "0" ] && kill -TERM "$PID" 2>/dev/null
        sleep 10
    fi
    echo "$(date +%s)" > "$STATE"
}

# ── 0. 冷却：5 分钟内刚自愈过就跳过 ──────────────────────
if [ $((NOW - LAST)) -lt 300 ]; then
    exit 0
fi

# ── 1. 服务停止 ─────────────────────────────────────────
if ! active; then
    restart_gw
    if active; then
        log "服务停止 → 已重启恢复（PID $(systemctl --user show -p MainPID --value hermes-gateway)）"
    else
        log "服务停止 → 重启失败"
        send "🔴 [$TS] Gateway 服务停止且自动重启失败，需手动处理"
    fi
    exit 0
fi

# ── 2. 进程活着但 telegram 适配器死了（只看上次自愈之后）──
DEAD=$(journalctl --user -u hermes-gateway --since "@$LAST" --no-pager 2>/dev/null \
    | grep -iE "could not reconnect after|Fatal .*adapter error|polling could not reconnect" \
    | tail -1)

if [ -n "${DEAD:-}" ]; then
    restart_gw
    if active; then
        log "适配器掉线 → 已重启恢复 | $(echo "$DEAD" | sed 's/^.*python\[[0-9]*\]: //' | cut -c1-160)"
    else
        log "适配器掉线 → 重启失败"
        send "🔴 [$TS] Telegram 适配器掉线，自动重启失败，需手动处理"
    fi
    exit 0
fi

# ── 3. 健康 → 静默（推进水位线，避免下次重复扫描旧日志）──
echo "$NOW" > "$STATE"
exit 0
