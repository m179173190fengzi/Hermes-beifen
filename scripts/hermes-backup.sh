#!/bin/bash
# Hermes 自动备份到 GitHub
# 每天同步：config, skills, memory, obsidian
#
# 2026-10-16 改造：不再依赖调度器投递（它没有重试，网络抖动就丢消息）。
#   本脚本自己把摘要推送到 Telegram，git push 与 TG 发送都带重试。
#   成功时 stdout 为空（调度器静默）；只有 TG 彻底发送失败才打印一行，
#   让调度器再试一次（等于双保险）。

set -uo pipefail

REPO_DIR="/home/wei/Hermes-beifen"
HERMES_HOME="/home/wei/.hermes"
SKILLS_DIR="$HERMES_HOME/skills"
MEMORY_DIR="$HERMES_HOME/memory"
OBSIDIAN_VAULT="/home/wei/文档/Obsidian Vault"
CONFIG_DIR="$HERMES_HOME"
PROXY="http://127.0.0.1:7890"

DATE_TAG=$(date '+%Y-%m-%d_%H:%M')
LOG=""
log() { LOG="${LOG}$*"$'\n'; }

log "=== Hermes 自动备份: $DATE_TAG ==="

# 1. 同步 config（⚠️ 绝不上传 .env！只导出 key 名，值为空）
cp "$CONFIG_DIR/config.yaml" "$REPO_DIR/config/hermes-config.yaml" 2>/dev/null || true
if [ -f "$CONFIG_DIR/.env" ]; then
    grep -oE '^[A-Z_0-9]+=' "$CONFIG_DIR/.env" 2>/dev/null | sed 's/=$/=<REDACTED>/' \
        > "$REPO_DIR/config/env-keys-only.txt" || true
fi
rm -f "$REPO_DIR/config/hermes-env.txt" 2>/dev/null || true

# 2. 同步 memory（⚠️ 真实目录是 memories/，memory/ 是 7 月的旧目录）
MEM_SRC="$HERMES_HOME/memories"
[ -f "$MEM_SRC/MEMORY.md" ] || MEM_SRC="$MEMORY_DIR"
cp "$MEM_SRC/MEMORY.md" "$REPO_DIR/memory/" 2>/dev/null || true
cp "$MEM_SRC/USER.md" "$REPO_DIR/memory/" 2>/dev/null || true

# 2b. 同步 cron 任务定义（打狗日报/监控的定义都在这里，很重要）
cp "$CONFIG_DIR/cron/jobs.json" "$REPO_DIR/config/cron-jobs.json" 2>/dev/null || true

# 3. 同步 skills 列表
ls -1 "$SKILLS_DIR/" > "$REPO_DIR/skills/skills-list.txt" 2>/dev/null || true

# 4. 同步 obsidian vault (仅 .md 文件)
if [ -d "$OBSIDIAN_VAULT" ]; then
    rsync -a --include='*/' --include='*.md' --exclude='*' "$OBSIDIAN_VAULT/" "$REPO_DIR/obsidian/" 2>/dev/null || true
fi

# 5. 同步 V4 策略脚本
mkdir -p "$REPO_DIR/scripts"
cp /home/wei/v4-strategy.py "$REPO_DIR/scripts/" 2>/dev/null || true

# 6. 提交并推送（带重试）
cd "$REPO_DIR" || exit 1
git add -A 2>/dev/null

if git diff --cached --quiet; then
    log "🔵 无变更，跳过提交"
else
    git commit -q -m "Auto backup $DATE_TAG" 2>/dev/null || true
    PUSH_OK=0
    for i in 1 2 3 4; do
        if git push origin main >/tmp/hermes_backup_push.log 2>&1; then
            PUSH_OK=1
            break
        fi
        sleep $((i * 20))
    done
    if [ "$PUSH_OK" = "1" ]; then
        log "✅ 备份完成并推送到 GitHub"
    else
        log "⚠️ git push 重试 4 次仍失败（下次运行会自动重试，数据已提交到本地仓库）"
        log "   最后错误: $(tail -1 /tmp/hermes_backup_push.log 2>/dev/null | cut -c1-120)"
    fi
fi

# 7. 自己发送到 Telegram（带重试）
TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$HERMES_HOME/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')
CHAT=$(grep -E '^TELEGRAM_HOME_CHANNEL=' "$HERMES_HOME/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d ' ')

SENT=0
if [ -n "$TOKEN" ] && [ -n "$CHAT" ]; then
    for i in 1 2 3 4 5; do
        CODE=$(HTTPS_PROXY="$PROXY" HTTP_PROXY="$PROXY" curl -s --max-time 30 \
            -o /dev/null -w "%{http_code}" \
            -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
            -d "chat_id=${CHAT}" \
            --data-urlencode "text=${LOG}")
        if [ "$CODE" = "200" ]; then
            SENT=1
            break
        fi
        sleep $((i * 15))
    done
fi

# 8. 收尾：成功静默；彻底失败则打印一行，让调度器兜底再试
if [ "$SENT" != "1" ]; then
    echo "⚠️ 备份执行完毕，但 Telegram 推送重试 5 次失败（消息见 job 日志）"
fi
exit 0
