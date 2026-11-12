# Vibe-Trading v0.1.11 安装记录

> 安装日期：2026-07-18 | 机器：Bot A (Ubuntu 26.04)

## 环境

- Python 3.14 (系统自带)
- 代理：127.0.0.1:7890 (FLClash)
- 目标目录：`~/vibe-venv/`

## 安装命令

```bash
python3 -m venv ~/vibe-venv
~/vibe-venv/bin/pip install --proxy http://127.0.0.1:7890 vibe-trading-ai
```

## 验证

```bash
~/vibe-venv/bin/vibe-trading --version
# → vibe-trading 0.1.11

~/vibe-venv/bin/vibe-trading alpha list
# → 460 alphas across 4 zoos
```

## 可用命令

| 命令 | 用途 |
|------|------|
| `vibe-trading chat` | 交互模式（自然语言回测） |
| `vibe-trading alpha list` | 列出因子库 |
| `vibe-trading alpha bench` | 因子性能bench |
| `vibe-trading serve` | 启动Web UI |
| `vibe-trading run` | 单次prompt运行 |
| `vibe-trading init` | 交互式配置（LLM provider等） |
| `vibe-trading connector` | 交易broker连接管理 |

## 配置

`~/.vibe-trading/.env` 需手动创建，格式：
```
DEEPSEEK_API_KEY=sk-...
```

## 已知问题

- `init` 为交互命令，后台运行会EOFError
- `alpha bench` 需要Tushare token做A股universe
- crypto数据走yfinance/CCXT免key
