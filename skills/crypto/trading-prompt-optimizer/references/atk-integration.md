# OKX Agent Trade Kit 集成参考

> 安装日期：2026-07-14 | 版本：okx-trade-cli@1.3.9
> 授权方式：OAuth 2.0 Device Flow | 站点：global | 模拟盘权限

## 一句话

ATK 是 OKX 的开源交易工具集，通过自然语言驱动 AI Agent 完成从研究到执行的整个交易流程。支持 MCP 和 CLI 两种接入。已通过 Hermes 技能包接入，`okx` CLI 已全局安装。

## 安装备忘

```bash
# 1. 安装技能包（11个技能）
npx skills add okx/agent-skills

# 2. 安装 CLI
npm install -g @okx_ai/okx-trade-cli

# 3. OAuth 授权（device flow，非交互模式）
okx auth login --manual --site global
# → 返回 verificationUri + userCode，在浏览器打开授权

# 4. 验证
okx auth status --json                  # 确认 logged_in
okx market ticker BTC-USDT              # 确认行情可查
```

## 11个Skills索引

| Skill | 用途 | 需要Auth |
|-------|------|---------|
| `okx-cex-market` | 行情/K线/持仓量/资金费率 | ❌ 公开数据 |
| `okx-sentiment-tracker` | 3万+KOL情绪聚合 + 新闻 | ✅ |
| `okx-cex-smartmoney` | 1000+实名交易员信号/排行榜/持仓 | ✅ |
| `okx-cex-trade` | 现货/合约/期权/算法单 | ✅ |
| `okx-cex-portfolio` | 账户余额/持仓/盈亏/账单 | ✅ |
| `okx-cex-earn` | 简单赚币/双币赢/链上赚币 | ✅ |
| `okx-cex-bot` | 网格/定投/马丁格尔策略 | ✅ |
| `earn-hunter` | 7×24利率监控自动通知 | ✅ |
| `okx-outcomes` | 世界杯预测市场 | ✅ |
| `okx-cex-auth` | OAuth授权/登录/登出 | - |
| `okx-cex-skill-mp` | 多角色skill管理 | ✅ |

## CLI 常用命令速查

### 行情数据（无需鉴权）

```bash
# 最新价格
okx market ticker BTC-USDT

# 批量行情（SPOT/SWAP/FUTURES/OPTION）
okx market tickers SWAP

# K线（支持 1m/3m/5m/15m/30m/1H/2H/4H/6H/12H/1D/1W/1M）
okx market candles BTC-USDT --bar 4H --limit 10

# 盘口深度
okx market orderbook BTC-USDT --sz 5

# 交易对列表
okx market instruments --instType SPOT

# 资金费率
# 用 market candles 查资金费率：instId=BTC-USDT-SWAP, bar=8H
```

### 新闻与情绪

```bash
# 最新新闻（默认英文，可指定平台和语言）
okx news latest --coins BTC,ETH,SOL --lang zh-CN --limit 10

# 重要新闻
okx news important --coins BTC,ETH --lang zh-CN

# 按代币搜新闻
okx news by-coin --coins BTC --importance high --lang zh-CN

# 关键词搜索
okx news search --keyword "CZ" --lang zh-CN

# 文章详情
okx news detail <id> --lang zh-CN
```

### 聪明钱信号

```bash
# 交易员排行榜（按Pnl/胜率/回撤筛选）
okx smartmoney traders-by-filter --sortBy pnl --period 30 --minWinRate 0.6 --limit 10

# 单个交易员详情
okx smartmoney performance-by-trader --authorIds <id>

# 交易员当前持仓
okx smartmoney trader-positions --authorId <id>
```

### 组合与账户

```bash
# 账户余额
okx account balance

# 当前持仓
okx account positions

# 账单历史
okx account bills

# 资金划转
okx account transfer
```

### 交易执行

```bash
# 市价单
okx spot order --side buy --sz 100 --szUnit quoteccy --instId BTC-USDT

# 限价单 + 止盈止损
okx spot order --side buy --px 62000 --sz 0.01 --instId BTC-USDT \
  --tpTriggerPx 65000 --tpOrdPx 64900 \
  --slTriggerPx 60000 --slOrdPx 59900

# 永续合约开多
okx swap order --side buy --posSide long --sz 10 --instId BTC-USDT-SWAP

# 查询挂单
okx spot orders-pending
```

## Alpha简报集成方案

ATK 的数据可以直接替代/增强现有 Alpha 合成简报的数据源：

| Alpha 简报阶段 | 原方案 | ATK 替代 |
|---------------|--------|---------|
| 行情概览 | DexScreener | `okx market ticker BTC-USDT` |
| 链上扫描 | GMGN | ATK无链上meme数据，保留GMGN |
| 情绪分析 | 推文搜索 | `okx news sentiment` + `okx sentiment-tracker` |
| 聪明钱 | Twitter KOL | `okx smartmoney traders-by-filter` |
| 宏观日历 | 无 | ATK 套件5（需实盘权限） |

**混合策略**：链上数据走 GMGN，CEX 行情+情绪+聪明钱走 ATK，推特分析走 `twitter search`。三路交叉验证。

## 注意事项

- `market:read` 权限无需登录即可调用
- demo 模式（模拟盘）只能做模拟交易，涨跌和实盘不一样
- **OAuth 授权页需手动选择 demo/实盘权限**，默认可能是模拟盘。两者可以累加（不需要撤销旧的重新选），`okx auth status --json` 的 `scopes` 字段会同时包含两种。如需实盘，重新跑 `okx auth login --manual --site global` 选实盘即可
- `okx config init` 是 API Key 配置向导，不是 OAuth — 两种鉴权方式互斥
- CLI 报错 `StorageNotFoundError` 时重新运行 `okx auth login --manual`
- 中国区网络可能需要代理，已在 env 配置 `http_proxy=http://127.0.0.1:7890`

## 合约交易备忘

### BTC-USDT-SWAP 规格

| 参数 | 值 |
|------|-----|
| 合约乘数 (ctVal) | 0.01 BTC/张 |
| 最小交易量 (minSz) | 0.01 |
| 步长 (lotSz) | 0.01 |
| 报价最小变动 (tickSz) | 0.1 |

### 开仓张数计算

```python
张数 = (保证金 × 杠杆) / (BTC价格 × 0.01)
# 例: 20,493 USDT × 20x / ($62,561 × 0.01) ≈ 655张
```

### 常见错误

| 错误码 | 原因 | 修复 |
|--------|------|------|
| 51202 | 市价单超限 | 减张数重试。市价单有单笔限额，分批或改限价单 |
| `posSide="short" is only valid with mgnMode="isolated"` | 全仓模式不需要posSide | 去掉 `--posSide` 参数 |

### 杠杆设置

```bash
# 全仓
okx swap leverage --instId BTC-USDT-SWAP --lever 20 --mgnMode cross

# 逐仓（需指定方向）
okx swap leverage --instId BTC-USDT-SWAP --lever 20 --mgnMode isolated --posSide short
```
