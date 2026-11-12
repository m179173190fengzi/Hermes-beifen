# DeepSeek 401 Authentication Troubleshooting

## Symptom

```
⚠️ API call failed (attempt 1/3): AuthenticationError [HTTP 401]
   🔌 Provider: deepseek  Model: deepseek-v4-flash
   🌐 Endpoint: https://api.deepseek.com/v1
   📝 Error: HTTP 401: Authentication Fails, Your api key: ****9599 is invalid
```

## Diagnostic Flow

### 1. Check error key suffix vs config api_key suffix

```bash
grep 'api_key' ~/.hermes/config.yaml
```

Compare the last 4 chars in the error (`****9599`) against each api_key in config.

### 2. Identify the mismatch

If the error key suffix **doesn't match** `model.api_key` but **does match** another provider's key (`providers.<name>.api_key`), you have a credential cross-wire — `.env` likely has the wrong key in the main provider's env var.

### 3. Verify runtime env var

```bash
echo "${#DEEPSEEK_API_KEY}"  # 0 = empty
echo "${DEEPSEEK_API_KEY: -4}"  # last 4 chars
```

### 3b. Verify actual file content (bypass tool truncation)

`read_file`, `grep`, and `hermes config` ALL **truncate/sanitize** API keys for display. You may see `sk-236...f0ef` in tool output when the actual file contains the full `sk-REDACTED`. Use `xxd` to see the real bytes:

```bash
sed -n '5p' ~/.hermes/config.yaml | xxd | head -3
```

Decode the hex — if the hex columns show the full 35-character key (`sk-` + 32 hex chars), the file is correct and the display truncation is a security feature, not a data loss issue.

This is critical when the error says one key suffix but config display shows another — the config might be fine and the issue is only the `.env` override.

### 3c. `hermes config set` also truncates its confirmation

```bash
$ hermes config set model.api_key sk-REDACTED
✓ Set model.api_key = sk-236...f0ef in /home/wei/.hermes/config.yaml
```

The confirmation message truncates the key — **don't confuse this with a failed write**. The actual file content IS the full key. Verify with `sed -n '5p' ~/.hermes/config.yaml | xxd`.

### 4. After fixing keys, must /reset the session

Even after both `config.yaml` and `.env` have the correct key, the **running session's environment** is sourced at session start. Changes to `.env` are invisible to the current session. The user must run `/reset` or `/new` for the new env vars to be loaded.

This is why you can fix the key but the session still shows 401 on retry — it's using the env from session start.

### 5. Use Python/httpx for a clean API test (bypasses Hermes credential routing)

Hermes's own credential abstraction layer makes it hard to tell if the raw key works. Test the key directly:

```python
import httpx
resp = httpx.get(
    "https://api.deepseek.com/v1/models",
    headers={"Authorization": "Bearer <key>"},
    timeout=10
)
print(resp.status_code, resp.text[:200])
```

- HTTP 200 with model list (`deepseek-v4-flash`, `deepseek-v4-pro`, etc.) = key is valid
- HTTP 401 = key is expired, revoked, or belongs to a different API provider

### 6. Root cause

The `.env` file contains `DEEPSEEK_API_KEY=<wrong_key>` which **overrides** the `model.api_key` value in `config.yaml`. The model section fetches `api_key` first from environment variable, falling back to config value — so a stale `.env` entry takes priority over config.

## Fix

**Option A — Update config with correct key (preferred):**
```bash
hermes config set model.api_key <valid_deepseek_key>
```
Then `/reset` the session.

**Option B — Remove the stale env var, rely on config value:**
```bash
# Edit .env to remove or comment out the DEEPSEEK_API_KEY line
# Then the config.yaml's model.api_key will be used instead
```

**Option C — If the wawa/relay path was being used for auxiliary tasks, verify the relay key is still valid too:**
Test the relay provider's key directly with Python/httpx against its own endpoint.

## Common Scenarios

| Error key suffix | Config key match | Likely cause |
|-----------------|-----------------|--------------|
| Matches `model.api_key` | Same key | Key is expired/revoked — get a new one |
| Matches a different `providers.*.api_key` | Different key | `.env` has wrong `DEEPSEEK_API_KEY` value |
| Doesn't match any key in config | Unknown key | Stale `.env` entry from a previous provider |

## Prevention

When setting up a new relay provider (e.g., WAWA ZZ), **always check** after configuration that the `.env` file hasn't been overwritten:

```bash
grep DEEPSEEK ~/.hermes/.env
```

The `DEEPSEEK_API_KEY` in `.env` should match the main DeepSeek key, not any relay provider's key.

After any provider change, always test with Python/httpx directly and then do `/reset`.
