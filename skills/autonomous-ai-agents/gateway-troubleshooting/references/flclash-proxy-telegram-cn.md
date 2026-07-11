# FLClash + Telegram Gateway in China

## Context

Session 2026-06-24: User diagnosed why Telegram bot wasn't responding.
FLClash (FlClashCore) was running as the proxy client on this system.

## FLClash Process Discovery

```bash
ps aux | grep -i clash
# → /usr/bin/FlClash (GUI)
# → /usr/share/FlClash/FlClashCore /tmp/FlClashSocket_6239.sock (core)

ss -tlnp | grep clash
# → LISTEN 0 4096 127.0.0.1:7890
```

FLClash uses Clash Meta kernel. Default mixed proxy port is **7890**
(HTTP + SOCKS5 on the same port).

## Proxy Config for Gateway

Added to `~/.hermes/.env`:

```
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:7890
```

## Log Progression

1. Before extras fix:
   `Platform 'Telegram' requirements not met (pip install 'hermes-agent[telegram]')`

2. After extras fix, before proxy:
   `telegram connect timed out after 30s`
   `DoH discovery yielded no usable IPs (system DNS: 208.43.237.140)`

3. After proxy configured (expected, not observed in this session):
   `[Telegram] Connected`

## FlClash Config Structure

**Config root:** `~/.local/share/com.follow.clash/`

| Path | Purpose |
|------|---------|
| `config.yaml` | Core Clash config: ports, mode, merged proxies from active sub |
| `profiles/<id>.yaml` | Expanded subscription profile (full proxy list + rules) |
| `shared_preferences.json` | Flutter app prefs: autoLaunch, autoRun, theme, window props |
| `database.sqlite` | SQLite: `profiles` table stores sub URL, label, expiry, traffic |
| `cache.db` | BoltDB: GEO data cache |

**Query subscription URLs from database.sqlite:**

```bash
python3 -c "
import sqlite3
con = sqlite3.connect('/home/wei/.local/share/com.follow.clash/database.sqlite')
cur = con.cursor()
for row in cur.execute('SELECT id, label, url, auto_update FROM profiles'):
    print(f'{row[1]}: {row[2]} (auto_update={row[3]})')
"
```

## FlClash Auto-Start on Boot

Requires **both** steps:

### 1. System autostart `.desktop` file

Create `~/.config/autostart/FlClash.desktop`:

```
[Desktop Entry]
Type=Application
Name=FlClash
GenericName=FlClash
Exec=FlClash
Icon=FlClash
Categories=Network;
X-GNOME-Autostart-enabled=true
```

### 2. FlClash internal auto-launch flag

Modify `~/.local/share/com.follow.clash/shared_preferences.json` — set `autoLaunch: true` and `autoRun: true` under `appSettingProps`:

```bash
python3 -c "
import json
with open('/home/wei/.local/share/com.follow.clash/shared_preferences.json','r') as f:
    data = json.load(f)
c = json.loads(data['flutter.config'])
c['appSettingProps']['autoLaunch'] = True
c['appSettingProps']['autoRun'] = True
data['flutter.config'] = json.dumps(c, ensure_ascii=False)
with open('/home/wei/.local/share/com.follow.clash/shared_preferences.json','w') as f:
    json.dump(data, f, ensure_ascii=False)
print('done')
"
```

Without step 2, the .desktop file starts FlClash GUI but the proxy core may not auto-connect to the subscription.

## Key Insight

The `reconnection watcher` retries automatically every ~30s, so even
if the gateway starts without a proxy configured, adding proxy + restarting
(as opposed to waiting for retry) is the right fix.
