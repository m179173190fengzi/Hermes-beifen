"""
SixMaClusterStrategy v4 — 六均线交易系统 (OKX 合约)
====================================================
时间框架: 1h (推荐)
交易对: BTC/USDT:USDT, ETH/USDT:USDT
6条均线: SMA20, SMA60, SMA120, EMA20, EMA60, EMA120
杠杆: 10x (通过 custom_leverage + stoploss=-0.02 实现)

入场逻辑:
  - 🟢 做多: 均线密集粘合 + K线在所有均线上方 + 日线趋势向上 (熊市模式关闭时才启用)
  - 🔴 做空: 空头排列流畅(均线完美递减) + 所有均线斜率向下 + K线在所有均线下方 + 不反弹突破MA20 + 日线趋势向下

出场逻辑:
  - 平多: K线跌破 MA20 或 EMA20
  - 平空: K线上破 MA20 或 EMA20

v4 新增:
  - bear_market_mode: 熊市强制只做空 (默认 True)
  - leverage: 杠杆倍数 1-20x (默认 10x)
  - stoploss = -0.02 (10x下 = 20%本金)
  - 禁用移动止损,完全靠 exit 信号

Copy to: ~/ft_userdata/user_data/strategies/six_ma_cluster.py
"""

from functools import reduce
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (
    IStrategy,
    Trade,
    BooleanParameter,
    DecimalParameter,
    IntParameter,
    merge_informative_pair,
)
import talib.abstract as ta
from technical import qtpylib


class SixMaClusterStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True

    minimal_roi = {"0": 100.0}
    stoploss = -0.02                          # 10x杠杆下2%跌幅 = 20%本金亏损
    trailing_stop = False                     # 禁用移动止损,靠exit信号出场

    timeframe = "1h"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # 做多: 均线密集阈值
    cluster_threshold = DecimalParameter(
        0.005, 0.05, default=0.015, decimals=3, space="buy", optimize=True, load=True
    )
    confirm_bars = IntParameter(0, 3, default=2, space="buy", optimize=True)

    # 做空: 空头排列参数
    bearish_confirm_bars = IntParameter(1, 5, default=2, space="buy", optimize=True)
    no_bounce_bars = IntParameter(1, 5, default=2, space="buy", optimize=True)

    # 熊市模式: 强制不做多 (当前币圈熊市推荐开启)
    bear_market_mode = BooleanParameter(default=True, space="buy")

    # 杠杆倍数
    leverage = IntParameter(1, 20, default=10, space="buy")

    # 日线趋势
    daily_trend_ema = IntParameter(20, 120, default=60, space="buy", optimize=True)
    use_daily_filter = BooleanParameter(default=True, space="buy")

    # 止盈
    take_profit_pct = DecimalParameter(
        0.02, 0.20, default=0.08, decimals=3, space="sell", optimize=True, load=True
    )

    startup_candle_count = 200

    order_types = {"entry": "limit", "exit": "limit", "stoploss": "market", "stoploss_on_exchange": False}
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    def informative_pairs(self):
        return [(pair, "1d") for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe, metadata):
        # 6条均线
        for period in [20, 60, 120]:
            dataframe[f"sma{period}"] = ta.SMA(dataframe, timeperiod=period)
            dataframe[f"ema{period}"] = ta.EMA(dataframe, timeperiod=period)

        ma_cols = [f"{t}{p}" for t in ["sma", "ema"] for p in [20, 60, 120]]
        ma_df = dataframe[ma_cols]

        # === 做多: 均线密集 ===
        ma_max = ma_df.max(axis=1)
        ma_min = ma_df.min(axis=1)
        dataframe["ma_spread"] = (ma_max - ma_min) / dataframe["close"]
        dataframe["is_clustered"] = dataframe["ma_spread"] < self.cluster_threshold.value
        confirm = self.confirm_bars.value
        if confirm > 0:
            dataframe["cluster_confirmed"] = dataframe["is_clustered"].rolling(confirm).min() == 1
        else:
            dataframe["cluster_confirmed"] = dataframe["is_clustered"]

        # === 做空: 空头排列 ===
        dataframe["bearish_ordered"] = (
            (dataframe["sma20"] < dataframe["sma60"])
            & (dataframe["sma60"] < dataframe["sma120"])
            & (dataframe["ema20"] < dataframe["ema60"])
            & (dataframe["ema60"] < dataframe["ema120"])
            & (dataframe["ema20"] < dataframe["sma20"])
        )
        for col in ma_cols:
            dataframe[f"{col}_down"] = dataframe[col] < dataframe[col].shift(1)
        dataframe["all_slopes_down"] = reduce(
            lambda a, b: a & b, [dataframe[f"{c}_down"] for c in ma_cols]
        )
        bc = self.bearish_confirm_bars.value
        if bc > 0:
            dataframe["bearish_aligned"] = (
                (dataframe["bearish_ordered"] & dataframe["all_slopes_down"]).rolling(bc).min() == 1
            )
        else:
            dataframe["bearish_aligned"] = dataframe["bearish_ordered"] & dataframe["all_slopes_down"]

        # 不反弹验证
        nb = self.no_bounce_bars.value
        if nb > 0:
            recent_high = dataframe["high"].rolling(nb).max()
            dataframe["no_bounce"] = (recent_high < dataframe["sma20"]) & (recent_high < dataframe["ema20"])
        else:
            dataframe["no_bounce"] = (dataframe["high"] < dataframe["sma20"]) & (dataframe["high"] < dataframe["ema20"])

        # K线位置
        dataframe["price_above_all"] = reduce(
            lambda a, b: a & b, [dataframe["close"] > dataframe[c] for c in ma_cols]
        )
        dataframe["price_below_all"] = reduce(
            lambda a, b: a & b, [dataframe["close"] < dataframe[c] for c in ma_cols]
        )

        # === 日线趋势过滤 ===
        informative = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1d")
        if informative is not None:
            informative["ema"] = ta.EMA(informative["close"], timeperiod=self.daily_trend_ema.value)
            informative["bullish"] = informative["close"] > informative["ema"]
            dataframe = merge_informative_pair(dataframe, informative, self.timeframe, "1d", ffill=True)
            dataframe.drop(columns=["date_1d"], inplace=True)
            dataframe["daily_bullish"] = dataframe["bullish_1d"]
        else:
            dataframe["daily_bullish"] = True

        # === 多空开关 ===
        dataframe["long_allowed"] = True
        dataframe["short_allowed"] = True

        # 熊市模式: 屏蔽所有多头信号
        if self.bear_market_mode.value:
            dataframe["long_allowed"] = False

        # 日线趋势过滤: 多头趋势只做多,空头趋势只做空
        if self.use_daily_filter.value:
            dataframe.loc[dataframe["daily_bullish"], "short_allowed"] = False
            dataframe.loc[~dataframe["daily_bullish"], "long_allowed"] = False

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        # 做多
        conditions_long = [
            dataframe["cluster_confirmed"], dataframe["price_above_all"],
            dataframe["long_allowed"], dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda a, b: a & b, conditions_long), ["enter_long", "enter_tag"]] = (1, "cluster_long")

        # 做空
        conditions_short = [
            dataframe["bearish_aligned"], dataframe["price_below_all"],
            dataframe["no_bounce"], dataframe["short_allowed"], dataframe["volume"] > 0,
        ]
        dataframe.loc[reduce(lambda a, b: a & b, conditions_short), ["enter_short", "enter_tag"]] = (1, "bearish_aligned_short")

        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        exit_long = qtpylib.crossed_below(dataframe["close"], dataframe["sma20"]) | qtpylib.crossed_below(dataframe["close"], dataframe["ema20"])
        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (1, "exit_long_ma20")

        exit_short = qtpylib.crossed_above(dataframe["close"], dataframe["sma20"]) | qtpylib.crossed_above(dataframe["close"], dataframe["ema20"])
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (1, "exit_short_ma20")

        return dataframe

    def custom_leverage(self, pair, current_time, current_rate, proposed_leverage, max_leverage, side, **kwargs):
        return float(self.leverage.value)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_profit >= self.take_profit_pct.value:
            return "take_profit"
        return None
