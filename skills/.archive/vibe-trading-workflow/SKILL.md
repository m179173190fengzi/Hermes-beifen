---
name: vibe-trading-workflow
description: Vibe-Trading 量化回测工具 — 自然语言策略开发、460+因子库、多市场回测
category: trading
---

# Vibe-Trading 量化研究工具

> 自然语言驱动的量化回测与策略开发系统

## 安装位置

```bash
~/vibe-venv/bin/vibe-trading   # pip install vibe-trading-ai 到 venv
```

版本 v0.1.11 | GitHub: HKUDS/Vibe-Trading (24.7k stars)

## 配置

配置存放在 `~/.vibe-trading/.env`：

```bash
DEEPSEEK_API_KEY=    # 从 Hermes config 提取
LANGCHAIN_MODEL_NAME=deepseek-v4-pro
DEEPSE---K_BASE_URL=https://api.deepseek.com/v1
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

运行前必须 export 环境变量才能用 LLM：

```bash
# 读取 .env 后加上 LANGCHAIN_MODEL_NAME
export DEEPSEEK_API_KEY="(从hermes config获取)"
export LANGCHAIN_MODEL_NAME=deepseek-v4-pro
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

参考脚本：`~/vibe-btc-test.sh`

## 可用功能

### 1. 自然语言回测（需 LLM 环境变量）

```bash
~/vibe-venv/bin/vibe-trading run -p "回测BTC双均线SMA20/60 crossover..."
~/vibe-venv/bin/vibe-trading chat     # 交互模式
```

AI 自动完成：写策略代码 → AST 语法验证 → 跑回测 → 输出 Sharpe/总收益/最大回撤/胜率

### 2. Alpha 因子库（无需 LLM）

```bash
~/vibe-venv/bin/vibe-trading alpha list
~/vibe-venv/bin/vibe-trading alpha list --zoo alpha101
~/vibe-venv/bin/vibe-trading alpha list --zoo gtja191
~/vibe-venv/bin/vibe-trading alpha list --zoo qlib158
```

4 个因子库共 460+ 因子：alpha101(101) + qlib158(158) + gtja191(191) + academic(10+)

因子 bench 需要 Tushare token（A 股 csi300 数据源），crypto 回测不受限。

### 3. 数据源可用性

| 数据源 | 需 KEY | 国内可用 |
|--------|--------|---------|
| yfinance | 否 | 是（走代理） |
| CCXT | 否 | 是（走代理） |
| AKShare | 否 | 是 |
| OKX API | 否（公开行情） | 是 |
| Tushare | 是 | 是（需注册） |

### 4. 其他命令

```bash
~/vibe-venv/bin/vibe-trading serve          # Web UI
~/vibe-venv/bin/vibe-trading connector list  # 券商列表
~/vibe-venv/bin/vibe-trading memory list     # 查看记忆
```

## 注意事项

- .env 中的 LANGCHAIN_MODEL_NAME 必须手动 export，source .env 不自动加载
- DeepSeek key 在 Hermes config 中以截断形式存储，需完整 API key
- crypto 回测走 yfinance/CCXT 不需要额外 token
- 回测 benchmark_return 是美股 SPY 基准，crypto 回测需自行解读
