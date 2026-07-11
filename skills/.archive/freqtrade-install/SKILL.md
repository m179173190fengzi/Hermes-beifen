---
name: freqtrade-install
category: software-development
description: Install FreqTrade from source and configure FreqUI behind GFW — proxy workarounds, GitHub API rate-limit bypass, CLI syntax quirks, OKX futures config.
---

# FreqTrade Installation

Install and configure [FreqTrade](https://github.com/freqtrade/freqtrade) — the open-source crypto trading bot — from source in restricted-network environments (China/GFW).

## When to use

- User wants FreqTrade for OKX/Binance/Bybit automated trading
- Docker pull fails (Docker Hub blocked by GFW)
- `freqtrade install-ui` fails (GitHub API rate-limited)
- User needs to configure OKX futures (isolated margin, 做多/做空)

## Installation steps

### 1. Clone with proxy

```bash
git clone --depth 1 \
  -c http.proxy=http://127.0.0.1:7890 \
  -c https.proxy=http://127.0.0.1:7890 \
  https://github.com/freqtrade/freqtrade.git
```

### 2. Create venv & install deps

```bash
cd freqtrade
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run `setup.sh -i` is also an option but `pip install -r requirements.txt && pip install -e .` is more reliable when interrupted.

### 3. Create user data & config

```bash
freqtrade create-userdir --userdir ~/ft_userdata/user_data
freqtrade new-config --userdir ~/ft_userdata/user_data
```

### 4. Manual FreqUI install (when `install-ui` fails)

When `freqtrade install-ui` hits GitHub API rate limit (403):

```bash
# Find latest release tag
curl -sL "https://github.com/freqtrade/frequi/releases" | \
  grep -oP 'href="/freqtrade/frequi/releases/tag/[^"]+' | head -1

# Download zip
curl -sL "https://github.com/freqtrade/frequi/releases/download/<VERSION>/freqUI.zip" \
  -o /tmp/freqUI.zip

# Extract to UI directory
INSTALL_DIR="freqtrade/freqtrade/rpc/api_server/ui/installed"
unzip -o /tmp/freqUI.zip -d "$INSTALL_DIR"
echo "<VERSION>" > "$INSTALL_DIR/.uiversion"
```

### 5. Verify installation

```bash
freqtrade --version
freqtrade list-exchanges | grep -i okx
```

## OKX futures config template

Reference: `references/okx-futures-config.md`

Key settings for USDT-margined futures:
- `"trading_mode": "futures"`
- `"margin_mode": "isolated"` (逐仓, safer than cross)
- Pair format: `"BTC/USDT:USDT"` (spot: `BTC/USDT`)
- Proxy: `"ccxt_config": { "httpProxy": "http://127.0.0.1:7890" }`

## CLI syntax (2026.x)

In FreqTrade 2026.x dev, `-c/--config` and `--userdir` are **subcommand-level** flags, not global flags:

```bash
# ✅ Correct
freqtrade trade -c config.json --userdir ./user_data
freqtrade list-exchanges -c config.json

# ❌ Wrong — "invalid choice: 'config.json'"
freqtrade -c config.json trade
```

## PATH setup

Add to `~/.bash_aliases` or `~/.bashrc`:

```bash
export PATH="$HOME/bin:$PATH"
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

Create symlink:
```bash
ln -sf ~/freqtrade/.venv/bin/freqtrade ~/bin/freqtrade
```

## Pitfalls

- **Docker Hub blocked in China**: Don't fight it — use native Python install.
- **GitHub API rate limit**: FreqUI `install-ui` command uses the API (60 req/hr unauthenticated). When rate-limited, download the zip directly from the releases page.
- **`-c` flag placement**: In 2026.x dev branch, `-c` must come AFTER the subcommand. Check `freqtrade <cmd> --help` to confirm.
- **Interrupted setup.sh**: If `setup.sh -i` gets interrupted mid-pip, resume with `pip install -r requirements.txt && pip install -e .`.
- **Proxy env vars**: Docker daemon proxy needs `sudo` (systemd config). For pip/git/clone, set `HTTP_PROXY` in the shell or pass `-c http.proxy=` to git.

## Verification

```bash
freqtrade --version
freqtrade list-exchanges  # should show OKX (Supported)
freqtrade webserver -c config.json  # then curl http://127.0.0.1:8080/ -> 200 with HTML
```

## API credential verification

When ccxt proxy connections fail (timeouts with GFW), verify OKX API credentials directly with curl + HMAC-SHA256 signing:

```bash
# test_okx_auth.sh — reads creds from env vars
# Usage: OKX_KEY=xxx OKX_SECRET=*** OKX_PASS=xxx bash test_okx_auth.sh
PROXY="http://127.0.0.1:7890"
TS=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
sign_request() {
  local sig_str="${TS}${1}${2}${3}"
  echo -n "$sig_str" | openssl dgst -sha256 -hmac "$OKX_SECRET" | awk '{print $2}'
}

# Test: 账户余额
SIGN=$(sign_request "GET" "/api/v5/account/balance" "")
curl -s --connect-timeout 5 -x "$PROXY" \
  -H "OK-ACCESS-KEY: $OKX_KEY" \
  -H "OK-ACCESS-SIGN: $SIGN" \
  -H "OK-ACCESS-TIMESTAMP: $TS" \
  -H "OK-ACCESS-PASSPHRASE: $OKX_PASS" \
  "https://www.okx.com/api/v5/account/balance" | python3 -m json.tool
```

**Common OKX error codes**:

| Code | Message | Cause |
|------|---------|-------|
| 50111 | Invalid OK-ACCESS-KEY | API key doesn't exist or was deleted |
| 50113 | Invalid OK-ACCESS-SIGN | Wrong secret or signing error |
| 50114 | Invalid OK-ACCESS-TIMESTAMP | Clock skew > 30s from OKX time |
| 50001 | Parameter missing | Required field is empty |

**Python alternative** (reads from config file, avoids exposing creds in argv):

```python
import hmac, hashlib, base64, json, requests
from datetime import datetime, timezone

with open('user_data/config-okx.json') as f:
    cfg = json.load(f)['exchange']

ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
sig_str = f'{ts}GET/api/v5/account/balance'
sig = base64.b64encode(hmac.new(
    cfg['secret'].encode(), sig_str.encode(), hashlib.sha256
).digest()).decode()

r = requests.get('https://www.okx.com/api/v5/account/balance',
    headers={
        'OK-ACCESS-KEY': cfg['key'],
        'OK-ACCESS-SIGN': sig,
        'OK-ACCESS-TIMESTAMP': ts,
        'OK-ACCESS-PASSPHRASE': cfg['password'],
    },
    proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
)
print(r.json())
```

## Running in trade mode (background)

When running `freqtrade trade` in the background (e.g., as a systemd service or via `&`), stdout is typically buffered and invisible. Best practice: redirect all output to a log file.

### Startup script pattern

```bash
#!/bin/bash
# ~/ft_userdata/run_trade.sh
DIR="/home/wei/ft_userdata"
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

exec "$DIR/freqtrade/.venv/bin/freqtrade" trade \
    --strategy MyStrategy \
    -c "$DIR/user_data/config.json" \
    --userdir "$DIR/user_data" \
    -v \
    >> /tmp/freqtrade_trade.log 2>&1
```

Then start with `bash run_trade.sh &` and monitor with `tail -f /tmp/freqtrade_trade.log`.

### Strategy selection

- List available strategies: `freqtrade list-strategies -c config.json`
- The strategy class name from your `.py` file (not the filename) is the identifier used in `--strategy`.
- If the config has a `timeframe` field, it overrides the strategy class's `timeframe` attribute. Remove `timeframe` from the config if you want the strategy to control it.

### Common trade-mode pitfalls

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| No output for 30+ seconds | ccxt proxy config missing; FreqTrade hangs trying to reach OKX/Binance | Add `"httpProxy": "http://127.0.0.1:7890"` in `exchange.ccxt_config` |
| "Found no enter signals" repeating | Normal — strategy hasn't triggered yet | Check with `freqtrade show-trades` or FreqUI |
| Port 8080 conflict | A prior webserver or trade process is still bound | `kill -9 <PID>` before starting trade |
| Strategy not found | The `.py` file might have syntax errors | Check with `freqtrade list-strategies` |

### ccxt_config proxy requirement

The `exchange.ccxt_config` must contain the proxy explicitly **in addition to** any other keys:

```json
"exchange": {
    "name": "okx",
    "ccxt_config": {
        "httpProxy": "http://127.0.0.1:7890",
        "timeout": 60000
    }
}
```

If `httpProxy` is missing, FreqTrade will hang during market loading when behind a GFW proxy. The `timeout` key is automatically added by FreqTrade — do not remove it, but ensure `httpProxy` is listed alongside it.

## FreqUI webserver troubleshooting

### JWT secret key

FreqUI requires `jwt_secret_key` in the `api_server` config section. It must be **at least 32 characters** — shorter values cause a startup crash:

```
CRITICAL - Invalid configuration. Reason: 'xxx' is too short
Failed validating 'minLength' in schema['properties']['api_server']['properties']['jwt_secret_key']
```

Fix:
```json
"api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1",
    "listen_port": 8080,
    "username": "admin",
    "password": "your_password",
    "jwt_secret_key": "your32+characterLongSecretKeyHere"
}
```

### Port already in use

If port 8080 is occupied by a stale process, find and kill it:

```bash
ss -tlnp | grep 8080          # find PID
kill -9 <PID>                  # force kill
```

Then restart the webserver.

### Common login issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Login page loads but won't log in | Default/too-short `jwt_secret_key` | Set a 32+ char key |
| Port 8080 in use | Old process hanging | Kill and restart |
| Page loads slowly | Exchange API calls on startup | Normal — wait 10-15s on first load |
