---
name: freqtrade-strategy-dev
description: "Develop, backtest, and iterate Freqtrade trading strategies — indicator patterns, multi-timeframe analysis, risk management, and performance optimization."
version: 1.3.0
author: Hermes Agent
tags: [freqtrade, trading, strategy-development, backtesting]
---

# Freqtrade Strategy Development

Build and refine Freqtrade strategies for crypto futures trading. Covers indicator-based entry/exit logic, multi-timeframe analysis, backtesting, and iterative optimization.

## Quick Start

```bash
# Activate venv
cd ~/ft_userdata && source freqtrade/.venv/bin/activate

# List strategies
freqtrade list-strategies -c user_data/config-okx.json

# Run backtest
freqtrade backtesting -c user_data/config-okx.json --strategy MyStrategy -i 1h --timerange 20260501-

# Run dry-run live
freqtrade trade -c user_data/config-okx.json --strategy MyStrategy
```

## Strategy Structure

### Required imports

```python
import talib.abstract as ta
from technical import qtpylib
from functools import reduce
from pandas import DataFrame
from freqtrade.strategy import (
    IStrategy, Trade,
    BooleanParameter, DecimalParameter, IntParameter,
    merge_informative_pair,
)
```

### Key class attributes

```python
INTERFACE_VERSION = 3
can_short: bool = True          # Enable shorts for futures
minimal_roi = {"0": 100.0}      # Disable auto-ROI, rely on exit signals
stoploss = -0.02                # Adjust for leverage (10x = 2% = 20% margin)
timeframe = "1h"
process_only_new_candles = True
use_exit_signal = True
startup_candle_count: int = 200 # Must cover longest MA period
```

### Entry/Exit logic patterns

**Entry signals** go in `populate_entry_trend`:
```python
conditions_long = [
    # ... pandas conditions ...
    dataframe["volume"] > 0,
]
dataframe.loc[reduce(lambda a, b: a & b, conditions_long),
              ["enter_long", "enter_tag"]] = (1, "my_tag")
```

**Exit signals** go in `populate_exit_trend`:
```python
exit_long_conditions = [
    qtpylib.crossed_below(dataframe["close"], dataframe["sma20"]),
    dataframe["volume"] > 0,
]
dataframe.loc[reduce(lambda a, b: a & b, exit_long_conditions),
              ["exit_long", "exit_tag"]] = (1, "my_exit_tag")
```

## Working with Reference Samples

When the user says "参考这段走势" and gives a date/time range:

1. **Determine the pair FIRST** — 用户说参考走势时，默认是BTC/USDT:USDT。**不要**默认用ETH，**不要**自己猜。被纠正过。直接确认「你说的是BTC对吧？」
2. **Download specific timeframe data** for the correct pair
3. **Compute indicators**, print the time series to verify
4. **Check signal triggering** — does the pattern appear in the strategy's signal column?
5. **Small tweaks only** — adjust params by 1-2 units at most
6. **Full backtest to verify**, not just the sample

⚠️ **Common mistake**: analyzing ETH when user said BTC. This wastes multiple turns and confuses the analysis.

### Key reference samples (save from this session):
- BTC 1m 2026-06-27 11:15~11:43 UTC (19:15~19:43 Beijing): clean short drop 60340→60171, textbook 流畅下跌

## "看大做小" Concept — Multi-TF Sequential Search

### Core Principle

看大做小 is a **top-down sequential search**, NOT a fixed two-level filter and NOT a same-chart concept:

```
15m 走出下跌趋势（均线排列确认方向），但还没到入场点
  ↓ 大周期没机会，往下找
5m 看 → 还没有？
  ↓ 再往下
3m 看 → 接近了
  ↓ 再往下
1m 看 → 流畅下跌+不反弹 → 开空
```

**This was corrected by the user multiple times. Here is the evolution:**
- ❌ I guessed: 看大做小 = 同一张图的两个概念（均线结构+K线走势）
- ✅ User: "不是同一张图"
- ❌ I guessed: 看大做小 = 15m方向+1m入场（固定两个级别）
- ✅ User: "灵活运用，以此类推"
- ❌ I changed the user's MAs to SMA5/10/20
- ✅ User: "你没按我说的均线来" — ** NEVER change the user's specified MA parameters **
- ✅ **Final correct:** 从大周期开始确认方向，然后向下逐级搜索入场。没有固定组合，灵活变通。

**When implementing:**
1. Use `merge_informative_pair` to load the higher-TF data
2. Add `_{timeframe}` suffix when reading merged columns
3. Keep the user's specified MAs (SMA20/60/120 + EMA20/60/120) on ALL timeframes
4. Make `direction_tf` configurable via `CategoricalParameter`

### Implementation

**Approach A: Cross-TF Bias (merge_informative_pair)**

