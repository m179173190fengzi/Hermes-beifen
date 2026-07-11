#!/bin/bash
# FreqTrade 便捷启动脚本 — 生成后根据实际路径修改
# 使用: ./freqtrade.sh <子命令> [参数]
#
# 示例:
#   ./freqtrade.sh trade                    # 开始交易
#   ./freqtrade.sh backtesting              # 回测
#   ./freqtrade.sh list-markets             # 查看交易对
#   ./freqtrade.sh webserver                # Web UI

DIR="$(cd "$(dirname "$0")" && pwd)"
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# -c 和 --userdir 放在子命令之后 (FreqTrade 2026.x 语法)
CMD="$1"
shift

exec "$DIR/freqtrade/.venv/bin/freqtrade" "$CMD" \
    -c "$DIR/user_data/config-okx.json" \
    --userdir "$DIR/user_data" \
    "$@"
