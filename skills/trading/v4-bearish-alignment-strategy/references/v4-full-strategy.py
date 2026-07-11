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


class V4Strategy(IStrategy):
    """
    V4 交易策略 — 6条均线(SMA20/60/120+EMA20/60/120) + 看大做小

    逻辑:
    1. 大周期(direction_tf)确认方向: 6条均线依次排列压制/支撑K线
    2. 小周期(执行周期)找入场: 流畅下跌/上涨 + 不反弹
    3. 大周期确认后，才在小周期开仓
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
    direction_tf = CategoricalParameter(
        ["3m", "5m", "15m", "30m", "1h"], default="15m", space="buy"
    )

    order_types = {"entry": "limit", "exit": "limit",
                   "stoploss": "market", "stoploss_on_exchange": False}
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "sma20": {"color": "#FF6B6B"},
            "sma60": {"color": "#FFA500"},
            "sma120": {"color": "#FFD700"},
            "ema20": {"color": "#4ECDC4"},
            "ema60": {"color": "#45B7D1"},
            "ema120": {"color": "#96CEB4"},
        },
    }

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.direction_tf.value) for pair in pairs]

    def _ma_analysis(self, df, suffix=""):
        df["sma20"] = ta.SMA(df, timeperiod=20)
        df["sma60"] = ta.SMA(df, timeperiod=60)
        df["sma120"] = ta.SMA(df, timeperiod=120)
        df["ema20"] = ta.EMA(df, timeperiod=20)
        df["ema60"] = ta.EMA(df, timeperiod=60)
        df["ema120"] = ta.EMA(df, timeperiod=120)
        ma = ["sma20","sma60","sma120","ema20","ema60","ema120"]
        df["bearish_ord"] = (
            (df["sma20"]<df["sma60"]) & (df["sma60"]<df["sma120"])
            & (df["ema20"]<df["ema60"]) & (df["ema60"]<df["ema120"])
            & (df["ema20"]<df["sma20"])
        )
        df["bullish_ord"] = (
            (df["sma20"]>df["sma60"]) & (df["sma60"]>df["sma120"])
            & (df["ema20"]>df["ema60"]) & (df["ema60"]>df["ema120"])
            & (df["ema20"]>df["sma20"])
        )
        below = above = True
        for c in ma:
            below = below & (df["close"]<df[c])
            above = above & (df["close"]>df[c])
        df["below_all"] = below
        df["above_all"] = above
        df["trend_short"] = df["bearish_ord"] & df["below_all"]
        df["trend_long"] = df["bullish_ord"] & df["above_all"]
        return df

    def populate_indicators(self, dataframe, metadata):
        pair = metadata["pair"]
        dtf = self.direction_tf.value

        inf = self.dp.get_pair_dataframe(pair=pair, timeframe=dtf)
        if inf is not None:
            inf = self._ma_analysis(inf)
            dataframe = merge_informative_pair(
                dataframe, inf, self.timeframe, dtf, ffill=True
            )
            dataframe.drop(columns=[f"date_{dtf}"], inplace=True)
            # ⚠️ 列名有 _{dtf} 后缀
            dataframe["big_short"] = dataframe.get(f"trend_short_{dtf}", False)
            dataframe["big_long"] = dataframe.get(f"trend_long_{dtf}", False)
        else:
            dataframe["big_short"] = False
            dataframe["big_long"] = False

        dataframe = self._ma_analysis(dataframe)

        s = self.smooth_bars.value
        dataframe["lower"] = dataframe["close"] < dataframe["close"].shift(1)
        dataframe["smooth_d"] = dataframe["lower"].rolling(s).min() >= 1
        dataframe["higher"] = dataframe["close"] > dataframe["close"].shift(1)
        dataframe["smooth_u"] = dataframe["higher"].rolling(s).min() >= 1

        rh = dataframe["high"].rolling(2).max()
        dataframe["no_bounce"] = (rh < dataframe["sma20"]) & (rh < dataframe["ema20"])
        rl = dataframe["low"].rolling(2).min()
        dataframe["no_break"] = (rl > dataframe["sma20"]) & (rl > dataframe["ema20"])

        dataframe["v4_short"] = (
            dataframe["big_short"] & dataframe["smooth_d"]
            & dataframe["bearish_ord"] & dataframe["below_all"]
            & dataframe["no_bounce"]
        )
        dataframe["v4_long"] = (
            dataframe["big_long"] & dataframe["smooth_u"]
            & dataframe["bullish_ord"] & dataframe["above_all"]
            & dataframe["no_break"]
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
        es = qtpylib.crossed_above(dataframe["close"], dataframe["sma20"])
        el = qtpylib.crossed_below(dataframe["close"], dataframe["sma20"])
        dataframe.loc[es, ["exit_short", "exit_tag"]] = (1, "exit")
        dataframe.loc[el, ["exit_long", "exit_tag"]] = (1, "exit")
        return dataframe

    def custom_leverage(self, pair, current_time, current_rate,
                       proposed_leverage, max_leverage, side, **kwargs):
        return self.leverage.value