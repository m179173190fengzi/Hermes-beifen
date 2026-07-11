# Gemini Vision Configuration for Gateway Image Pre-Analysis

The Hermes Gateway can pre-analyze images sent by users using an auxiliary vision provider. By default, `auxiliary.vision.provider` is `auto`, which fails if no vision-capable API key is configured.

## Quick Setup

```bash
# 1. Configure the provider and model
hermes config set auxiliary.vision.provider google
hermes config set auxiliary.vision.model gemini-2.0-flash

# 2. Set the API key (two ways, choose one):
# Option A — in config.yaml:
hermes config set auxiliary.vision.api_key "your-gemini-api-key"

# Option B — in .env:
echo 'GEMINI_API_KEY=your-gemini-api-key' >> ~/.hermes/.env

# 3. Restart gateway
systemctl --user restart hermes-gateway
```

## Verification

Send an image to the gateway. If it works, the gateway log will show:

```
INFO gateway.run: Image routing: text (mode=text). Pre-analyzing 1 image(s) via vision_analyze.
```

Followed by a description of the image content in the agent's prompt.

## Known Issues

### API Key Truncation
When using `hermes config set auxiliary.vision.api_key`, the shell may interpret parts of the key. Make sure the full key is passed as a quoted string. Keys with special characters (`$`, `!`, backticks) need single quotes.

### Key Not Found in .env
If configured via `auxiliary.vision.api_key` in config.yaml, the Google provider may still fail silently. The Gemini provider typically looks for `GEMINI_API_KEY` in `.env`. Add it there as well:

```bash
echo 'GEMINI_API_KEY=your-full-key-here' >> ~/.hermes/.env
```

### Gateway Restart Required
Config changes are read at gateway startup. `hermes config set` writes to disk but the running process doesn't hot-reload — restart is mandatory:
```bash
systemctl --user restart hermes-gateway
```

### Silent Failure Mode
If `auxiliary.vision.provider` is `auto` and no vision provider is available, the gateway still routes images as text, but the prompt won't contain the image description. The user sees: "I couldn't quite see it this time." No ERROR in logs, just silence.

Check which providers are configured:
```bash
grep -A 5 "auxiliary:" ~/.hermes/config.yaml
```

## Pitfalls

- **Free tier limits.** Gemini 2.0 Flash has generous free quota (60 requests/minute). Still, hitting limits will cause silent failures.
- **Model compatibility.** `gemini-2.0-flash` supports vision. Older Gemini models may not. `gemini-2.5-flash-preview-tts` (for TTS) doesn't support vision.
- **Image size.** Gateway caches images to `~/.hermes/image_cache/`. Very large images (>10MB) may time out during download.
