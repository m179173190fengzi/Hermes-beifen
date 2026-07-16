# V4 策略 + OKX ATK CLI 执行集成

> 策略文件：`~/v4-strategy.py` | CLI：`okx` (ATK v1.3.9) | 创建：2026-07-14

## 一句话

用 Python 脚本包装 `okx market candles` 获取K线数据 → 计算6条均线 → 检测看跌排列 → 条件满足时输出信号。可手动跑或接入 cron。

## V4 策略核心

- 6条均线固定：SMA20/SMA60/SMA120 + EMA20/EMA60/EMA120
- 看跌排列：SMA20 < SMA60 < SMA120 且 EMA20 < EMA60 < EMA120 且 EMA20 < SMA20
- 平滑下跌：连续lower highs + lower lows，单根K线振幅 < 1.5%
- 熊市只做空，参考走势默认BTC
- 出场：价格突破MA20

## 数据源

```bash
# 获取K线数据传给策略
okx market candles BTC-USDT-SWAP --bar 4H --limit 150

# 当前价格
okx market ticker BTC-USDT
```

## 执行流程

```python
# 核心逻辑（~/v4-strategy.py 中的关键步骤）
1. fetch_candles(timeframe, limit=150)    # → [[close, high, low], ...]
2. sma(closes, period) / ema(closes, period)  # → 6个MA值
3. check_alignment(mas)                    # → (True/False, 原因)
4. check_smooth_decline(candles)           # → (True/False, 原因)
5. 多时间框架分析（4H → 1H → 15m 看大做小）
```

## 手动触发

```bash
python3 ~/v4-strategy.py
```

## 常见市场状态判断

| 4H 排列 | 1H 排列 | 判断 |
|---------|---------|------|
| ❌ SMA20 > SMA60 | 任何 | 不在熊市排列，不操作 |
| ✅ 看跌排列 | ✅ 看跌排列 | 强空头，可入场 |
| ✅ 看跌排列 | ❌ EMA20 > SMA20 | 大周期空但小周期反弹，等反弹结束再入 |
| 任何 | ✅ 价格在全部均线上方 | 短期偏多，不做空 |

## 注意事项

- CLI K线输出带表头/分隔线，脚本需过滤 `Environment`、`time`、`---` 行
- `okx market candles` 默认走实盘数据，不受demo/live模式影响
- 计算 EMA 需要足够历史数据（SMA120需要至少120根K线，4H需要20天）
- 脚本不包含自动下单逻辑——只输出信号，由用户决定是否执行
