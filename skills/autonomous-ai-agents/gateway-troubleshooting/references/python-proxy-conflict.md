# Python Proxy Compatibility with Gateway

## Symptom

- `curl -s --proxy http://127.0.0.1:7890 https://api.telegram.org` works fine
- `freqtrade list-pairs` (Python/CCXT) connects slowly or times out
- Python `requests.get(url, proxies={'https': 'http://127.0.0.1:7890'})` hangs
- Gateway logs show: `connect timed out after 30s, next retry in Ns`

## Root Cause

The host has **conflicting proxy environment variables**:

| Variable | Value | Source |
|----------|-------|--------|
| `HTTP_PROXY` | `http://127.0.0.1:7890` | `.env` or system |
| `ALL_PROXY` | `socks5://127.0.0.1:7890` | `.env` or system |

Python's `urllib3` resolves the proxy chain differently than libcurl:
- **curl** uses `HTTP_PROXY` directly via `--proxy` flag → works
- **Python** reads `HTTP_PROXY`, then `HTTPS_PROXY`, then `ALL_PROXY` → when `ALL_PROXY=socks5` is set, tries SOCKS5 which the Clash mixed port handles, but the Python SOCKS handler (`PySocks` if installed, or plain http if not) may interact poorly with the proxy's protocol detection.

Additionally, `HTTP_PROXY=http://...` + `HTTPS_PROXY=http://...` + `ALL_PROXY=socks5://...` creates a **protocol mismatch** — the HTTP/HTTPS proxy vars point to an HTTP CONNECT proxy, while ALL_PROXY expects a SOCKS5 protocol. Python's proxy resolution order can pick the wrong one.

## Fix

**Option A:** Unset conflicting env vars before the Python command

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
# Then run your Python command
python3 your_script.py
```

**Option B:** Set all three to the same HTTP proxy:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
unset ALL_PROXY  # key: don't leave SOCKS5 set
```

**Option C:** Use curl as a subprocess from Python (curl handles the proxy reliably):

```python
import subprocess, json
result = subprocess.run(['curl', '-s', '--max-time', '10', 
    '--proxy', 'http://127.0.0.1:7890',
    'https://api.telegram.org/bot<TOKEN>/getMe'],
    capture_output=True, text=True, timeout=15)
data = json.loads(result.stdout)
```

## Detection

```bash
# Check if env vars are conflicting
env | grep -i proxy | sort

# Test Python's proxy behavior
python3 -c "
import os
for k in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:
    v = os.environ.get(k)
    if v: print(f'{k}={v}')
"
```

## When This Matters

- Any Python-based tool that needs to reach Telegram/Discord/OKX APIs through a proxy
- CCXT-based trading bots (FreqTrade, etc.) — backtest works (local data), but live `freqtrade trade` needs exchange connection
- Hermes auxiliary client connections through the proxy

## OKX-Specific: Timeout Even Without Proxy

Even after unsetting all proxy env vars, Python CCXT may still time out connecting to OKX:

```
ERROR - Could not load markets, therefore cannot start.
```

This happens because CCXT loads ALL market types (SPOT, SWAP, FUTURES, etc.) at startup, and some endpoints return large responses that take longer than the default 10s CCXT timeout.

**Fix — increase CCXT timeout in config.json:**

```json
"ccxt_config": {
    "timeout": 60000
}
```

**Key distinction:** `freqtrade backtesting` works fine without exchange connection (uses local data files). `freqtrade trade` (even dry_run) needs the exchange connection for market structure data.

**Verification that the API itself is reachable:**

```bash
# Direct (no proxy) — works from China
curl -s https://www.okx.com/api/v5/public/time
# → {"code":"0","msg":"","data":[{"ts":"..."}]}

# Via curl with proxy
curl -s --proxy http://127.0.0.1:7890 -H "OK-ACCESS-KEY: $KEY" \
  https://www.okx.com/api/v5/account/balance
```
