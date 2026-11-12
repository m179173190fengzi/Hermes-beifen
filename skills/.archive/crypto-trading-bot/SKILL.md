---
name: crypto-trading-bot
category: devops
tags: [freqtrade, okx, futures, trading, automated-trading, crypto, low-time-investment, passive-monitoring]
triggers:
  - "install freqtrade"
  - "set up crypto trading bot"
  - "OKX 合约"
  - "automated trading"
  - "crypto trading bot setup"
  - "碎片化时间"
  - "低时间投入"
  - "上班族打狗"
linked_files:
  - references/okx-futures-config.md: OKX 合约配置文件模板说明
  - templates/freqtrade.sh: 便捷启动脚本
  - templates/sample-futures-strategy.py: 支持做空的 RSI 合约策略示例
  - templates/six-ma-cluster-strategy.py: 六均线密集交易系统
  - templates/low-time-crypto-approach.md: 碎片化时间用户打法指南（低时间投入+监控模式）
  - scripts/test-okx-connection.py: OKX API 凭证验证脚本
  - references/okx-atk-guide.md: OKX Agent Trade Kit 安装/认证/CLI速查/合约规格
description: Set up and configure automated cryptocurrency trading bots. Covers FreqTrade setup, OKX futures config, strategy authoring, backtesting, AND low-time-investment passive monitoring for users with limited screen time. Install guide with proxy workarounds for China/GFW.
---

# Crypto Trading Bot Setup (FreqTrade)

## Overview

FreqTrade — open-source crypto trading bot. Support OKX spot and isolated futures.

## Quick Install (Native Python — Preferred for China/GFW)

```bash
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --depth 1 https://github.com/freqtrade/freqtrade.git
cd freqtrade
HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 ./setup.sh -i
```

## CLI Syntax Note (FreqTrade 2026.x)

`-c` goes **after** subcommand:
```bash
freqtrade trade -c config.json
freqtrade backtesting -c config.json --strategy SampleStrategy
```

## Proxy Config

```json
{
  "exchange": {
    "name": "okx",
    "ccxt_config": {
      "httpProxy": "http://127.0.0.1:7890",
      "timeout": 60000
    }
  }
}
```

Both `httpProxy` AND `timeout` must be listed together — FreqTrade drops httpProxy when it adds its own timeout key.

## Low-Time-Investment Mode

For users with limited screen time (~10min/day) who want passive monitoring:

1. See `templates/low-time-crypto-approach.md` for the full playbook
2. Use GMGN trending + cron alerts for token discovery
3. Set cronjob for MC thresholds: `--min-marketcap 100000`
4. Only check results when alerts fire — no active screen-watching

## Signal-Only Monitoring

```bash
python3 -c "
import ccxt
okx = ccxt.okx({'httpProxy': 'http://127.0.0.1:7890'})
ticker = okx.fetch_ticker('BTC/USDT')
print(f'BTC: ${ticker[\"last\"]} | 24h: {ticker[\"percentage\"]:.1f}%')
"
```

## PATH Setup

```bash
mkdir -p ~/bin
ln -sf ~/ft_userdata/freqtrade/.venv/bin/freqtrade ~/bin/freqtrade
```

## Quick Reference

| Task | Command |
|------|---------|
| List exchanges | `freqtrade list-exchanges -c config.json` |
| Download data | `freqtrade download-data -t 5m --days 30 -c config.json` |
| Backtest | `freqtrade backtesting --strategy SampleStrategy -c config.json` |
| Start trade | `freqtrade trade -c config.json` |
| FreqUI | `freqtrade webserver -c config.json --userdir ./user_data` |

---

## Installation Details (Absorbed from freqtrade-install)

The `freqtrade-install` skill has been merged here. Below is the detailed install workflow for restricted-network environments.

### Manual Install (step-by-step, more reliable than `setup.sh`)

```bash
cd freqtrade
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

If `setup.sh -i` gets interrupted mid-pip, resume with the above.

### Create User Data & Config

```bash
freqtrade create-userdir --userdir ~/ft_userdata/user_data
freqtrade new-config --userdir ~/ft_userdata/user_data
```

### Manual FreqUI Install (when `install-ui` hits GitHub API rate limit 403)

```bash
# Find latest release tag
curl -sL "https://github.com/freqtrade/frequi/releases" | \
  grep -oP 'href="/freqtrade/frequi/releases/tag/[^\"]+' | head -1

# Download zip
curl -sL "https://github.com/freqtrade/frequi/releases/download/<VERSION>/freqUI.zip" \
  -o /tmp/freqUI.zip

