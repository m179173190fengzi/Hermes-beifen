# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
V4 交易策略 — 最终版

均线: SMA20/60/120 + EMA20/60/120（固定不改）
看大做小: 同一K线上6条均线排列(大) + K线流畅走势(小)

https://github.com/NousResearch/hermes-agent
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union
from functools import reduce

from freqtrade.strategy import (
    IStrategy, Trade, Order, PairLocks, informative,
    BooleanParameter, CategoricalParameter, DecimalParameter,
    IntParameter, RealParameter,
    timeframe_to_minutes, timeframe_to_next_date, timeframe_to_prev_date,
    merge_informative_pair, stoploss_from_absolute, stoploss_from_open,
)
import talib.abstract as ta
from technical import qtpylib


class V4Strategy(IStrategy):
    """
    V4 交易策略 — 看大做小

    均线(固定): SMA20/60/120 + EMA20/60/120
    看大: 6条均线是否空头/多头排列
    做小: K线流畅下跌/上涨 + 不反弹突破
    """
    INTERFACE_VERSION = 3
    can_short = True
    minimal_roi = {"0": 100.0}
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    stoploss = -0.02
    leverage = IntParameter(low=1, high=10, default=3, space="buy")
    bear_market_mode = BooleanParameter(default=True, space="buy")
    smooth_bars = IntParameter(low=2, high=5, default=3, space="buy")
    startup_candle_count = 200

    order_types = {"entry": "limit", "exit": "limit",
                   "stoploss": "market", "stoploss_on_exchange": False}
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "sma20": {"color": "#FF6B6B"}, "sma60": {"color": "#FFA500"},
            "sma120": {"color": "#FFD700"}, "ema20": {"color": "#4ECDC4"},
            "ema60": {"color": "#45B7D1"}, "ema120": {"color": "#96CEB4"},
        },
    }

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe, metadata):
        # 6条均线
        dataframe["sma20"] = ta.SMA(dataframe, 20)
        dataframe["sma60"] = ta.SMA(dataframe, 60)
        dataframe["sma120"] = ta.SMA(dataframe, 120)
        dataframe["ema20"] = ta.EMA(dataframe, 20)
        dataframe["ema60"] = ta.EMA(dataframe, 60)
        dataframe["ema120"] = ta.EMA(dataframe, 120)

        ma = ["sma20","sma60","sma120","ema20","ema60","ema120"]

        # 看大：排列
        dataframe["bearish_order"] = (
            (dataframe["sma20"]<dataframe["sma60"]) & (dataframe["sma60"]<dataframe["sma120"])
            & (dataframe["ema20"]<dataframe["ema60"]) & (dataframe["ema60"]<dataframe["ema120"])
            & (dataframe["ema20"]<dataframe["sma20"])
        )
        dataframe["bullish_order"] = (
            (dataframe["sma20"]>dataframe["sma60"]) & (dataframe["sma60"]>dataframe["sma120"])
            & (dataframe["ema20"]>dataframe["ema60"]) & (dataframe["ema60"]>dataframe["ema120"])
            & (dataframe["ema20"]>dataframe["sma20"])
        )

        # 看大：K线在均线下方/上方
        below = above = True
        for c in ma:
            below = below & (dataframe["close"]<dataframe[c])
            above = above & (dataframe["close"]>dataframe[c])
        dataframe["price_below"] = below
        dataframe["price_above"] = above

        # 做小：流畅走势
        s = self.smooth_bars.value
        dataframe["lower"] = dataframe["close"] < dataframe["close"].shift(1)
        dataframe["smooth_d"] = dataframe["lower"].rolling(s).min() >= 1
        dataframe["higher"] = dataframe["close"] > dataframe["close"].shift(1)
        dataframe["smooth_u"] = dataframe["higher"].rolling(s).min() >= 1

        # 做小：不反弹/不破位
        rh = dataframe["high"].rolling(2).max()
        dataframe["no_bounce"] = (rh < dataframe["sma20"]) & (rh < dataframe["ema20"])
        rl = dataframe["low"].rolling(2).min()
        dataframe["no_break"] = (rl > dataframe["sma20"]) & (rl > dataframe["ema20"])

        # 综合信号
        dataframe["v4_short"] = (
            dataframe["bearish_order"] & dataframe["price_below"]
            & dataframe["smooth_d"] & dataframe["no_bounce"]
        )
        dataframe["v4_long"] = (
            dataframe["bullish_order"] & dataframe["price_above"]
            & dataframe["smooth_u"] & dataframe["no_break"]
        )
        if self.bear_market_mode.value:
            dataframe["v4_long"] = False

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        dataframe.loc[dataframe["v4_short"]&(dataframe["volume"]>0), ["enter_short","enter_tag"]] = (1,"v4空")
        dataframe.loc[dataframe["v4_long"]&(dataframe["volume"]>0), ["enter_long","enter_tag"]] = (1,"v4多")
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        dataframe.loc[
            qtpylib.crossed_above(dataframe["close"], dataframe["sma20"]),
            ["exit_short","exit_tag"]] = (1,"exit")
        dataframe.loc[
            qtpylib.crossed_below(dataframe["close"], dataframe["sma20"]),
            ["exit_long","exit_tag"]] = (1,"exit")
        return dataframe

    def custom_leverage(self, pair, current_time, current_rate,
                       proposed_leverage, max_leverage, side, **kwargs):
        return self.leverage.value
