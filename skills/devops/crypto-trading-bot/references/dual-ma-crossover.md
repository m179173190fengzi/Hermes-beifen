# Dual MA Crossover Strategy (双均线交易系统)

A classic trend-following strategy based on two moving averages. When the fast MA crosses above the slow MA (Golden Cross), go long. When the fast MA crosses below the slow MA (Death Cross), go short.

**Source:** Based on the video "2026年加密货币第一桶金，双均线交易系统教学" by 以太坊教授幣哥.

## Core Logic

| Signal | Condition |
|--------|-----------|
| **Long entry** | Fast MA crosses **above** Slow MA (Golden Cross / 金叉) |
| **Short entry** | Fast MA crosses **below** Slow MA (Death Cross / 死叉) |
| **Long exit** | Fast MA crosses below Slow MA OR price closes below Slow MA |
| **Short exit** | Fast MA crosses above Slow MA OR price closes above Slow MA |
| **Take profit** | Fixed percentage (default 5%) |
| **Stop loss** | Fixed percentage (default 6%) + trailing stop |

## Implementation (FreqTrade)

```python
from functools import reduce

def populate_indicators(self, dataframe, metadata):
    dataframe["ma_fast"] = ta.EMA(dataframe, timeperiod=self.fast_ma_period.value)
    dataframe["ma_slow"] = ta.EMA(dataframe, timeperiod=self.slow_ma_period.value)
    dataframe["ma_exit_slow"] = ta.EMA(dataframe, timeperiod=self.exit_slow_ma_period.value)
    # Trend strength (%)
    dataframe["ma_distance"] = (
        (dataframe["ma_fast"] - dataframe["ma_slow"]) / dataframe["close"]
    ) * 100
    return dataframe

def populate_entry_trend(self, dataframe, metadata):
    conditions_long = [
        qtpylib.crossed_above(dataframe["ma_fast"], dataframe["ma_slow"]),
        dataframe["volume"] > 0,
    ]
    # Trend filter: price above slow MA
    conditions_long.append(dataframe["close"] > dataframe["ma_slow"])

    dataframe.loc[
        reduce(lambda a, b: a & b, conditions_long),
        ["enter_long", "enter_tag"],
    ] = (1, "golden_cross")
    return dataframe
```

## Parameter Ranges

| Parameter | Range | Default | Notes |
|-----------|-------|---------|-------|
| Fast MA | 20–100 | 50 | EMA by default; lower = more signals |
| Slow MA | 100–300 | 200 | Higher = fewer, more reliable signals |
| Exit Slow MA | 100–300 | 200 | Can be same as Slow MA or faster |
| Take Profit | 2%–15% | 5% | Fixed TP level |
| Use EMA vs SMA | Boolean | True | EMA is more responsive |
| Trend Filter | Boolean | True | Require price on the same side as signal |

## Timeframe Selection

| Timeframe | Signal quality | Trade frequency | Best for |
|-----------|---------------|-----------------|----------|
| 5m | Poor (lots of noise) | Very high | Scalping only |
| 15m | Fair | High | Day trading |
| 1h | Good | Medium | Swing trading (recommended start) |
| 4h | Very good | Low | Position trading |
| 1d | Excellent | Very low | Long-term trend following |

**Rule of thumb:** Start with 1h timeframe and EMA 50/200. If too few signals, try EMA 20/60. If too many false signals, try EMA 100/300 or switch to 4h.

## Known Issues

- **Performs poorly in ranging/sideways markets** — MA crossovers generate many false signals when price oscillates without a clear trend. Use with a trend filter (price above/below slow MA) to reduce noise.
- **Win rate typically 20–30%** — Trend-following strategies have low win rates but winners are larger than losers (high risk:reward when trend persists). Ensure your position sizing can handle 5+ consecutive losses.
- **Lagging indicator** — Entries are delayed relative to price reversal. You will never catch the exact top or bottom.
- **OKX ccxt proxy config** — The `httpProxy` setting in `ccxt_config` must be explicitly included in the exchange config. It can get silently dropped when editing the file. For live trading, also set `HTTP_PROXY`/`HTTPS_PROXY` environment variables.

## Full Example

See `/home/wei/ft_userdata/user_data/strategies/dual_ma_strategy.py` for a complete FreqTrade implementation with:
- Hyperoptable parameters
- Custom exit (fixed take profit)
- Trailing stop
- Support for both long and short
