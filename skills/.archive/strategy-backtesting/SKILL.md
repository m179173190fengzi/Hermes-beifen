---
name: strategy-backtesting
description: 量化策略回测 — 用自然语言工具（Vibe-Trading等）做策略研究、因子分析、回测验证。配合V4策略和GMGN链上信号使用。
category: trading
---

# 策略回测工作流

> 覆盖工具：Vibe-Trading（自然语言回测）、TradingView Pine Script（导出）、自定义Python回测

## 安装

```bash
# 方式一（推荐）：venv隔离安装
python3 -m venv ~/vibe-venv
~/vibe-venv/bin/pip install vibe-trading-ai

# 方式二（pipx遇到大依赖超时用venv）
pipx install vibe-trading-ai  # 注意：依赖多可能超时
```

## LLM Provider 配置

Vibe-Trading 需要用LLM驱动自然语言回测。支持的provider（部分）：

| # | Provider | Env Key | 国内可用 |
|---|----------|---------|---------|
| 1 | DeepSeek | `DEEPSEEK_API_KEY` | ✅ |
| 2 | DashScope/Qwen | `DASHSCOPE_API_KEY` | ✅ |
| 3 | OpenRouter | `OPENROUTER_API_KEY` | 需代理 |
| 4 | Ollama（本地） | 无 | ✅ |

### 配置方法

创建 `~/.vibe-trading/.env`：

```bash
mkdir -p ~/.vibe-trading
cat > ~/.vibe-trading/.env << 'EOF'
DEEPSEEK_API_KEY=sk-xxx
EOF
```

然后验证：
```bash
~/vibe-venv/bin/vibe-trading version
```

## Alpha Zoo（460个因子）

Vibe-Trading 内置4个因子库，无需API即可查看：

```bash
# 列出所有因子（展示前50）
~/vibe-venv/bin/vibe-trading alpha list

# 按库筛选
~/vibe-venv/bin/vibe-trading alpha list --zoo alpha101
~/vibe-venv/bin/vibe-trading alpha list --zoo gtja191
~/vibe-venv/bin/vibe-trading alpha list --zoo qlib158
~/vibe-venv/bin/vibe-trading alpha list --zoo academic
```

### 因子库说明

| Zoo | 数量 | 来源 | 适用市场 |
|-----|------|------|---------|
| **qlib158** | 158 | Microsoft Qlib | 股票/ETF |
| **alpha101** | 101 | Kakushadze 2016 (arXiv:1601.00991) | 股票/ETF |
| **gtja191** | 191 | 国泰君安 2014 短周期因子 | A股为主 |
| **academic** | 10 | Fama-French 5 + Carhart + Amihud等 | 股票/加密货币 |

### 因子Bench

```bash
# 需要Tushare token做A股，格式：--period YYYY-YYYY
# 例：bench alpha101 在沪深300上
~/vibe-venv/bin/vibe-trading alpha bench --zoo alpha101 --universe csi300 --period 2024-2025

# Crypto数据走yfinance/CCXT免key
```

## 自然语言回测

配好LLM provider后，使用交互模式：

```bash
~/vibe-venv/bin/vibe-trading chat
```

然后在对话中输入自然语言描述策略，例如：
- "回测BTC双均线策略，SMA20和SMA60，2023-2025年数据"
- "测试V4 bearish alignment策略在BTC上的表现"
- "帮我对比alpha101_001到alpha101_010在crypto上的IC"

### 无LLM的回测方法

也可以直接使用Vibe-Trading的Python API（需要熟悉其模块结构）：
```python
from backtest import run_backtest
from data.loader import DataLoaderRegistry
# 详见Vibe-Trading官方文档
```

## Web UI

```bash
~/vibe-venv/bin/vibe-trading serve
```
然后浏览器打开 `http://localhost:8000`。

## 与现有系统的对接

| 已有系统 | Vibe-Trading 角色 |
|---------|-----------------|
| V4策略脚本 | ✅ 用Vibe-Trading回测V4策略的历史表现 |
| GMGN链上打狗 | ❌ Vibe-Trading不做链上meme（互补） |
| 10分制评分系统 | ✅ 461个因子可当额外数据源 |
| OKX CEX下单 | ✅ 支持OKX broker connector + guardrails |

## 数据源（免Key可用）

| 数据源 | 覆盖市场 | Key要求 |
|--------|---------|---------|
| yfinance | 美股、加密货币(BTC-USD等) | 无 |
| CCXT | 加密货币(Binance/OKX等) | 无（公开数据） |
| AKShare | A股、期货 | 无 |
| Tushare | A股、因子数据 | 需注册token |

## Pitfalls

- ⚠️ **pipx install可能超时** — Vibe-Trading依赖多（~200个），venv方式更稳
- ⚠️ **alpha bench需要Tushare token做A股** — 但crypto数据走yfinance/CCXT免key
- ⚠️ **init命令是交互式的** — 无法在后台直接跑，需要手动输入或直接写.env
- ⚠️ **period格式严格** — `YYYY-YYYY` 或 `YYYY-MM-DD/YYYY-MM-DD`，不要用逗号或斜杠
- ⚠️ **450+因子大部分为股票设计** — crypto回测需注意因子是否适用
- ⚠️ **国内访问GitHub/PyPI需代理** — 安装时设置 `--proxy http://127.0.0.1:7890`

## 参考文件

| 文件 | 说明 |
|------|------|
| `references/vibe-trading-setup.md` | Vibe-Trading v0.1.11 安装记录和验证步骤 |
