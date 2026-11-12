#!/bin/bash
# 回滚到 pipx 0.19.0（若 v0.23.0 起不来）
set -e
cp ~/.hermes/scripts/hermes-gateway.service.pipx-0.19.0 ~/.config/systemd/user/hermes-gateway.service
ln -sf /home/wei/.local/share/pipx/venvs/hermes-agent/bin/hermes ~/.local/bin/hermes
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
sleep 3
systemctl --user is-active hermes-gateway
hermes --version | head -2
