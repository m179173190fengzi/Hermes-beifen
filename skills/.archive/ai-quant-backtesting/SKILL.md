---
name: ai-quant-backtesting
description: AI驱动的量化策略回测工作流 — 安装配置Vibe-Trading，编写signal engine，运行回测，解读结果。覆盖自然语言回测和直接Python回测两种模式。
category: trading
---

# AI Quant Backtesting Workflow

使用 Vibe-Trading 进行AI驱动的量化回测。

## 安装

```bash
python3 -m venv ~/vibe-venv
~/vibe-venv/bin/pip install vibe-trading-ai
# 需要代理时加 --proxy
```

## 配置

`~/.vibe-trading/.env`:

```
DEEPSEEK_API_KEY=sk-...
LANGCHAIN_MODEL_NAME=deepseek-v4-pro
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

关键：必须设置 `LANGCHAIN_MODEL_NAME`，否则preflight check会卡住。

## 两种回测模式

### 模式A：LLM驱动（自然语言）

```bash
~/vibe-venv/bin/vibe-trading run -p "回测BTC SMA20/SMA60双均线策略..."
```

**优点**：说人话就行，AI自动生成signal engine和config
**缺点**：
- LLM生成策略代码后写报告阶段容易超时（180s不够）
- 复杂策略LLM不一定写对
- 每次运行都要完整走LLM流程，慢

### 模式B：直接Python回测（推荐复杂策略）

自己写signal engine脚本，只依赖 `yfinance` + `pandas` + `numpy`：

```python
import yfinance as yf, pandas as pd, numpy as np

btc = yf.download('BTC-USD', start='2019-01-01', end='2025-01-01', interval='1wk')
# 处理MultiIndex
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = btc.columns.get_level_values(0)
# 计算指标
btc['SMA20'] = btc['Close'].rolling(20).mean()
# 遍历信号
for i in range(start_idx, len(btc)):
    # 入场逻辑 + 出场逻辑
    pass
```

**优点**：快（10-30s），完全可控，可以调试
**缺点**：需要手写逻辑

## 数据源

| 市场 | 工具 | 是否需要Key |
|------|------|:-----------:|
| Crypto | yfinance / ccxt | ❌ 免key |
| A股 | akshare / tushare | ❌ akshare免key / tushare需token |
| 美股 | yfinance | ❌ 免key |
| 港股 | yfinance | ❌ 免key |

## Alpha Zoo（Vibe-Trading内置因子库）

460个预构建因子，4个zoo：

```bash
# 列出因子
~/vibe-venv/bin/vibe-trading alpha list
~/vibe-venv/bin/vibe-trading alpha list --zoo alpha101
~/vibe-venv/bin/vibe-trading alpha list --zoo gtja191
~/vibe-venv/bin/vibe-trading alpha list --zoo academic
~/vibe-venv/bin/vibe-trading alpha list --zoo qlib158

# 因子bench（需要tushare token做A股）
~/vibe-venv/bin/vibe-trading alpha bench --zoo alpha101 --universe csi300 --period 2024-2025
```

## Pitfalls

### ⚠️ 时间周期选择直接影响策略有效性

- **周线**：SMA120需要120根K线≈2.3年初始化数据。数据源至少要回溯3年
- **日线**：V4的EMA20<SMA20条件只能在小周期触发，周线从不触发
- **4H/1H**：V4真正的工作频率
- **回测经验：V4只做4H级别回测**，日线/周线的EMA20<SMA20和smooth decline条件无法触发

### ⚠️ V4策略在周线/日线级别无效

**4H回测（2025-10 ~ 2026-07）：**
- 胜率: 50.0% | 利润因子: 2.76 | 总收益: +2.80%
- 4笔交易，两亏两赚，亏均1.61% vs 赚均4.43%

**周线回测（2022-2024）：**
- 完整V4条件（SMA排列+EMA20<SMA20+smooth decline）：0触发
- 简化版（仅SMA排列做空）：3笔交易，胜率0%，-3%
- **原因**：周线EMA20永远>SMA20（近期权重更高）；BTC周线平均震幅8-10% > smooth decline阈值6%；等SMA排列好时，熊市底部已过

**日线回测（2025-2026.7）：**
- 完整V4排列触发68天，但+smooth decline后0触发
- **原因**：2025年4月闪崩时段日线震幅6-10%（>1.5%阈值）；V型反转太快

**结论**：V4只能用于4H级别回测。大周期（日线/周线）只用来确认方向，不触发交易。这证实了"看大做小"原则。

### ⚠️ Smooth Decline阈值按时间框架校准

| 时间框架 | 波动率阈值 | 说明 |
|:--------|:---------:|:-----|
| 4H | 1.2% | ✅ V4最优频率 |
| 1H | 1.5% | 可用 |
| 15m | 2.0% | 短周期允许更大波动 |
| 日线 | 1.5% | 但EMA20<SMA20在日线几乎不触发 |

### ⚠️ yfinance MultiIndex列

`yfinance.download()` 返回的DataFrame在v0.1.5+有MultiIndex列名，需要：
```python
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = btc.columns.get_level_values(0)
```
否则列名是 `('Close', 'BTC-USD')` 而不是 `'Close'`。

### ⚠️ LLM驱动回测超时

`vibe-trading run` 在LLM生成策略后还要写报告，经常超时（180s不够）。复杂策略建议直接写Python脚本。

## 快速测试

```bash
# 验证安装
~/vibe-venv/bin/vibe-trading --version

# 验证LLM连接
~/vibe-venv/bin/python3 -c "
import urllib.request, json
req = urllib.request.Request('https://api.deepseek.com/v1/models')
req.add_header('Authorization', 'Bearer YOUR_KEY')
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
print(f'{len(data[\"data\"])} models available')
"
```

## 相关文件

| File | Description |
|------|-------------|
| `references/v4-weekly-case-study.md` | V4周线回测详细数据，证明周线V4无效的实证 |
