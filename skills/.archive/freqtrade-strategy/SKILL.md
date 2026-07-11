---
name: freqtrade-strategy
category: software-development
description: Develop, backtest, and optimize FreqTrade trading strategies — entry/exit logic, multi-timeframe indicators, iterative optimization, result analysis.
---

# FreqTrade Strategy Development

Develop, backtest, and iteratively optimize FreqTrade strategies. Covers the full workflow: indicator design → entry/exit logic → backtesting → result analysis → iterative refinement.

## When to use

- User wants a custom trading strategy (not stock templates)
- User has a trading idea and needs to code it into FreqTrade
- A strategy needs optimization (win rate, drawdown, Sharpe)
- Diagnostic: why is a strategy losing money? (split long/short, check timeframe, analyze drawdown)

## Strategy Development Workflow

### 1. Skeleton — start with a minimal working strategy

```
user_data/strategies/my_strategy.py  ← single file, inherits IStrategy
```

Required class attributes:
- `INTERFACE_VERSION = 3`
- `timeframe` — start with `"1h"` (less noise than 15m/5m)
- `can_short: bool = True` (if futures)
- `stoploss` — e.g. `-0.05` (adjust for leverage)
- `minimal_roi = {"0": 100.0}` (disable ROI, rely on exit signals)
- `startup_candle_count` — enough for your longest MA period

### 2. Indicators — `populate_indicators()`

- Use `ta.SMA()` / `ta.EMA()` from `talib.abstract`
- For multi-timeframe data, use `self.dp.get_pair_dataframe()` with `merge_informative_pair()`
- Create boolean columns for entry conditions (cleaner than inline conditions)

**Pattern — Multi-timeframe (informative pairs):**

```python
def informative_pairs(self):
    pairs = self.dp.current_whitelist()
    return [(pair, "1d") for pair in pairs]

def populate_indicators(self, dataframe, metadata):
    # ... compute 1h indicators ...

    # Daily trend
    informative = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe="1d")
    if informative is not None:
        informative["daily_ema"] = ta.EMA(informative, timeperiod=60)
        informative["daily_bullish"] = informative["close"] > informative["daily_ema"]
        dataframe = merge_informative_pair(
            dataframe, informative, self.timeframe, "1d", ffill=True
        )
        dataframe.drop(columns=["date_1d"], inplace=True)
        # ⚠️ Column becomes "daily_bullish_1d" after merge (suffixed with timeframe)
        dataframe["daily_trend_bullish"] = dataframe["daily_bullish_1d"]
    else:
        # Fallback when no daily data available
        dataframe["daily_trend_bullish"] = True
    return dataframe
```

### 3. Entry logic — `populate_entry_trend()`

**Pattern — clean condition lists with `reduce`:**

```python
from functools import reduce

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
```

### 4. Exit logic — `populate_exit_trend()`

Same pattern as entry. Use `qtpylib.crossed_above()` / `qtpylib.crossed_below()` for crossover detection.

### 5. Leverage (futures)

```python
def custom_leverage(self, pair, current_time, current_rate,
                    proposed_leverage, max_leverage, side, **kwargs) -> float:
    return 10.0  # or self.leverage.value for optimization
```

**⚠️ Stoploss + leverage relationship:** With 10x leverage, a −2% stoploss burns 20% of margin. Adjust stoploss inversely with leverage:
- 1x (spot): stoploss −5% is fine
- 3x: stoploss −3% to −4%
- 10x: stoploss −1.5% to −2.5%
- 20x: stoploss −0.8% to −1.5%

### 6. Fixed take-profit (custom_exit)

```python
def custom_exit(self, pair, trade, current_time, current_rate,
                current_profit, **kwargs):
    if current_profit >= self.take_profit_pct.value:
        return "take_profit"
    return None
```

Use `DecimalParameter` for the take profit target so it can be optimized via hyperopt. If using exit signals as the primary exit, set `minimal_roi = {"0": 100.0}` to disable automatic ROI exits.

## Backtesting Workflow

### Data preparation

```bash
# Download data — MUST match your strategy's timeframe
freqtrade download-data -c config.json --exchange okx \
  --trading-mode futures --timeframes 1h --days 60 \
  -p BTC/USDT:USDT ETH/USDT:USDT

# Check what data is available
freqtrade list-data --exchange okx --trading-mode futures
```

For multi-timeframe strategies (e.g., 1h + 1d), download BOTH:
```bash
freqtrade download-data ... --timeframes "1h,1d"
```

