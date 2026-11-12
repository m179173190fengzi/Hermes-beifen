# Reading Tweets Without X Auth (vxtwitter API)

When `xurl` auth is not set up (no app registered, no OAuth tokens), use the **vxtwitter** public API as a read-only workaround. No API key, no OAuth, no rate-limit registration needed for light use.

## Endpoint

```
https://api.vxtwitter.com/{username}/status/{tweet_id}
```

Example:
```
https://api.vxtwitter.com/IBuzovskyi/status/2077825355163803662
```

## Response Structure

```json
{
  "tweetID": "2077825355163803662",
  "user_name": "YanXbt",
  "user_screen_name": "IBuzovskyi",
  "text": "Tweet body text",
  "date": "Thu Jul 16 18:39:03 +0000 2026",
  "likes": 29,
  "retweets": 8,
  "replies": 1,
  "hasMedia": false,
  "mediaURLs": [],
  "media_extended": [],
  "hashtags": [],
  "possibly_sensitive": false,
  "article": {                           // ← X long-form articles appear here
    "title": "...",
    "preview_text": "...",
    "image": "https://pbs.twimg.com/media/..."
  },
  "qrt": null,                           // quoted tweet
  "retweet": null,
  "communityNote": null,
  "pollData": null
}
```

## Key Features

- **No auth required** — works without any X API credentials
- **X Articles** — long-form articles are captured in the `article` object with `title`, `preview_text`, and `image`
- **JSON output** — easy to parse programmatically
- **Media** — images, video, and GIFs in `mediaURLs[]` and `media_extended[]`
- **Quoted/retweeted content** — nested in `qrt`/`retweet` objects
- **Community notes** — `communityNote` field if present

## Limitations

- **Read-only** — cannot post, like, retweet, or DM
- **No auth-protected content** — private accounts, X articles behind login → only preview text, not full article body
- **No streaming/search** — only single-tweet lookup by ID
- **Unofficial** — could break if X changes their API

## Usage in agent

```python
import httpx

resp = httpx.get(f"https://api.vxtwitter.com/{username}/status/{tweet_id}", timeout=15)
data = resp.json()

text = data.get("text", "")
article = data.get("article", {})
title = article.get("title", "")
preview = article.get("preview_text", "")
```

## Alternative: fxtwitter

Same concept, different URL pattern:
```
https://api.fxtwitter.com/{username}/status/{tweet_id}
```
Returns similar JSON structure. Try as fallback if vxtwitter is down.
