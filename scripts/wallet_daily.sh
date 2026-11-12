#!/bin/bash
# 每日钱包行为审计：只报最近24小时的交易与违规动作；无交易则静默
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
exec python3 /home/wei/.hermes/scripts/wallet_audit.py \
  --wallet 0x7dc68c2884fad2e09085c6d23c2f56a9f1304d54 --today