### Running the backtest

```bash
freqtrade backtesting -c config.json --strategy MyStrategy \
  -i 1h --timerange 20260501- --export trades
```

Key flags:
- `-i` / `--timeframe` — the strategy's primary timeframe
- `--timerange` — limit to test range (use `YYYYMMDD-` for open-ended)
- `--export trades` — save trade list for analysis
- `--export-filename` — custom output path

### Reading results — key metrics

| Metric | What it tells you |
|--------|-------------------|
| Tot Profit % | Is the strategy profitable? |
| Win% | Signal quality (25-40% is normal for trend-following) |
| Long / Short profit % | Split this — one side may be dragging the other down |
| Drawdown | Risk — >10% is dangerous without a filter |
| Max Consecutive Loss | Psychological pain threshold |
| Sharpe | Risk-adjusted return (>1 is good) |
| Avg Duration | How long you're exposed — longer = more risk time |

## Iterative Optimization Pattern

The most reliable pattern found in practice is a **3-pass refinement**:

### Pass 1: Baseline
- Implement the trader's raw idea as described
- Run backtest with default params
- Identify: is it losing on longs, shorts, or both?

### Pass 2: Trend filter
- If one direction is losing, add a higher-timeframe trend filter
- Daily EMA60 works well for 1h strategies
- Re-run, check if the losing direction improved

### Pass 3: Entry logic refinement
- Replace weak entry conditions with stronger ones
- For shorts: "bearish alignment" (smoothly descending MAs + no pullback) outperforms "cluster below MAs"
- For longs: "cluster + breakout above all MAs" works in uptrends

### Pass 4 (optional): Market mode switch
- Add a manual toggle for bear/bull market to force single-direction trading
- When unfiltered: disable the losing side entirely

### Pass 5: Smooth decline detection (V4 enhancement)
For short entries, add a "流畅下跌" (smooth decline) detector as an alternative to the strict bearish alignment:

```python
# 3-4 consecutive lower closes = smooth decline
smooth_period = 4
dataframe["lower_low"] = dataframe["close"] < dataframe["close"].shift(1)
dataframe["smooth_decline"] = (
    dataframe["lower_low"].rolling(window=smooth_period).min() >= 1
)
# Price below MA20 + MA20 sloping down
dataframe["below_ma20"] = dataframe["close"] < dataframe["sma20"]
dataframe["ma20_sloping_down"] = dataframe["sma20"] < dataframe["sma20"].shift(1)

# V4 comprehensive short signal
dataframe["v4_short_signal"] = (
    dataframe["bearish_aligned"]                    # strict bearish alignment
    | (
        dataframe["smooth_decline"]                 # OR smooth decline
        & dataframe["below_ma20"]
        & dataframe["ma20_sloping_down"]
        & dataframe["no_bounce_above_ma20"]
    )
)
```

This captures moves like ETH Jun 1-7 (2006→1552, -23%) where price keeps making lower lows without the 6 MAs being perfectly ordered.

### Tiger-Style Iteration (Real-World Case Study)

A common refinement path from user feedback (documented from a real session):

| Iteration | Change | Result |
|-----------|--------|--------|
| v1 | MA cluster + long/short both | −48.25 USDT (−4.82%), 26% win |
| v2 | + daily EMA60 trend filter | −8.74 USDT (−0.87%), 29.8% win |
| v3 | Short entry changed to bearish alignment + no-bounce | +14.37 USDT (+1.44%), 38.8% win |
| v4 | Bear-market mode (shorts only) | **+45.10 USDT (+4.51%), 56.2% win, 2.06% drawdown** |

Key insight: **the trend filter alone halved losses, but switching entry logic from "cluster below MAs" to "smooth bearish alignment + no bounce" made shorting profitable. Then disabling the losing direction entirely produced the best result.**

### Timeframe Sensitivity

The same strategy behaves very differently across timeframes. Always test on multiple:

| Timeframe | Total | Win% | Drawdown | Sharpe | Best For |
|-----------|-------|------|----------|--------|----------|
| **1h** | +4.51% / 32 trades | 56.2% | 2.06% | 2.28 | Balanced mix |
| **2h** | **+8.04% / 25 trades** | 44.0% | 5.37% | 3.21 | Smooth decline patterns |
| **4h** | **+9.79% / 12 trades** | **58.3%** | **1.39%** | **3.43** | Highest quality signals |

