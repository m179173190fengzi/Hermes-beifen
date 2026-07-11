#!/bin/bash
# FreqTrade 便捷启动脚本
# 使用: ./freqtrade.sh <命令> [参数]
# 示例:
#   ./freqtrade.sh trade                    # 开始交易
#   ./freqtrade.sh backtesting              # 回测
#   ./freqtrade.sh list-markets             # 查看交易对
#   ./freqtrade.sh download-data -t 5m      # 下载数据
#
# Adapt these paths to your setup:
FREQTRADE_DIR="$HOME/ft_userdata/freqtrade"
CONFIG="$HOME/ft_userdata/user_data/config-okx.json"
USERDIR="$HOME/ft_userdata/user_data"

# Export proxy if needed (GFW workaround)
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# Note: -c must come AFTER the subcommand in FreqTrade 2026.x
CMD="$1"
shift
exec "$FREQTRADE_DIR/.venv/bin/freqtrade" "$CMD" \
    -c "$CONFIG" \
    --userdir "$USERDIR" \
    "$@"
