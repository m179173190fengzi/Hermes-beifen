# V4 回测方法论

> 从2026-07-18全流程实测提炼。Vibe-Trading + 直接Python脚本两种方式均可。

## 核心发现：V4只能跑4H级别

| 时间周期 | V4排列触发 | +Smooth Decline | 结论 |
|---------|:----------:|:--------------:|:----:|
| 周线 | 罕见（2022年11月出现过） | 0%（周线震幅8-10%，阈值6%过不了） | 不可用 |
| 日线 | 可以（2025年4月68天触发） | 0%（闪崩日线震幅6-10%，阈值1.8%过不了） | 不可用 |
| **4H** | **有效（10个月270根）** | **22根双条件触发，4笔实际交易** | **✅ 正确周期** |

## EMA20 < SMA20 条件

这是V4最重要的过滤条件，但只在≤4H级别有效：

- **周线**：EMA20永远在SMA20上方（EMA权重偏向近期价格，周线级别价格趋势性太强）
- **日线**：熊市拐点附近偶有触发，但BTC日线EMA20恢复速度比SMA20快得多
- **4H**：EMA20 < SMA20在下跌趋势中能稳定触发

## Smooth Decline 波动率阈值

```
条件: avg_range(最后10根K线) / 当前收盘价 < 阈值
```

| 周期 | 阈值 | BTC典型值 | 结论 |
|:----|:---:|:---------:|:----:|
| 周线 | 6% | 8-10% | ❌ 太严格 |
| 日线 | 1.5% | 2-10%（4月闪崩）| ❌ 恐慌时不过 |
| 4H | 1.2% | 0.5-1.5%（趋势中） | ✅ 有效 |

## 实测结果（BTC 2025-10 ~ 2026-07 · 4H）

```
总收益率:   +2.80%
胜率:       50.0%
平均盈利:   4.43%
平均亏损:   1.61%
利润因子:   2.76
交易次数:   4
```

- 胜率50%但利润因子2.76 → 亏的时候亏得少，赚的时候赚得多（可持续特征）
- 最大回撤34.97%（持仓期间浮亏，不是本金亏损）

## Vibe-Trading 使用要点

**安装：**
```bash
pipx install vibe-trading-ai
# 或 venv:
python3 -m venv ~/vibe-venv && ~/vibe-venv/bin/pip install vibe-trading-ai
```

**配置：** `~/.vibe-trading/.env` 需要 `DEEPSEEK_API_KEY` + `LANGCHAIN_MODEL_NAME`

**重要的坑：**
- `vibe-trading run -p "..."` 依赖LLM生成策略代码，大型回测容易超时（180s不够）
- 实际回测引擎很快（10秒内），但LLM写报告慢
- **推荐方案**：直接写Python信号引擎（参考 `~/v4-4h-backtest.py`），用CCXT获取4H数据
- `vibe-trading chat` 交互模式比 `run` 模式更好用，可以逐步调试

**数据源优先顺序：**
1. CCXT（币安直连，支持4H/多年代理，需要7890代理）
2. yfinance（只能日线及以上，4H不支持）
3. Vibe-Trading自带加载器（OKX/yfinance/CCXT）

## 数据获取（CCXT 4H）

```python
import ccxt, pandas as pd
binance = ccxt.binance({'proxies': {'https': 'http://127.0.0.1:7890'}})
candles = binance.fetch_ohlcv('BTC/USDT', '4h', since=timestamp_ms, limit=1000)
# 逐页获取，返回 [timestamp, open, high, low, close, volume]
```
