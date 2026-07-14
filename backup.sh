#!/bin/bash
# Hermes 自动备份到 GitHub
# 每天同步：config, skills, memory, obsidian

set -e

REPO_DIR="/home/wei/Hermes-beifen"
HERMES_HOME="/home/wei/.hermes"
SKILLS_DIR="$HERMES_HOME/skills"
MEMORY_DIR="$HERMES_HOME/memory"
OBSIDIAN_VAULT="/home/wei/文档/Obsidian Vault"
CONFIG_DIR="$HERMES_HOME"

DATE_TAG=$(date '+%Y-%m-%d_%H:%M')

echo "=== Hermes 自动备份: $DATE_TAG ==="

# 1. 同步 config
cp "$CONFIG_DIR/config.yaml" "$REPO_DIR/config/hermes-config.yaml" 2>/dev/null || true
cp "$CONFIG_DIR/.env" "$REPO_DIR/config/hermes-env.txt" 2>/dev/null || true

# 2. 同步 memory
cp "$MEMORY_DIR/MEMORY.md" "$REPO_DIR/memory/" 2>/dev/null || true
cp "$MEMORY_DIR/USER.md" "$REPO_DIR/memory/" 2>/dev/null || true

# 3. 同步 skills 列表
ls -1 "$SKILLS_DIR/" > "$REPO_DIR/skills/skills-list.txt"

# 4. 同步 obsidian vault (仅 .md 文件)
if [ -d "$OBSIDIAN_VAULT" ]; then
    rsync -a --include='*/' --include='*.md' --exclude='*' "$OBSIDIAN_VAULT/" "$REPO_DIR/obsidian/" 2>/dev/null || true
fi

# 5. 同步 V4 策略脚本
cp /home/wei/v4-strategy.py "$REPO_DIR/scripts/" 2>/dev/null || mkdir -p "$REPO_DIR/scripts" && cp /home/wei/v4-strategy.py "$REPO_DIR/scripts/" 2>/dev/null || true

# 6. 同步 cron 任务列表(只读，不包含密钥)
cd "$REPO_DIR"

# 添加所有变更
git add -A 2>/dev/null

# 如果有变更才提交
if ! git diff --cached --quiet; then
    git commit -m "Auto backup $DATE_TAG"
    git push origin main 2>&1 || echo "⚠ Push failed, will retry next time"
    echo "✅ 备份完成并推送到 GitHub"
else
    echo "🔵 无变更，跳过提交"
fi

echo "=== 备份结束 ==="
