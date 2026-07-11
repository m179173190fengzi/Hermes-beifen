# X/Twitter Monitoring Setup

The user wants automated monitoring of X/Twitter for crypto trending topics, KOL shills, and hot narratives.

## Prerequisites: xurl CLI

The official X Developer Platform CLI tool. Installed from GitHub releases:

```bash
# Download Linux x86_64 binary
curl -sL "https://github.com/xdevplatform/xurl/releases/download/v1.2.2/xurl_Linux_x86_64.tar.gz" -o /tmp/xurl.tar.gz

# Extract and install
cd /tmp && tar -xzf xurl.tar.gz && chmod +x xurl && mv xurl ~/.local/bin/

# Verify
xurl --help
```

## User Setup (MUST be done by user, NOT by agent)

For security reasons, the agent cannot do the OAuth flow. The user must:

1. **Create X Developer Portal App** at https://developer.x.com/en/portal/dashboard
   - Name: anything (e.g., "hermes-monitor")
   - Set Redirect URI to `http://localhost:8080/callback`
   - App type: "Web App, automated app or bot"
   
2. **Copy Client ID and Client Secret** from Keys and Tokens page

3. **Register app and authenticate** (user runs these in their terminal):
   ```bash
   xurl auth apps add my-app --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
   xurl auth oauth2 --app my-app
   xurl auth default my-app
   ```

4. **Verify**:
   ```bash
   xurl auth status
   xurl whoami
   ```

## Useful Commands for Crypto Monitoring

### Search Trending Topics
```bash
# Search for hot crypto tokens/trends in Chinese + English
xurl search "solana coin trending" -n 20
xurl search "solana memecoin" -n 20
xurl search "bsc cz new coin" -n 20
xurl search "土狗 冲 solana" -n 15
```

### Check Specific KOL Activity
```bash
# Check a KOL's recent posts
xurl user @ansem
xurl user @cz_binance
xurl search "from:ansem" -n 10
```

### Follow Specific Users' Timelines
```bash
xurl user @ansem
xurl following --of ansem -n 20     # Who does this KOL follow?
```

## Cron Job Setup for Auto-Monitoring

Once xurl is authenticated, set up a cron job that periodically checks X for crypto trending topics:

```bash
# Sample search: find tokens being shilled with high engagement
xurl search "new coin solana" -n 20
xurl search "gm solana" -n 10
```

Pair with `hermes cronjob` action='create' for periodic runs.

## Known Issues

| Problem | Solution |
|---------|----------|
| Credits depleted / 403 | User needs to buy X API credits ($5+ min) in Developer Console → Billing |
| Rate limit (429) | Wait 15 min between searches on free tier |
| OAuth flow doesn't return to localhost | Re-run `xurl auth oauth2 --app my-app` with correct redirect URI |
