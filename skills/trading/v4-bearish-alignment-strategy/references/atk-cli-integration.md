# V4 策略 · OKX ATK CLI 集成

> 通过 OKX Agent Trade Kit CLI 实时检测 V4 看跌排列信号，无需启动 Freqtrade。

## 前置条件

| 组件 | 安装命令 |
|------|---------|
| ATK CLI | `npm i -g @okx_ai/okx-trade-cli` |
| OKX Skills | `npx skills add okx/agent-skills` → 安装全部11个 |
| OAuth 授权 | `okx auth login --manual --site global` → 浏览器登录授权 |

## 策略脚本

```bash
# 技能目录内运行（推荐）
python3 ~/.hermes/skills/trading/v4-bearish-alignment-strategy/scripts/v4-check-signals.py
```

### 脚本检测逻辑

1. 同时扫描 **4H / 1H / 15m** 三个周期
2. 提取各周期收盘价，计算 SMA20/60/120 + EMA20/60/120
3. 检测 **看跌排列** 条件：
   - SMA20 < SMA60 < SMA120
   - EMA20 < EMA60 < EMA120
   - EMA20 < SMA20（短期动量向下）
4. 只分析不下单（READ-ONLY 安全设计）

## ATK CLI 快速参考

| 功能 | 命令 |
|------|------|
| 查BTC现价 | `okx market ticker BTC-USDT` |
| 查K线 | `okx market candles BTC-USDT-SWAP --bar 1H --limit 150` |
| 开空单 | `okx swap place --instId BTC-USDT-SWAP --side sell --ordType market --sz <张数> --tdMode cross` |
| 设杠杆 | `okx swap leverage --instId BTC-USDT-SWAP --lever 20 --mgnMode cross` |
| 查持仓 | `okx swap positions BTC-USDT-SWAP` |
| 查看情绪 | `okx news latest --coins BTC --lang zh-CN --limit 5` |
| 聪明钱多空比 | `okx smartmoney traders-by-filter --sortBy pnl --period 7 --limit 5 --json` |

### 合约规格

BTC-USDT-SWAP: ctVal=0.01（每张=0.01 BTC）, minSz=0.01, lotSz=0.01

### 开仓公式

```
保证金 = 账户余额 × 仓位比例（如1/3）
张数 = (保证金 × 杠杆) / (BTC价格 × 0.01)
```

### 交易模式切换

| 模式 | 用法 |
|------|------|
| 模拟盘 | 所有命令加 `--demo` |
| 实盘 | 不加参数 |


### 安全注意事项

- 脚本只分析不执行 —— 不下单
- ATK 不支持提币（安全设计）
- ATK 不支持跨链桥
- 每次下单前必须用户明确确认

### WSL 环境注意

| 问题 | 原因 | 解决 |
|------|------|------|
| ATK CLI 安装 | npm 在 WSL 可直接安装 | `npm i -g @okx_ai/okx-trade-cli` |
| ATK Skills | WSL 安装 Hermes Skills | `npx skills add okx/agent-skills`（交互式选全部11个） |
| 代理到Telegram | WSL 的 127.0.0.1 是 WSL 不是 Win | 用 `ip route` 查 Win 网关 IP 代替 127.0.0.1 |
| 实盘授权 | OAuth一次只能选demo或live | 先 `okx auth logout`，再 `okx auth login --manual --site global`，授权时选实盘权限 |

### 已知限制与陷阱

| 问题 | 原因 | 解决 |
|------|------|------|
| 市价单超限 `sCode 51202` | 单笔市价单有最大合约数限制 | 减小 `--sz` 重试，市价单不可拆分批次 |
| 实盘需要双授权 | OAuth一次只能选demo或live | 先 `okx auth logout`，再 `okx auth login --manual --site global`，授权时选实盘 |
| `hermes config get` 不可用 | Win版 Hermes 不支持 `get` 子命令 | 用 `hermes config show` 查看 |
| Ubuntu 24.04 pip报 `externally-managed-environment` | PEP 668 限制 | 用 `pipx install` 代替 `pip3 install` |
| ATK 无策略引擎 | ATK只提供数据和下单CLI，无K线分析能力 | 配合 v4-check-signals.py 使用