The 2h timeframe with V4 smooth decline detection captured a specific ideal pattern: ETH Jun 1-7 (2006→1552, -23%), where price made consistently lower lows on 2h candles with no bounce. This pattern is the user's preferred setup for the "V4 strategy."

**Guideline:** 4h produces the best risk-adjusted returns but fewer trades. 2h captures more opportunities with slightly higher drawdown. 1h is a middle ground. Start with the timeframe the user explicitly prefers, then benchmark others.



## Common Patterns to Recognize

### "均线密集" (MA Cluster) — good for LONG entries
All 6 MAs are within a tight % range. Price above all = breakout bullish signal.

**Implementation:**
```python
ma_cols = ["sma20", "sma60", "sma120", "ema20", "ema60", "ema120"]
ma_max = dataframe[ma_cols].max(axis=1)
ma_min = dataframe[ma_cols].min(axis=1)
dataframe["ma_spread"] = (ma_max - ma_min) / dataframe["close"]
dataframe["is_clustered"] = dataframe["ma_spread"] < 0.015
```

### "空头排列流畅" (Bearish Alignment) — good for SHORT entries
All MAs perfectly descending (longest > shortest) AND sloping down AND price stays below MA20.

**Implementation:**
```python
dataframe["bearish_ordered"] = (
    (dataframe["sma20"] < dataframe["sma60"])
    & (dataframe["sma60"] < dataframe["sma120"])
    & (dataframe["ema20"] < dataframe["ema60"])
    & (dataframe["ema60"] < dataframe["ema120"])
    & (dataframe["ema20"] < dataframe["sma20"])  # EMA faster than SMA = strong bear
)
# Slope check
for col in ma_cols:
    dataframe[f"{col}_down"] = dataframe[col] < dataframe[col].shift(1)
dataframe["all_slopes_down"] = ...  # AND all slope columns
# No bounce above MA20
recent_high = dataframe["high"].rolling(window=2).max()
dataframe["no_bounce"] = (recent_high < dataframe["sma20"]) & (recent_high < dataframe["ema20"])
```

## OKX API Issues (Python CCXT vs curl)

When Python CCXT times out connecting to OKX but curl works:

**Root cause:** Python's `urllib3`/`requests` library handles the HTTPS CONNECT through the proxy differently than libcurl. This is an environment-specific issue.

**Diagnostic:** Test API auth directly with curl:
```bash
# First check if OKX is reachable at all
curl -s --max-time 5 https://www.okx.com/api/v5/public/time

# Then test with authenticated endpoint using HMAC signature
python3 -c "
import subprocess, json, hmac, base64, time
ts = str(int(time.time()))
msg = ts + 'GET' + '/api/v5/account/balance' + ''
sign = base64.b64encode(hmac.new(secret.encode(), msg.encode(), 'sha256').digest()).decode()
cmd = ['curl', '-s', '--max-time', '8', '--proxy', 'http://127.0.0.1:7890',
  '-H', f'OK-ACCESS-KEY: {api_key}',
  '-H', f'OK-ACCESS-SIGN: {sign}',
  '-H', f'OK-ACCESS-TIMESTAMP: {ts}',
  '-H', f'OK-ACCESS-PASSPHRASE: {passphrase}',
  'https://www.okx.com/api/v5/account/balance']
result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
data = json.loads(result.stdout)
print(data.get('code'), data.get('msg'))
"
```

**Known error codes:**
- `"50111"` → `Invalid OK-ACCESS-KEY` — the API key was deleted from OKX or was never confirmed. The user needs to create a new API key on OKX.
- `"50113"` → Wrong passphrase
- `RequestTimeout` → Network issue (proxy/DNS). Try without proxy.

**Workaround for live trading:** The user runs `freqtrade trade` in their own terminal (CCXT works from their environment). Backtesting with local data files works fine (no live exchange connection needed).

**Proxy config pitfalls:**
- `ccxt_config: { httpProxy: "http://127.0.0.1:7890" }` gets silently dropped when `timeout` is also added. List both explicitly:
  ```yaml
  ccxt_config:
    httpProxy: "http://127.0.0.1:7890"
    timeout: 60000
  ```
- When `ALL_PROXY=socks5://...` is in env vars, Python's urllib3 may pick it up instead of `HTTP_PROXY`, causing hangs. Unset ALL_PROXY or set all to HTTP.

## References

- `references/six-ma-strategy.md` — Full implementation of the 6-MA cluster/bearish alignment strategy
- `references/dual-ma-crossover.md` — Dual MA crossover strategy (双均线交易系统) with parameter tuning guide
