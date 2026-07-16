# YouTube Crypto Content Search via Playwright

## Purpose
Search YouTube for crypto-related tutorial/discussion videos and extract structured metadata without an API key. Useful when the user mentions a specific tutorial ("油管上有个视频说XXX") or asks about crypto content on YouTube.

## Technique

### Step 1: Search YouTube via Playwright

Navigate to YouTube search URL with the query:
```
https://www.youtube.com/results?search_query=KEYWORDS
```

Use URL-safe encoding for Chinese characters — Playwright handles this automatically via URL bar navigation.

### Step 2: Extract Video Data

```javascript
// Get all video titles and links
const videos = Array.from(document.querySelectorAll('a#video-title')).map(a => ({
  title: a.textContent.trim(),
  href: a.href,
  time: a.getAttribute('aria-label') || ''
}));

// Get visible text (includes descriptions, view counts, channel names)
const allText = document.body.innerText;
```

### Step 3: Read Video Details

Navigate to a specific video:
```
https://www.youtube.com/watch?v=VIDEO_ID
```

Then extract:
```javascript
// Description
document.querySelector('#description-inner')?.textContent

// Transcript via YouTube's built-in captions
// Note: extracting full transcripts requires navigating to CC/subtitles
```

## Common Search Queries

| Topic | Search Query |
|:------|:-------------|
| Hermes Agent Chinese tutorials | `Hermes Agent AI 自动化` |
| Crypto automation | `crypto trading bot AI automation` |
| BSC/Solana trading | `Solana meme coin sniper tutorial` |
| Chinese crypto edu | `币圈 链上 打狗 教学` |

## Limitations

- ❌ **Cannot automatically download videos** — the environment has no ffmpeg/youtube-dl
- ❌ **Cannot extract full transcripts reliably** — YouTube's transcript API is separate from the page DOM
- ❌ **youtubetranscript.com blocked** — YouTube actively blocks third-party transcript endpoints, returns "sorry, we're blocking us from fetching subtitles"
- ❌ **youtube-transcript-api pip package unusable** — v1.2.4 has incompatible API signatures vs documented examples; `YouTubeTranscriptApi.fetch()`/.list()/.get_transcript() methods all fail
- ❌ **Playwright cannot click transcript button** — YouTube's `转写文稿`/`Show transcript` tab exists in DOM but is `hidden` (display:none); Playwright strict mode + JavaScript click both fail
- ✅ **Can extract video metadata** — titles, view counts, channel names, descriptions
- ✅ **Can identify relevant videos** and point the user to them

## Pitfalls

- ⚠️ YouTube may show a cookie consent banner the first time — handle by checking for consent buttons or accept them
- ⚠️ Search results are often in the user's locale language — add English terms to get broader results
- ⚠️ Video descriptions may be truncated (YouTube limits visible description length on search results page)
