#!/bin/bash
# 启用 Telegram 通道自愈 timer
set -e
systemctl --user daemon-reload
systemctl --user enable --now hermes-tg-heal.timer
sleep 1
systemctl --user list-timers hermes-tg-heal.timer --no-pager | head -4
echo "--- 手动触发一次验证 ---"
systemctl --user start hermes-tg-heal.service
systemctl --user show -p ExecMainStatus --value hermes-tg-heal.service
echo "timer 状态: $(systemctl --user is-active hermes-tg-heal.timer)"
