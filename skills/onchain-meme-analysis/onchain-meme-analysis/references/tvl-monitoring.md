# 链上 TVL 监控（DeFiLlama）

用于定时任务中的链市纵览模块。

## API 端点

```bash
curl -s "https://api.llama.fi/v2/chains"
```

返回所有链的TVL数据。从JSON中提取目标链（注意v2端点中`tvlChange7d`/`tvlChange1d`字段）：

```python
# 目标链在API中的命名
target_map = {
    'Solana': ['solana'],
    'BSC': ['bsc', 'binance'],
    'Robinhood': ['robinhood'],
}
```

## 监控脚本（持久路径）

**脚本位置：`/home/wei/.hermes/scripts/tvl_monitor.py`**（勿放 /tmp！重启即清空，cron任务会静默失败）

输出：
```
RH: $361M | 7d +0.0% | 24h +0.0%
BSC: $4,883M | 7d +0.0% | 24h +0.0%
Solana: $4,804M | 7d +0.0% | 24h +0.0%
```

⚠️ **代理要求**：本机需走 FLClash 代理 `http://127.0.0.1:7890` 访问 DeFiLlama，脚本内置代理handler，失败自动回退直连。

## Cron job 用法

在定时任务prompt中加入：
```
用 `python3 /home/wei/.hermes/scripts/tvl_monitor.py` 获取三链TVL对比，解读资金流向
```

## 历史教训

- 2026-07-31：旧脚本在 `/tmp/tvl_monitor.py`，重启后丢失导致报告缺TVL板块 → 重建到 `~/.hermes/scripts/`（持久目录）
- 给 cron job 用的任何辅助脚本一律放 `~/.hermes/scripts/`，不要放 `/tmp`
