# 链上 TVL 监控（DeFiLlama）

用于定时任务中的链市纵览模块。

## API 端点

```bash
curl -s "https://api.llama.fi/chains"
```

返回所有链的TVL数据。从JSON中提取目标链：

```python
# 目标链在API中的命名
target_map = {
    'Solana': ['solana'],
    'BNB Chain': ['bnb chain', 'binance'],
    'Robinhood': ['robinhood'],
}
```

## 监控脚本

`/tmp/tvl_monitor.py` — 输出格式化TVL对比：
```
TVL对比 -- 2026-07-10 21:19

Solana           $   11.04B  ##
BNB Chain        $    6.79B  #
Robinhood        $  108.72M  #####

Solana / Robinhood = 102x
BNB / Robinhood    = 62x
```

## Cron job 用法

在定时任务prompt中加入：
```
用 `python3 /tmp/tvl_monitor.py` 获取三链TVL对比，解读资金流向
```
