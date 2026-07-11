# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union
from functools import reduce

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    PairLocks,
    informative,
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    RealParameter,
    timeframe_to_minutes,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    merge_informative_pair,
    stoploss_from_absolute,
    stoploss_from_open,
)

# --------------------------------
import talib.abstract as ta
from technical import qtpylib


class SixMaClusterStrategy(IStrategy):
    """
    V4 多级别空头交易策略

    核心逻辑:
    - 6条均线: SMA20, SMA60, SMA120, EMA20, EMA60, EMA120
    - 🟢 做多: 均线密集粘合 + K线站在所有均线上方（蓄力突破）
    - 🔴 做空: 均线空头排列流畅 + K线在所有均线下方 + 不反弹突破20均线（顺势下跌）

    同时监控1h/2h/4h三个级别，任意级别满足条件即开空。
    """

    INTERFACE_VERSION = 3

    can_short: bool = True

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    trailing_stop = False
    timeframe = "1h"

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    cluster_threshold = DecimalParameter(low=0.005, high=0.05, default=0.015, decimals=3, space="buy", optimize=True, load=True)
    confirm_bars = IntParameter(low=0, high=3, default=2, space="buy", optimize=True)
    bearish_confirm_bars = IntParameter(low=1, high=5, default=2, space="buy", optimize=True)
    no_bounce_bars = IntParameter(low=1, high=5, default=2, space="buy", optimize=True)
    bear_market_mode = BooleanParameter(default=True, space="buy")
    leverage = IntParameter(low=1, high=20, default=10, space="buy")
    daily_trend_ema = IntParameter(low=20, high=120, default=60, space="buy", optimize=True)
    use_daily_filter = BooleanParameter(default=True, space="buy")
    take_profit_pct = DecimalParameter(low=0.02, high=0.20, default=0.08, decimals=3, space="sell", optimize=True, load=True)

    startup_candle_count: int = 200

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        timeframes = ["1h", "2h", "4h"]
        return [(pair, tf) for pair in pairs for tf in timeframes]

    def _detect_v4_pattern(self, df: DataFrame, suffix: str = "") -> DataFrame:
        """在指定dataframe上检测V4空头模式"""
        df[f"sma20{suffix}"] = ta.SMA(df, timeperiod=20)
        df[f"sma60{suffix}"] = ta.SMA(df, timeperiod=60)
        df[f"sma120{suffix}"] = ta.SMA(df, timeperiod=120)
        df[f"ema20{suffix}"] = ta.EMA(df, timeperiod=20)
        df[f"ema60{suffix}"] = ta.EMA(df, timeperiod=60)
        df[f"ema120{suffix}"] = ta.EMA(df, timeperiod=120)

        ma_cols = [f"sma20{suffix}", f"sma60{suffix}", f"sma120{suffix}",
                   f"ema20{suffix}", f"ema60{suffix}", f"ema120{suffix}"]

        # 空头排列
        df[f"bearish_ordered{suffix}"] = (
            (df[f"sma20{suffix}"] < df[f"sma60{suffix}"])
            & (df[f"sma60{suffix}"] < df[f"sma120{suffix}"])
            & (df[f"ema20{suffix}"] < df[f"ema60{suffix}"])
            & (df[f"ema60{suffix}"] < df[f"ema120{suffix}"])
            & (df[f"ema20{suffix}"] < df[f"sma20{suffix}"])
        )

        # 均线斜率
        for col in ma_cols:
            df[f"{col}_sd{suffix}"] = df[col] < df[col].shift(1)
        df[f"all_slopes_down{suffix}"] = reduce(
            lambda a, b: a & b,
            [df[f"{col}_sd{suffix}"] for col in ma_cols]
        )

        # 空头排列确认
        df[f"bearish_aligned{suffix}"] = (
            (df[f"bearish_ordered{suffix}"] & df[f"all_slopes_down{suffix}"])
            .rolling(window=2).min() == 1
        )

        # 流畅下跌
        df[f"lower_low{suffix}"] = df["close"] < df["close"].shift(1)
        df[f"smooth_decline{suffix}"] = (
            df[f"lower_low{suffix}"].rolling(window=4).min() >= 1
        )

        # K线在MA20下方
        df[f"below_ma20{suffix}"] = df["close"] < df[f"sma20{suffix}"]
        df[f"ma20_sd{suffix}"] = df[f"sma20{suffix}"] < df[f"sma20{suffix}"].shift(1)

        # 不反弹
        recent_high = df["high"].rolling(window=2).max()
        df[f"no_bounce{suffix}"] = (
            (recent_high < df[f"sma20{suffix}"])
            & (recent_high < df[f"ema20{suffix}"])
        )

        # K线在所有均线下方
        df[f"price_below_all{suffix}"] = (
            (df["close"] < df[f"sma20{suffix}"])
            & (df["close"] < df[f"sma60{suffix}"])
            & (df["close"] < df[f"sma120{suffix}"])
            & (df["close"] < df[f"ema20{suffix}"])
            & (df["close"] < df[f"ema60{suffix}"])
            & (df["close"] < df[f"ema120{suffix}"])
        )

        # V4综合信号
        df[f"v4_signal{suffix}"] = (
            df[f"bearish_aligned{suffix}"]
            | (
                df[f"smooth_decline{suffix}"]
                & df[f"below_ma20{suffix}"]
                & df[f"ma20_sd{suffix}"]
                & df[f"no_bounce{suffix}"]
            )
        )

        return df

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata["pair"]

        # 加载2h和4h informatives
        for tf in ["2h", "4h"]:
            informative = self.dp.get_pair_dataframe(pair=pair, timeframe=tf)
            if informative is not None:
                informative = self._detect_v4_pattern(informative, suffix=f"_{tf}")
                dataframe = merge_informative_pair(
                    dataframe, informative, self.timeframe, tf, ffill=True
                )
                dataframe.drop(columns=[f"date_{tf}"], inplace=True)

        # 1h级别检测
        dataframe = self._detect_v4_pattern(dataframe, suffix="")

        # 多级别综合信号：任意级别有信号就开单
        dataframe["v4_short_signal"] = (
            dataframe["v4_signal"]
            | dataframe.get("v4_signal_2h", False)
            | dataframe.get("v4_signal_4h", False)
        )

        # 多级别 price_below_all
        price_below = dataframe["price_below_all"]
        if "price_below_all_2h" in dataframe.columns:
            price_below = price_below | dataframe["price_below_all_2h"]
        if "price_below_all_4h" in dataframe.columns:
            price_below = price_below | dataframe["price_below_all_4h"]
        dataframe["price_below_all"] = price_below

        # 多级别 no_bounce
        no_bounce = dataframe["no_bounce"]
        if "no_bounce_2h" in dataframe.columns:
            no_bounce = no_bounce & dataframe["no_bounce_2h"]
        if "no_bounce_4h" in dataframe.columns:
            no_bounce = no_bounce & dataframe["no_bounce_4h"]
        dataframe["no_bounce_above_ma20"] = no_bounce

        # K线在所有均线上方（做多用）
        dataframe["price_above_all"] = (
            (dataframe["close"] > dataframe["sma20"])
            & (dataframe["close"] > dataframe["sma60"])
            & (dataframe["close"] > dataframe["sma120"])
            & (dataframe["close"] > dataframe["ema20"])
            & (dataframe["close"] > dataframe["ema60"])
            & (dataframe["close"] > dataframe["ema120"])
        )

        # 均线密集（做多用）
        ma_cols = ["sma20", "sma60", "sma120", "ema20", "ema60", "ema120"]
        ma_df = dataframe[ma_cols]
        ma_max = ma_df.max(axis=1)
        ma_min = ma_df.min(axis=1)
        dataframe["ma_spread"] = (ma_max - ma_min) / dataframe["close"]
        dataframe["is_clustered"] = dataframe["ma_spread"] < self.cluster_threshold.value
        confirm = self.confirm_bars.value
        if confirm > 0:
            dataframe["cluster_confirmed"] = (
                dataframe["is_clustered"].rolling(window=confirm).min() == 1
            )
        else:
            dataframe["cluster_confirmed"] = dataframe["is_clustered"]

        # 日线趋势过滤
        daily_tf = "1d"
        informative = self.dp.get_pair_dataframe(pair=pair, timeframe=daily_tf)
        if informative is not None:
            daily_ema_period = self.daily_trend_ema.value
            informative["daily_ema"] = ta.EMA(informative, timeperiod=daily_ema_period)
            informative["daily_bullish"] = informative["close"] > informative["daily_ema"]

            dataframe = merge_informative_pair(
                dataframe, informative, self.timeframe, daily_tf, ffill=True
            )
            dataframe.drop(columns=["date_1d"], inplace=True)
            dataframe["daily_trend_bullish"] = dataframe["daily_bullish_1d"]
        else:
            dataframe["daily_trend_bullish"] = True

        # 多空开关
        dataframe["long_allowed"] = True
        dataframe["short_allowed"] = True
        if self.bear_market_mode.value:
            dataframe["long_allowed"] = False
        if self.use_daily_filter.value:
            dataframe.loc[dataframe["daily_trend_bullish"] == True, "short_allowed"] = False
            dataframe.loc[dataframe["daily_trend_bullish"] == False, "long_allowed"] = False

        dataframe["volume_ma"] = ta.SMA(dataframe["volume"], timeperiod=20)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 做多
        conditions_long = [
            dataframe["cluster_confirmed"],
            dataframe["price_above_all"],
            dataframe["long_allowed"],
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda a, b: a & b, conditions_long),
            ["enter_long", "enter_tag"],
        ] = (1, "cluster_long")

        # 做空
        conditions_short = [
            dataframe["v4_short_signal"],
            dataframe["price_below_all"],
            dataframe["no_bounce_above_ma20"],
            dataframe["short_allowed"],
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda a, b: a & b, conditions_short),
            ["enter_short", "enter_tag"],
        ] = (1, "bearish_aligned_short")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 平多
        exit_long_conditions = [
            (
                qtpylib.crossed_below(dataframe["close"], dataframe["sma20"])
                | qtpylib.crossed_below(dataframe["close"], dataframe["ema20"])
            ),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda a, b: a & b, exit_long_conditions),
            ["exit_long", "exit_tag"],
        ] = (1, "exit_long_ma20_break")

        # 平空
        exit_short_conditions = [
            (
                qtpylib.crossed_above(dataframe["close"], dataframe["sma20"])
                | qtpylib.crossed_above(dataframe["close"], dataframe["ema20"])
            ),
            dataframe["volume"] > 0,
        ]
        dataframe.loc[
            reduce(lambda a, b: a & b, exit_short_conditions),
            ["exit_short", "exit_tag"],
        ] = (1, "exit_short_ma20_break")

        return dataframe

    def custom_leverage(self, pair: str, current_time: datetime, current_rate: float,
                       proposed_leverage: float, max_leverage: float, side: str,
                       **kwargs) -> float:
        return self.leverage.value

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime,
                    current_rate: float, current_profit: float, **kwargs) -> Optional[Union[str, bool]]:
        if current_profit >= self.take_profit_pct.value:
            return "take_profit"
        return None