# Extract to UI directory
INSTALL_DIR="freqtrade/freqtrade/rpc/api_server/ui/installed"
unzip -o /tmp/freqUI.zip -d "$INSTALL_DIR"
echo "<VERSION>" > "$INSTALL_DIR/.uiversion"
```

### Startup Script

See `templates/freqtrade-startup.sh` for a run script that logs to file.

### PATH Setup

```bash
mkdir -p ~/bin
ln -sf ~/freqtrade/.venv/bin/freqtrade ~/bin/freqtrade
```

---

## Strategy Development (Absorbed from freqtrade-strategy + freqtrade-strategy-dev)

The `freqtrade-strategy` and `freqtrade-strategy-dev` skills have been merged here.

### Workflow

1. **Skeleton** — single file `user_data/strategies/my_strategy.py` inheriting `IStrategy`:
   ```python
   INTERFACE_VERSION = 3
   can_short = True
   timeframe = "1h"
   stoploss = -0.02
   minimal_roi = {"0": 100.0}  # disable auto-ROI
   startup_candle_count = 200
   ```

2. **Indicators** (`populate_indicators`) — use `talib.abstract` (SMA/EMA), create boolean entry columns
3. **Multi-timeframe** via `merge_informative_pair` — slower TF merged into base
   ⚠️ **Suffix pitfall**: merged columns get `_{timeframe}` suffix (e.g. `bias_15m`)
4. **Entry** (`populate_entry_trend`) — clean conditions with `reduce(lambda a, b: a & b, ...)`
5. **Exit** (`populate_exit_trend` or `custom_exit`) — use `qtpylib.crossed_above/below`
6. **Backtest** — download BOTH timeframes' data, then `freqtrade backtesting -c config.json --strategy MyStrategy -i 1h`

### 均线密集 (MA Cluster) for LONG entries

```python
ma_cols = ["sma20", "sma60", "sma120", "ema20", "ema60", "ema120"]
ma_max = dataframe[ma_cols].max(axis=1)
ma_min = dataframe[ma_cols].min(axis=1)
dataframe["ma_spread"] = (ma_max - ma_min) / dataframe["close"]
dataframe["is_clustered"] = dataframe["ma_spread"] < 0.015
```

### 空头排列流畅 (Bearish Alignment) for SHORT entries

```python
dataframe["bearish_ordered"] = (
    (dataframe["sma20"] < dataframe["sma60"]) &
    (dataframe["sma60"] < dataframe["sma120"]) &
    (dataframe["ema20"] < dataframe["ema60"]) &
    (dataframe["ema60"] < dataframe["ema120"]) &
    (dataframe["ema20"] < dataframe["sma20"])
)
# + slope check + no bounce above MA20
```

### 流畅下跌 (Smooth Decline) — V4 enhancement

```python
smooth_period = 4
dataframe["lower_low"] = dataframe["close"] < dataframe["close"].shift(1)
dataframe["smooth_decline"] = (
    dataframe["lower_low"].rolling(window=smooth_period).min() >= 1
)
dataframe["below_ma20"] = dataframe["close"] < dataframe["sma20"]
dataframe["ma20_sloping_down"] = dataframe["sma20"] < dataframe["sma20"].shift(1)
```

### Iterative Optimization Pattern

The most reliable pattern is a **3-5 pass refinement**:

| Pass | Action | Typical delta |
|:----:|--------|:------------:|
| 1 | Baseline — implement raw idea | — |
| 2 | Add daily trend filter | Halves losses |
| 3 | Refine short entry logic | Turns profitable |
| 4 | Bear-market mode (shorts only) | Best result |
| 5 | Timeframe benchmark (1h vs 2h vs 4h) | 4h often best |

### Timeframe Sensitivity

| Timeframe | Win Rate | Profit | Verdict |
|:---------:|:--------:|:------:|:--------|
| ≤15m | 0-20% | Negative ❌ | Too noisy |
| 1h | 47-56% | +4-6% ✅ | Good |
| 2h | 44% | +8% ✅ | Good |
| **4h** | **58%** | **+9.8% 🏆** | **Best** |

### Key Strategy Development Pitfalls

- **NEVER change the user's specified MA parameters** (SMA20/60/120 + EMA20/60/120)
- **merge suffix**: `merge_informative_pair` adds `_{tf}` suffix — access as `bias_15m`, not `bias`
- **Bool column conflict**: Don't create `dataframe["enter_short"]` in `populate_indicators` — it will conflict with the later assignment in `populate_entry_trend`. Use a different name like `dataframe["v4_short"]`.
- **Pair confusion**: When user says "参考走势", confirm which pair (BTC not ETH). Default to BTC.
- **看大做小不是固定两个级别**: Not a fixed 15m→1m pattern. Start at higher TF, drill down flexibly.
- **Reference strategies stored under `references/`**:
  - `references/six-ma-strategy.md` — Full 6-MA strategy implementation with backtest results
  - `references/six-ma-cluster-strategy.md` — Abridged strategy reference
  - `references/dual-ma-crossover.md` — Dual MA crossover strategy

---

## OKX API Auth Verification (Absorbed from freqtrade-install)

When ccxt proxy connections fail (timeouts behind GFW), verify OKX API credentials directly:

### curl + HMAC-SHA256

```bash
PROXY="http://127.0.0.1:7890"
TS=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
SIGN=$(echo -n "${TS}GET/api/v5/account/balance" | openssl dgst -sha256 -hmac "$OKX_SECRET" | awk '{print $2}')
curl -s --connect-timeout 5 -x "$PROXY" \
  -H "OK-ACCESS-KEY: $OKX_KEY" \
  -H "OK-ACCESS-SIGN: $SIGN" \
  -H "OK-ACCESS-TIMESTAMP: $TS" \
  -H "OK-ACCESS-PASSPHRASE: $OKX_PASS" \
  "https://www.okx.com/api/v5/account/balance"
```

### Known OKX error codes

| Code | Message | Cause |
|------|---------|-------|
| 50111 | Invalid OK-ACCESS-KEY | API key was deleted or never confirmed |
| 50113 | Invalid OK-ACCESS-SIGN | Wrong secret or signing error |
| 50114 | Invalid OK-ACCESS-TIMESTAMP | Clock skew > 30s |
| 50001 | Parameter missing | Required field empty |

---

## FreqUI Webserver (Absorbed from freqtrade-install)

### JWT Secret Key

FreqUI requires `jwt_secret_key` ≥ 32 characters. Shorter values crash startup:
```
CRITICAL - Invalid configuration. Reason: 'xxx' is too short
```
Fix: set a 32+ char key in `api_server.jwt_secret_key`.

### Port Already in Use

```bash
ss -tlnp | grep 8080   # find PID
kill -9 <PID>
```

### Common Login Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Can't log in | Short/missing `jwt_secret_key` | Set 32+ chars |
| Port conflict | Stale process | Kill and restart |
| Slow page load | Exchange API calls on startup | Wait 10-15s |
