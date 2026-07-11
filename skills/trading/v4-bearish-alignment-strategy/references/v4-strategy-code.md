# V4策略代码参考

策略文件: ~/ft_userdata/user_data/strategies/v4.py
类名: V4Strategy

## 最终正确版本 (v5.0.0+)

关键逻辑:
1. 方向TF (direction_tf) 看6均线排列 → 设定多空偏向
2. 执行TF (当前timeframe) 看流畅走势 + 不反弹 → 入场
3. 大周期方向过滤后，只允许同向入场
4. bear_market_mode=True 禁用做多

## 关键代码片段

### 大周期方向合并（注意列名后缀！）

```python
# direction_tf = "15m"
inf = self.dp.get_pair_dataframe(pair=pair, timeframe=dtf)
if inf is not None:
    inf = self._ma_analysis(inf)
    dataframe = merge_informative_pair(
        dataframe, inf, self.timeframe, dtf, ffill=True
    )
    dataframe.drop(columns=[f"date_{dtf}"], inplace=True)
    # 注意！列名会被加 _{dtf} 后缀！
    dataframe["big_short"] = dataframe.get(f"trend_short_{dtf}", False)
```

### 6均线分析（共享函数）

```python
def _ma_analysis(self, df, suffix=""):
    df["sma20"] = ta.SMA(df, timeperiod=20)
    ...
    df["bearish_ord"] = (
        (df["sma20"]<df["sma60"]) & (df["sma60"]<df["sma120"])
        & (df["ema20"]<df["ema60"]) & (df["ema60"]<df["ema120"])
        & (df["ema20"]<df["sma20"])
    )
    ...
```

### 入场逻辑（populate_entry_trend）

```python
# 不要直接在populate_indicators里设enter_short！
# 用v4_short/v4_long做布尔列
dataframe.loc[
    dataframe["v4_short"] & (dataframe["volume"] > 0),
    ["enter_short", "enter_tag"],
] = (1, "v4空")
```

### 出场逻辑

```python
# 平空: K线上破SMA20
qtpylib.crossed_above(dataframe["close"], dataframe["sma20"])
# 平多: K线下破SMA20
qtpylib.crossed_below(dataframe["close"], dataframe["sma20"])
```

## 参考样本分析

BTC 1m 2026-06-27 11:15~11:43 UTC (19:15~19:43 北京):
- 60340 → 60171 (跌169点, -0.28%)
- 均线在K线上方依次排列压制
- 流畅3连跌 + 不反弹 → 教科书V4空头入场点

TODO: 将此代码保存为 templates/ 供下次直接使用。
