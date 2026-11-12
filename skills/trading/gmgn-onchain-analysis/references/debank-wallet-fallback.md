# DeBank Wallet Fallback (当GMGN持仓为空时)

## 问题

`gmgn-cli portfolio holdings` 对某些钱包返回空数组 `{"list":[]}`，即使钱包明显有钱（confirmed via BSCScan/DeBank / or `portfolio stats` 显示 `token_num > 0`）。

**已知表现：**
- BSC 钱包：GMGN holdings 返回空，但 DeBank 正确显示 $4,000+ 持仓
- 原因推测：GMGN 的 holdings 需要 critical auth（API key + private key），且私有key可能未绑定到该钱包地址；或 GMGN 索引不全

## 解决方案：DeBank 作为备用

### DeBank URL 格式
```
https://debank.com/profile/<0x_wallet_address>
```

### 从 DeBank 提取的数据

成功加载后，页面显示：
- 钱包总价值
- 按链分组持仓
- 每条持仓：token名、价格、数量、USD价值

### 解析方式

用 `browser_snapshot(full=true)` 获取页面文本快照。关键数据通常在 `<chain_name>` → token list 区域：

```
Token: $XXX
Price: $0.xxxxx
Amount: XXXX.XXXX
USD Value: $X,XXX.XX
```

### 局限性

- DeBank 有 Cloudflare 验证，有时会弹验证页（需重试或换 UA）
- DeBank 可能弹出"连接钱包"弹窗，需要 dismiss（点击 Reject）
- DeBank 数据更新有延迟（页面显示 "Data updated X secs ago"）
- DeBank 不显示已卖出/已完成交易的 P&L

## 何时使用

1. 用户问钱包为什么涨/为什么有钱 → 先跑 `gmgn-cli portfolio stats` 看总况
2. 如果 stats 显示 `token_num > 0` 但 `portfolio holdings` 返回空 → 走 DeBank 备用
3. 如果 stats 也空 → 钱包可能没有 GMGN 跟踪的活跃交易

## 案例

钱包 `0x7a848a5a8169aa6a2f603d056a749f924f504444`

| 数据源 | holdings | 总价值 |
|--------|----------|--------|
| GMGN portfolio holdings | `{"list":[]}` | N/A |
| GMGN portfolio stats | `token_num:20, total_cost:$29,534` | N/A (不显示当前价值) |
| DeBank | 7 tokens | $4,489 (BSC 98% + Base 2%) |
