# V4MtfStrategy — 同图看大做小完整代码
# 文件位置: ~/ft_userdata/user_data/strategies/v4_short.py
# 类名: V4MtfStrategy

"""
V4 多时间框架 — 同图看大做小

核心: 
在同一张K线上, 用两套均线实现"看大做小"
- 长均线(EMA60): 判断大方向（均线排列压制/支撑）
- 短均线(5/10/20): 精确入场（流畅下跌/上涨）

示例:
-i 1m → 短均线5/10/20, 长均线60看方向
-i 5m → 短均线5/10/20, 长均线60看方向  
-i 15m → 短均线10/20/40, 长均线60看方向

reproduce流程:
1. cp此文件到 ~/ft_userdata/user_data/strategies/v4_short.py
2. cd ~/ft_userdata && source freqtrade/.venv/bin/activate
3. freqtrade backtesting -c user_data/config-okx.json --strategy V4MtfStrategy -i 15m --timerange 20260620-
"""

from functools import reduce
from pandas import DataFrame
from freqtrade.strategy import (
    IStrategy, BooleanParameter, IntParameter,
    merge_informative_pair,
)
import talib.abstract as ta
from technical import qtpylib


class V4MtfStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = True
    minimal_roi = {"0": 100.0}
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    stoploss = -0.015
    leverage = IntParameter(low=1, high=5, default=3, space="buy")
    bear_market_mode = BooleanParameter(default=False, space="buy")

    ma_s = IntParameter(low=3, high=8, default=5, space="buy")
    ma_m = IntParameter(low=8, high=15, default=10, space="buy")
    ma_l = IntParameter(low=15, high=30, default=20, space="buy")
    ma_trend = IntParameter(low=40, high=120, default=60, space="buy")
    smooth_bars = IntParameter(low=2, high=4, default=3, space="buy")
    no_bounce_bars = IntParameter(low=1, high=3, default=2, space="buy")
    startup_candle_count: int = 200

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe, metadata):
        s, m, l = self.ma_s.value, self.ma_m.value, self.ma_l.value
        trend = self.ma_trend.value

        dataframe["ma_s"] = ta.SMA(dataframe, timeperiod=s)
        dataframe["ma_m"] = ta.SMA(dataframe, timeperiod=m)
        dataframe["ma_l"] = ta.SMA(dataframe, timeperiod=l)
        dataframe["ma_t"] = ta.EMA(dataframe, timeperiod=trend)

        # 大方向（看大做小里的"大"）
        dataframe["bias_short"] = dataframe["ma_t"] > dataframe["close"]
        dataframe["bias_long"] = dataframe["ma_t"] < dataframe["close"]

        # 小入场（看大做小里的"小"）
        dataframe["resist"] = (
            (dataframe["ma_s"] > dataframe["close"])
            & (dataframe["ma_m"] > dataframe["close"])
            & (dataframe["ma_l"] > dataframe["close"])
        )
        dataframe["support"] = (
            (dataframe["ma_s"] < dataframe["close"])
            & (dataframe["ma_m"] < dataframe["close"])
            & (dataframe["ma_l"] < dataframe["close"])
        )

        smooth = self.smooth_bars.value
        dataframe["lower_low"] = dataframe["close"] < dataframe["close"].shift(1)
        dataframe["smooth_down"] = dataframe["lower_low"].rolling(smooth).min() >= 1
        dataframe["higher_high"] = dataframe["close"] > dataframe["close"].shift(1)
        dataframe["smooth_up"] = dataframe["higher_high"].rolling(smooth).min() >= 1

        nb = self.no_bounce_bars.value
        rh = dataframe["high"].rolling(nb).max()
        rl = dataframe["low"].rolling(nb).min()
        dataframe["no_bounce"] = rh < dataframe["ma_s"]
        dataframe["no_break"] = rl > dataframe["ma_s"]

        # 信号列（用v4_short/v4_long避免bool列冲突）
        dataframe["v4_short"] = (
            dataframe["bias_short"] & dataframe["smooth_down"]
            & dataframe["resist"] & dataframe["no_bounce"]
        )
        dataframe["v4_long"] = (
            dataframe["bias_long"] & dataframe["smooth_up"]
            & dataframe["support"] & dataframe["no_break"]
        )
        if self.bear_market_mode.value:
            dataframe["v4_long"] = False

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe.loc[
            dataframe["v4_short"] & (dataframe["volume"] > 0),
            ["enter_short", "enter_tag"],
        ] = (1, "v4空")
        dataframe.loc[
            dataframe["v4_long"] & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "v4多")
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        s = self.ma_s.value
        dataframe.loc[
            qtpylib.crossed_above(dataframe["close"], dataframe["ma_s"]),
            ["exit_short", "exit_tag"],
        ] = (1, "exit")
        dataframe.loc[
            qtpylib.crossed_below(dataframe["close"], dataframe["ma_s"]),
            ["exit_long", "exit_tag"],
        ] = (1, "exit")
        return dataframe

    def custom_leverage(self, pair, current_time, current_rate,
                       proposed_leverage, max_leverage, side, **kwargs):
        return self.leverage.value
