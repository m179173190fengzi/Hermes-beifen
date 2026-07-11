# SixMaClusterStrategy — Reference Strategy

A complete, backtested Freqtrade strategy using 6 moving averages (SMA20/60/120 + EMA20/60/120).

## Entry Logic

- **Long**: MA cluster (all 6 MAs converge within ~1.5%) + price above all MAs (disabled in bear market)
- **Short**: Bearish alignment OR smooth decline + price below all MAs + no bounce above MA20

## Trend Filter

- Daily EMA60 determines overall market direction
- Bear market mode toggle: force-disable all longs
- Multi-timeframe detection: checks 1h, 2h, 4h simultaneously

## Exit Logic

- Close long: price crosses below MA20 or EMA20
- Close short: price crosses above MA20 or EMA20
- Fixed take-profit at 8%

## Evolution (BTC+ETH, ~50 days, $1000 wallet)

| Version | Change | Profit | Win Rate | Drawdown |
|---------|--------|:------:|:--------:|:--------:|
| v1 | MA cluster + both directions | -4.82% ❌ | 26.1% | 6.67% |
| v2 | + Daily trend filter | -0.87% ⚠️ | 29.8% | 2.62% |
| v3 | Bearish alignment for shorts | +1.44% ✅ | 38.8% | 4.24% |
| v4 | Bear market mode (shorts only) | +4.51% ✅ | 56.2% | 2.06% |
| v4 (2h) | Same on 2h TF | +8.04% ✅ | 44.0% | 5.37% |
| **v4 (4h)** | **Same on 4h TF** | **+9.79% 🏆** | **58.3%** | **1.39%** |
| V4 multi-TF | 1h+2h+4h combined | +6.55% ✅ | 48.5% | 3.44% |

## Key Parameters

```python
cluster_threshold = 0.015       # 1.5% MA spread for cluster detection
confirm_bars = 2                # Confirm cluster for 2 candles
bearish_confirm_bars = 2        # Confirm bearish alignment for 2 candles
no_bounce_bars = 2              # Price hasn't bounced above MA20 for 2 candles
daily_trend_ema = 60            # Daily EMA period
bear_market_mode = True         # Disable all longs
leverage = 10                   # 10x
stoploss = -0.02                # 2% (20% margin at 10x)
```

## File Locations

- Strategy: `~/ft_userdata/user_data/strategies/six_ma_cluster.py`
- Config: `~/ft_userdata/user_data/config-okx.json`
- Data: `~/ft_userdata/user_data/data/okx/futures/`
