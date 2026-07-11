# Twitter CLI Search Workflow

The `twitter` command (`twitter-cli` installed via pipx) provides X/Twitter search functionality **without requiring OAuth or Developer Portal credentials**. It uses an undocumented guest API.

## Basic Usage

```bash
# Search recent tweets (latest mode)
twitter search "crypto solana -is:retweet"

# Output is YAML format
# Keys: ok, schema_version, data (list of tweets with id and text)
```

## Parameters

| Query Syntax | Example | Effect |
|:-------------|:--------|:-------|
| `-is:retweet` | `solana -is:retweet` | Exclude retweets |
| `-is:reply` | `solana -is:reply` | Exclude replies |
| `$SYMBOL` | `$SOL` | Search for ticker mentions |
| `"phrase match"` | `"market maker"` | Exact phrase search |
| `from:user` | `from:cz_binance` | Tweets from specific user |
| `since:YYYY-MM-DD` | `since:2026-07-01` | Date filter |

## Integration with Execution

Twitter search output is YAML. Parse with Python for automated processing:

```bash
twitter search "solana meme -is:retweet -is:reply" | python3 -c "
import sys, yaml
data = yaml.safe_load(sys.stdin)
for t in data.get('data',[])[:5]:
    print(t.get('text','')[:200])
    print()
"
```

## When to Use vs Playwright

| Approach | Use Case | 
|:---------|:---------|
| `twitter search` ✅ | Cron jobs, periodic scans, keyword searches — **faster, no cookies needed** |
| Playwright | Full page interactions, logged-in features (timeline, likes, follows) |

## Cron Job Integration

For periodic X monitoring in cron jobs, use `twitter search` directly — no cookie injection needed:

```bash
# In a cron task:
twitter search "solana OR bsc OR meme -is:retweet"
```

This replaced the earlier Playwright+cookie-injection approach because:
1. No Chrome/Chromium dependency
2. No cookie extraction needed
3. Millisecond response vs multi-second browser launch
4. Works reliably in headless/background cron sessions

## Limitations

- **Read-only** — cannot post, like, retweet, or follow
- **Rate limited** — excessive queries may trigger temporary blocks (avoid > 1 request per 10 seconds)
- **No engagement metrics** — likes, retweets, reply counts not returned in basic search
- **Guest API** may be changed/deprecated by X without notice
