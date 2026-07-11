"""
SampleStrategy — OKX 合约示例策略
===================================
- 时间框架: 5分钟
- 交易对: BTC/USDT:USDT, ETH/USDT:USDT (合约格式)
- 基于 RSI 超买超卖的简单策略
- 支持做空 (can_short = True)
- 仅供学习和测试，生产使用请先在 dry-run + 回测中验证

Copy to: ~/ft_userdata/user_data/strategies/SampleStrategy.py
"""

from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta


class SampleStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # --- 时间框架 ---
    timeframe = '5m'

    # --- 允许做空（合约交易核心） ---
    can_short = True

    # --- ROI 止盈设置 ---
    # 格式 { "分钟数": "最低收益率" }
    minimal_roi = {
        "60": 0.01,   # 60分钟后 1% 止盈
        "30": 0.02,   # 30分钟后 2% 止盈
        "0": 0.04     # 立即 4% 止盈
    }

    # --- 止损 ---
    stoploss = -0.05  # -5% 止损

    # --- 追踪止损（浮动止盈） ---
    trailing_stop = True
    trailing_stop_positive = 0.01       # 浮盈 1% 后激活
    trailing_stop_positive_offset = 0.02  # 浮盈 2% 开始追踪
    trailing_only_offset_is_reached = True

    # --- RSI 参数（可通过超参优化） ---
    buy_rsi = IntParameter(20, 35, default=30, space='buy')
    sell_rsi = IntParameter(65, 80, default=70, space='sell')

    # --- 指标计算 ---
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    # --- 做多信号（RSI 超卖） ---
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] < self.buy_rsi.value) & (dataframe['volume'] > 0),
            'enter_long'] = 1

        # 做空信号（RSI 超买）
        dataframe.loc[
            (dataframe['rsi'] > self.sell_rsi.value) & (dataframe['volume'] > 0),
            'enter_short'] = 1

        return dataframe

    # --- 平仓信号 ---
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] > self.sell_rsi.value),
            'exit_long'] = 1

        dataframe.loc[
            (dataframe['rsi'] < self.buy_rsi.value),
            'exit_short'] = 1

        return dataframe