```python
def informative_pairs(self):
    pairs = self.dp.current_whitelist()
    return [(pair, self.direction_tf.value) for pair in pairs]

def populate_indicators(self, dataframe, metadata):
    inf = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe=self.direction_tf.value)
    if inf is not None:
        inf["bias"] = (inf["sma20"] < inf["sma60"]) & (inf["sma60"] < inf["sma120"])
        dataframe = merge_informative_pair(
            dataframe, inf, self.timeframe, self.direction_tf.value, ffill=True
        )
        # ⚠️ 列名会被加上 _{timeframe} 后缀！
        dataframe["bias"] = dataframe.get(f"bias_{self.direction_tf.value}", False)
```

⚠️ **⚠️ merge suffix pitfall**: `merge_informative_pair` adds `_{timeframe}` suffix to ALL informative columns. If dtf="15m", your bias column becomes `bias_15m`. Access it with `dataframe.get(f"bias_{dtf}", False)`, NOT `dataframe["bias"]`.

**Approach B: Same-Chart Long-MA-as-Bias**

Use a longer-period MA on the SAME chart to represent the "big picture", avoiding cross-TF merge issues entirely. This is often preferred for signal density:

```python
# Long MA for direction
dataframe["ma_t"] = ta.EMA(dataframe, timeperiod=60)
dataframe["bias_short"] = dataframe["ma_t"] > dataframe["close"]
dataframe["bias_long"] = dataframe["ma_t"] < dataframe["close"]
```

### Typical 看大做小 Combinations

| Execution TF | Direction Bias (same chart) |
|:-----------:|:---------------------------:|
| 1m | EMA60 |
| 5m | EMA60 |
| 15m | EMA60 |
| 1h | EMA60 |

## Timeframe Performance Comparison

Same strategy on different timeframes can produce dramatically different results:

| Timeframe | Win Rate | Profit | Best for |
|:---------:|:--------:|:------:|:---------|
| 1m-5m | 8-20% | -1~-3% ❌ | Nothing — too noisy |
| 15m | 0-20% | -0.38~-2% ⚠️ | Marginal |
| **1h** | 47-56% | **+4.5~+6%** ✅ | Good |
| **2h** | 44% | +8% ✅ | Good |
| **4h** | **58%** | **+9.8%** 🏆 | **Best** |

**Key insight**: Higher timeframes = fewer but higher-quality signals. Short timeframes (≤15m) rarely work for multi-MA trend-following strategies.

## Common Indicator Patterns

### V4 Bearish alignment (6 MAs)

```python
dataframe["bearish_ordered"] = (
    (dataframe["sma20"] < dataframe["sma60"]) &
    (dataframe["sma60"] < dataframe["sma120"]) &
    (dataframe["ema20"] < dataframe["ema60"]) &
    (dataframe["ema60"] < dataframe["ema120"]) &
    (dataframe["ema20"] < dataframe["sma20"])
)
```

### Smooth decline / "流畅下跌"

```python
smooth = 3  # consecutive lower closes
dataframe["lower_low"] = dataframe["close"] < dataframe["close"].shift(1)
dataframe["smooth_down"] = dataframe["lower_low"].rolling(smooth).min() >= 1
```

### "不反弹" (No bounce above MA20)

```python
rh = dataframe["high"].rolling(2).max()
dataframe["no_bounce"] = (rh < dataframe["sma20"]) & (rh < dataframe["ema20"])
```

## Pitfalls

- **NEVER change the user's specified MA parameters.** The user explicitly wants SMA20/60/120 + EMA20/60/120. If you try to use SMA5/10/20 for short timeframes, the user will (rightfully) be angry. Every timeframe gets the same 6 MAs.
- **Merge suffix**: `merge_informative_pair` adds `_{timeframe}` suffix to all informative columns. Access as `column_name_15m`, not `column_name`.
- **MTF merge direction**: You can ONLY merge a SLOWER timeframe INTO a FASTER base. Merging faster → slower raises `ValueError`.
- **Bool column conflict**: DON'T create `dataframe["enter_short"]` as a boolean in `populate_indicators`. The subsequent `dataframe.loc[..., ["enter_short", "enter_tag"]] = (1, "tag")` in `populate_entry_trend` raises `TypeError: Invalid value '1' for dtype 'bool'`. Fix: use a differently-named signal column (e.g. `dataframe["v4_short"]`) then assign to `enter_short` in `populate_entry_trend`.
- **Pair confusion**: When the user says "参考BTC一段走势", use BTC/USDT:USDT, NOT ETH. Analyzing the wrong pair wastes multiple turns.
- **Data coverage**: Running backtest on a narrow date range after warmup may MISS the best trading periods. Always ensure enough data for the full test window.
- **Short timeframe trap**: 1m/5m/15m are NOT suitable for multi-MA strategies. Warmup windows consume too much data.
- **Proxy for Python**: If CCXT times out but curl works, try removing proxy from ccxt_config or increasing timeout to 60000ms.
- **看大做小不是固定两个级别**: 不要硬编码15m→1m。用户要求的是灵活搭配，根据市场情况选择向下钻到哪一级。

## Related Skills

| Skill | When to load |
|:------|:-------------|
| `v4-bearish-alignment-strategy` | 用户提到V4策略、6均线时 |
| `freqtrade-install` | 初始安装和配置问题 |
