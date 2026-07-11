# DexScreener API — Solana 代币交叉搜索

GMGN CLI 按名称搜索需要先知道合约地址。DexScreener 按名称/符号搜索适合做**代币发现与交叉验证**。

## 按名称/符号搜索

```bash
curl -s --proxy http://127.0.0.1:7890 \
  "https://api.dexscreener.com/latest/dex/search?q=SULTAN" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import json,sys
d=json.load(sys.stdin)
pairs=d.get('pairs',[])
pairs.sort(key=lambda p: float(p.get('volume',{}).get('h24',0) or 0), reverse=True)
for p in pairs[:5]:
    b=p.get('baseToken',{})
    q=p.get('quoteToken',{})
    print(f\"{b.get('symbol','?')}/{q.get('symbol','?')}\")
    print(f\"  Address: {b.get('address','?')}\")
    print(f\"  Price: \${p.get('priceUsd','?')}\")
    print(f\"  Chg 1h: {p.get('priceChange',{}).get('h1','?')}% 6h: {p.get('priceChange',{}).get('h6','?')}%\")
    print(f\"  Vol 24h: \${p.get('volume',{}).get('h24','?')}\")
    print(f\"  Liq: \${p.get('liquidity',{}).get('usd','?')}\")
    print(f\"  FDV: \${p.get('fdv','?')}\")
    print(f\"  Dex: {p.get('dexId','?')}\")
    print()
"
```

## 应用于代币集群分析

当多个同名代币同时出现（如"苏丹/Sultan"集群）：

```
# 关键分析维度：
1. 按成交量排序 → 找出最活跃的池子
2. 检查流动性/市值比 → liq < $20K 对 $1M+ 市值是高危信号
3. 检查涨幅 → 1h +300% 以上通常是 pump 盘
4. 检查创建时间 → 同一批创建说明有组织撒网
5. 检查 DEX 类型 → pumpswap = pump.fun 相关, meteora = 正规 DEX
```

## 结合 GMGN CLI 做深度分析

DexScreener 做完发现后，拿到合约地址用 GMGN 看详情：

```bash
# 深度分析
gmgn-cli token info --chain sol --address <合约地址>
gmgn-cli token holders --chain sol --address <合约地址>
gmgn-cli token security --chain sol --address <合约地址>
gmgn-cli market signal --chain sol --address <合约地址>
```

## 限制

- DexScreener 不返回持有人分布、安全审计等链上细节 → 需要 GMGN 补充
- 搜索结果可能包含垃圾代币 → 按成交量/流动性筛选
- 某些新创建的代币可能需要几分钟才会出现在 DexScreener
- q 暂不支持中文名称搜索
