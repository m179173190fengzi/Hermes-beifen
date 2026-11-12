# OKX Agent Trade Kit (ATK) 配置与使用指南

> 将 OKX CEX 交易能力通过 CLI/MCP 接入 AI Agent（Hermes/Claude/Codex 等）。
> 安装时间：2026-07-14

---

## 一、安装

### 1.1 安装 CLI

```bash
npm i -g @okx_ai/okx-trade-cli
```

验证：`okx --version`

### 1.2 安装 OKX Skills（11个）

> ⚠️ `npx skills add okx/agent-skills` 有交互式选单，非交互环境会卡住。
> **替代方案：直接 clone + cp**

```bash
git clone --depth 1 https://github.com/okx/agent-skills.git /tmp/agent-skills
cp -r /tmp/agent-skills/skills/* ~/.hermes/skills/
```

11个 Skill 一览：

| Skill | 用途 | 需认证 |
|-------|------|:----:|
| `okx-cex-market` | 行情/深度/K线/资金费率/持仓量 | ❌ |
| `okx-cex-auth` | OAuth 认证流程 | — |
| `okx-cex-trade` | 现货/合约/期权/算法单下单 | ✅ |
| `okx-cex-portfolio` | 账户余额/持仓/盈亏/账单 | ✅ |
| `okx-cex-bot` | 网格/定投策略 | ✅ |
| `okx-cex-earn` | 简单赚币/双币赢/链上赚币 | ✅ |
| `okx-cex-smartmoney` | 1000+交易员聪明钱信号 | ✅ |
| `okx-sentiment-tracker` | 3万+KOL情绪聚合+新闻 | ✅ |
| `okx-cex-skill-mp` | 多角色Skill管理 | ✅ |
| `okx-outcomes` | 预测市场（世界杯等） | ✅ |
| `earn-hunter` | 7×24利率监控自动通知 | ✅ |

### 1.3 支持的站点

| 站点 | 参数值 | URL |
|------|:-----:|-----|
| Global | `global` | www.okx.com |
| EEA | `eea` | my.okx.com |
| US | `us` | app.okx.com |
| TR | `tr` | tr.okx.com |

---

## 二、认证（OAuth Device Flow）

### 2.1 前置检查

```bash
okx auth status --json     # 查看当前状态
okx config show --json     # 查看API Key配置（有API Key优先于OAuth）
```

### 2.2 设备授权（推荐，免API Key）

```bash
okx auth login --manual --site <global|eea|us|tr>
```

- `--manual` 模式：输出验证URL和验证码后立即返回（不阻塞）
- 把 `verificationUri` 和 `userCode` 给用户，让用户在浏览器授权
- 用户完成授权后，运行 `okx auth status --json` 验证

### 2.3 API Key 方式（传统）

```bash
okx config init
# 按提示选站点 → 是否模拟盘 → 输入 AK/SK/Passphrase
```

### 2.4 权限范围

OAuth 授权时可选权限：
- `demo:read` / `demo:trade` / `demo:asset_transfer` — 模拟盘
- `live:read` / `live:trade` — 实盘
- `market:read` — 行情数据（无需认证）

> ⚠️ 模拟盘和实盘是分开授权的，需分别授权。

### 2.5 管理

```bash
okx auth status --json    # 检查状态
okx auth logout            # 登出
okx auth install           # 安装/更新okx-auth二进制
```

---

## 三、CLI 命令速查

### 行情（无需认证）

```bash
# Ticker
okx market ticker BTC-USDT

# K线
okx market candles BTC-USDT --bar 1H --limit 50

# 深度
okx market orderbook BTC-USDT --sz 10

# 资金费率
okx market funding-rate BTC-USD-SWAP

# 合约规格
okx market instruments --instType SWAP --instId BTC-USDT-SWAP
```

输出字段：`ctVal`（合约面值）、`lotSz`（最小交易量）、`minSz`（最小下单量）、`tickSz`（最小价格变动）

### 合约交易（需认证，加 `--demo` 用模拟盘）

```bash
# 设杠杆
okx swap leverage --instId BTC-USDT-SWAP --lever 20 --mgnMode cross

# 开仓 (BTC-USDT-SWAP: ctVal=0.01, 650张=6.5 BTC)
okx swap place --instId BTC-USDT-SWAP --side sell --ordType market --sz 650 --tdMode cross

# 带止盈止损
okx swap place --instId BTC-USDT-SWAP --side sell --ordType market --sz 650 --tdMode cross \
  --tpTriggerPx 58000 --tpOrdPx -1 \
  --slTriggerPx 64000 --slOrdPx -1

# 查看持仓
okx swap positions BTC-USDT-SWAP

# 平仓
okx swap close --instId BTC-USDT-SWAP --mgnMode cross
```

### 账户（需认证）

```bash
okx account balance                  # 交易账户
okx account balance --demo           # 模拟盘余额  
okx account positions                # 持仓总览
```

### 聪明钱（需认证）

```bash
okx smartmoney traders-by-filter --sortBy pnl --period 30 --limit 20
okx smartmoney trader-positions --authorId <id>
```

### 情绪/新闻（需认证）

```bash
okx news latest --lang zh-CN --limit 10
okx news search --keyword "BTC" --sentiment bullish
```

### 事件合约/预测市场

```bash
okx event --help
```

---

## 四、合约规格速查（OKX）

| 合约 | ctVal | lotSz | minSz | tickSz |
|------|:-----:|:-----:|:-----:|:------:|
| BTC-USDT-SWAP | 0.01 BTC | 0.01 | 0.01 | 0.1 |
| ETH-USDT-SWAP | 0.1 ETH | 0.1 | 0.1 | 0.01 |
| SOL-USDT-SWAP | 1 SOL | 1 | 1 | 0.001 |

- **张数 × ctVal = 实际币数**（例：650张 × 0.01 = 6.5 BTC）
- 下单量以**张数**为单位，`--sz` 参数填张数
- 市价单有最大数量限制（超过报 sCode 51202）

---

## 五、常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `HTTP 403` | 权限不足 | 检查 OAuth scope 是否包含该模块 |
| `sCode 51202` | 市价单超最大量 | 减小 `--sz` |
| `posSide="short" only valid with mgnMode="isolated"` | 全仓不需要posSide | 去掉 `--posSide` |
| `Failed to spawn okx-auth` | 二进制损坏 | `okx auth install` |
| `No config found` | 未初始化 | `okx config init` 或 `okx auth login` |
| `Session expired` | Token过期 | 重新 `okx auth login --manual` |

---

## 六、推荐组合打法

```
Alpha简报  →  okx-sentiment-tracker (情绪) + okx-cex-smartmoney (聪明钱)
链上扫描  →  GMGN (链上) + okx-cex-market (CEX数据交叉验证)
开仓执行  →  okx-cex-trade (合约/现货)
持仓管理  →  okx-cex-portfolio (盈亏追踪)
零钱管理  →  okx-cex-earn + earn-hunter
预测市场  →  okx-outcomes (世界杯等)
```

> 注：ATK 主要覆盖 CEX（中心化交易所）数据。链上 meme 币打狗仍需 GMGN/OKX DEX 套件。
