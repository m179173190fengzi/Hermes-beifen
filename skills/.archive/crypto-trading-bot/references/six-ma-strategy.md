# Six-MA Cluster / Bearish Alignment Strategy

A FreqTrade strategy using 6 moving averages (SMA20/60/120 + EMA20/60/120) with two distinct entry modes:

- **LONG**: MA cluster + price above all MAs (breakout from consolidation)
- **SHORT**: Bearish alignment + price below all MAs + no pullback to MA20 (trend continuation)

## Strategy File

`user_data/strategies/six_ma_cluster.py`

## Key Parameters (defaults)

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| `cluster_threshold` | 0.015 | 0.005–0.05 | MA cluster tightness (long entry) |
| `confirm_bars` | 2 | 0–3 | Cluster confirmation candles (long) |
| `bearish_confirm_bars` | 2 | 1–5 | Bearish alignment confirmation (short) |
| `no_bounce_bars` | 2 | 1–5 | Candles without MA20 break (short) |
| `daily_trend_ema` | 60 | 20–120 | Daily EMA period for trend filter |
| `use_daily_filter` | True | bool | Enable daily trend filter |
| `bear_market_mode` | True | bool | Force shorts-only |
| `take_profit_pct` | 0.08 | 0.02–0.20 | Fixed take-profit |
| `leverage` | 10 | 1–20 | Leverage multiplier |

## Strategy Class Attributes

```python
INTERFACE_VERSION = 3
can_short = True
timeframe = "1h"
stoploss = -0.02       # 2% → 20% margin at 10x
minimal_roi = {"0": 100.0}
trailing_stop = False   # Rely on exit signals
startup_candle_count = 200
```

## Entry Logic

### Long: `cluster_long`
1. `cluster_confirmed` — all 6 MAs within `cluster_threshold` % of price for `confirm_bars` candles
2. `price_above_all` — close > all 6 MAs
3. `long_allowed` — daily trend bullish AND bear_market_mode disabled

### Short: `bearish_aligned_short`
1. `bearish_aligned` — MAs perfectly descending (SMA20<SMA60<SMA120, EMA20<EMA60<EMA120, EMA20<SMA20) for `bearish_confirm_bars` candles, AND all MAs sloping down
2. `price_below_all` — close < all 6 MAs
3. `no_bounce_above_ma20` — recent N candles' high < SMA20 and EMA20
4. `short_allowed` — daily trend bearish

## Exit Logic

### Close Long
- `crossed_below(close, sma20)` OR `crossed_below(close, ema20)`

### Close Short
- `crossed_above(close, sma20)` OR `crossed_above(close, ema20)`

### Take Profit (custom_exit)
- Fixed percentage: `current_profit >= take_profit_pct.value`

## V4 Enhancement: Smooth Decline Detection

Added in v4 to capture bearish trends when the strict bearish alignment condition is too restrictive. Detects "流畅下跌" — price making consistently lower lows without bouncing to MA20.

```python
smooth_period = 4  # 4 consecutive lower closes for 2h timeframe
dataframe["lower_low"] = dataframe["close"] < dataframe["close"].shift(1)
dataframe["smooth_decline"] = (
    dataframe["lower_low"].rolling(window=smooth_period).min() >= 1
)
dataframe["below_ma20"] = dataframe["close"] < dataframe["sma20"]
dataframe["ma20_sloping_down"] = dataframe["sma20"] < dataframe["sma20"].shift(1)

# Combined signal: bearish alignment (strict) OR smooth decline (flexible)
dataframe["v4_short_signal"] = (
    dataframe["bearish_aligned"]
    | (
        dataframe["smooth_decline"]
        & dataframe["below_ma20"]
        & dataframe["ma20_sloping_down"]
        & dataframe["no_bounce_above_ma20"]
    )
)
```

**When to use:** On 2h timeframe or when the market shows clean trending moves but MAs haven't fully aligned yet. The June 1-7 ETH move (2006→1552) is the canonical example.

## Timeframe Comparison (May-June 2026, shorts-only, 1000 USDT)

| Timeframe | Total | Win% | Drawdown | Sharpe | Trades | Best For |
|-----------|-------|------|----------|--------|--------|----------|
| **1h** | +4.51% | 56.2% | 2.06% | 2.28 | 32 | All-around |
| **2h** | **+8.04%** | 44.0% | 5.37% | 3.21 | 25 | Smooth decline patterns |
| **4h** | **+9.79%** | **58.3%** | **1.39%** | **3.43** | 12 | Highest quality |

## Backtest Results (1h, May-June 2026)

| Version | Total | Win% | Drawdown | Notes |
|---------|-------|------|----------|-------|
| v1: cluster only | -4.82% | 26.1% | 6.67% | Baseline, both directions |
| v2: + daily filter | -0.87% | 29.8% | 2.62% | Trend filter improved all metrics |
| v3: bearish alignment for shorts | +1.44% | 38.8% | 4.24% | Short entries improved significantly |
| v4: bear market mode (shorts only) | +4.51% | 56.2% | 2.06% | Best result, Sharpe 2.28 |

## Key Insight: Short Leg Optimization

The largest improvement came from changing the short entry from "cluster below MAs" (v1) to "bearish alignment + no bounce" (v3). These are fundamentally different market regimes:

- **Cluster below MAs** = consolidation near support — prone to false breakouts
- **Bearish alignment** = established downtrend — momentum continuation

The bearish alignment check catches already-flowing trends, while cluster detection catches consolidation breakouts.
