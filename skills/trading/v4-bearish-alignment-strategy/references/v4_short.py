# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
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


class V4ShortStrategy(IStrategy):
    """
    V4 短周期版 — 专为1m/3m/5m/15m设计

    均线用短周期自适应:
    - 1m: SMA5 < SMA10 < SMA20  (5/10/20分钟依次排列)
    - 3m: SMA5 < SMA10 < SMA20  (15/30/60分钟)
    - 5m: SMA10 < SMA20 < SMA40 (50/100/200分钟)
    - 15m: SMA20 < SMA60 < SMA120 (标准V4)

    核心: 依次排列 + 均线压制 + 流畅下跌
    """

    INTERFACE_VERSION = 3
    can_short: bool = True
    minimal_roi = {"0": 100.0}
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # 三根均线参数
    ma_short = IntParameter(low=3, high=10, default=5, space="buy")
    ma_mid = IntParameter(low=8, high=20, default=10, space="buy")
    ma_long = IntParameter(low=15, high=40, default=20, space="buy")

    smooth_bars = IntParameter(low=2, high=5, default=3, space="buy")
    no_bounce_bars = IntParameter(low=1, high=3, default=2, space="buy")
    bear_market_mode = BooleanParameter(default=True, space="buy")
    leverage = IntParameter(low=1, high=5, default=3, space="buy")
    stoploss = -0.015
    startup_candle_count: int = 50

    order_types = {"entry": "limit", "exit": "limit",
                   "stoploss": "market", "stoploss_on_exchange": False}
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, "1d") for pair in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        s = self.ma_short.value
        m = self.ma_mid.value
        l = self.ma_long.value

        dataframe["ma_s"] = ta.SMA(dataframe, timeperiod=s)
        dataframe["ma_m"] = ta.SMA(dataframe, timeperiod=m)
        dataframe["ma_l"] = ta.SMA(dataframe, timeperiod=l)

        # 条件1: 依次排列 (短 < 中 < 长)
        dataframe["ordered"] = (
            (dataframe["ma_s"] < dataframe["ma_m"])
            & (dataframe["ma_m"] < dataframe["ma_l"])
        )

        # 条件2: 均线在K线上方（压制）
        dataframe["ma_above"] = (
            (dataframe["ma_s"] > dataframe["close"])
            & (dataframe["ma_m"] > dataframe["close"])
            & (dataframe["ma_l"] > dataframe["close"])
        )

        # 条件3: 均线斜率全部向下
        dataframe["slope_s"] = dataframe["ma_s"] < dataframe["ma_s"].shift(1)
        dataframe["slope_m"] = dataframe["ma_m"] < dataframe["ma_m"].shift(1)
        dataframe["slope_l"] = dataframe["ma_l"] < dataframe["ma_l"].shift(1)
        dataframe["all_slope_down"] = (
            dataframe["slope_s"] & dataframe["slope_m"] & dataframe["slope_l"]
        )

        # 条件4: 流畅下跌
        smooth = self.smooth_bars.value
        dataframe["lower_low"] = dataframe["close"] < dataframe["close"].shift(1)
        dataframe["smooth_down"] = dataframe["lower_low"].rolling(smooth).min() >= 1

        # 条件5: 不反弹突破短均线
        nb = self.no_bounce_bars.value
        recent_high = dataframe["high"].rolling(nb).max()
        dataframe["no_bounce"] = recent_high < dataframe["ma_s"]

        # V4短周期信号（核心：依次排列 + 压制 + 流畅下跌）
        dataframe["v4_short_signal"] = (
            dataframe["ordered"]
            & dataframe["ma_above"]
            & dataframe["smooth_down"]
        )

        dataframe["daily_bearish"] = True
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            dataframe["v4_short_signal"],
            dataframe["daily_bearish"],
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda a, b: a & b, conditions),
            ["enter_short", "enter_tag"],
        ] = (1, "v4_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            qtpylib.crossed_above(dataframe["close"], dataframe["ma_s"]),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda a, b: a & b, conditions),
            ["exit_short", "exit_tag"],
        ] = (1, "exit_v4_short")
        return dataframe

    def custom_leverage(self, pair, current_time, current_rate,
                       proposed_leverage, max_leverage, side, **kwargs):
        return self.leverage.value
