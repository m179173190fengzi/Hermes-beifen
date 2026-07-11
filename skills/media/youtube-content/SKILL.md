---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs."
platforms: [linux, macos, windows]
---

# YouTube Content Tool

## When to use

Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video. Transforms transcripts into structured content (chapters, summaries, threads, blog posts).

Extract transcripts from YouTube videos and convert them into useful formats.

## Setup

```bash
pip install youtube-transcript-api
```

## Helper Scripts

`SKILL_DIR` is the directory containing this SKILL.md file.

### Primary: fetch_transcript.py (direct transcript)

Accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

### Fallback: fetch_metadata.py (oEmbed + page HTML)

When the transcript API is blocked (common on cloud IPs, behind GFW, or after rate-limits), use the metadata fallback to at least get the video title and description. Requires no pip dependencies (stdlib only).

```bash
# JSON with title + description
python3 SKILL_DIR/scripts/fetch_metadata.py "URL" [--proxy http://proxy:port]

# Plain text (title + author + description)
python3 SKILL_DIR/scripts/fetch_metadata.py "URL" --text-only

# Try yt-dlp with Chrome cookies as last resort
python3 SKILL_DIR/scripts/fetch_metadata.py "URL" --ytdlp-fallback
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Try fetch_transcript** with `--text-only --timestamps`. This is the primary method.
2. **If blocked** (IP block, 403, captcha, cloud provider detection): fall back to `fetch_metadata.py` with `--text-only --ytdlp-fallback`. This gives you the video title, author name, and description text, but NOT the full transcript.
3. **If metadata also fails**: try `fetch_metadata.py` without `--ytdlp-fallback` (uses oEmbed API + page HTML, which are lower-risk). oEmbed is nearly always available but only returns the title.
4. **Validate**: confirm the output is non-empty and in the expected language. If still empty, tell the user the video likely has transcripts disabled or is behind CAPTCHA.
5. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
6. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
7. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

### Detection: When to use fallback

- `youtube_transcript_api` raises `RequestBlocked` or `IPBlocked` — **use oEmbed fallback**
- Browser redirects to `google.com/sorry/index` (CAPTCHA) — **use oEmbed fallback**
- `yt-dlp` raises "Sign in to confirm you're not a bot" — **use oEmbed fallback**
- Invidious/Piped instances return 403 or empty data — **use oEmbed fallback**
- `urllib` raises HTTP 429 (Too Many Requests) — **wait 60s and retry with fetch_metadata**

### Working around IP bans (from youtube-transcript-api docs)

If you're on a cloud IP (AWS, GCP, Azure, etc.):
- Use a residential proxy or VPN
- Run the script from your local machine instead of the agent's cloud environment
- Use the oEmbed fallback (`fetch_metadata.py`) instead

## Error Handling

- **Transcript disabled / IP blocked / CAPTCHA**: fall back to `fetch_metadata.py` to get at least the title and description from oEmbed. If metadata also fails, tell the user the video is fully blocked (try from local browser, or provide a summary manually).
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `pip install youtube-transcript-api` and retry.
- **HTTP 429 (Too Many Requests)**: YouTube is rate-limiting your IP. Wait 60+ seconds before retrying. Use `fetch_metadata.py` in the meantime.
- **youtube_transcript_api v1.x API changes**: the API changed from `YouTubeTranscriptApi.get_transcript()` (v0.x) to `YouTubeTranscriptApi().fetch()` (v1.x). The bundled script uses v1.x. If the script fails with `AttributeError: module 'youtube_transcript_api' has no attribute 'YouTubeTranscriptApi'`, check the installed version.

## Downloading Videos with yt-dlp

When the user wants to download YouTube videos (including member-only/会员 content), use `yt-dlp`.

### Prerequisites

```bash
pip install yt-dlp  # or use system package manager
```

For JS challenge solving (required for most YouTube downloads in 2026+):
```bash
# Install via pip or use --remote-component ejs:github
# Node.js is required for JS challenge solving
which node  # should return a path
```

### Member-Only / 会员视频 Download

Member content requires the Chrome browser to be logged into a YouTube account that has the membership:

```bash
yt-dlp --remote-component ejs:github --cookies-from-browser chrome "VIDEO_URL" -o "output.mp4"
```

### Standard Download (with cookies for higher quality)

```bash
yt-dlp --cookies-from-browser chrome "VIDEO_URL" -o "output.mp4"
```

### Download Entire Playlist

```bash
yt-dlp --cookies-from-browser chrome --yes-playlist "PLAYLIST_URL" -o "%(playlist_index)s - %(title)s.%(ext)s"
```

### Key Flags

| Flag | Purpose |
|:-----|:--------|
| `--cookies-from-browser chrome` | Use Chrome cookies for member auth + higher quality |
| `--remote-component ejs:github` | Enable JS challenge solver (downloads solver from GitHub) |
| `--yes-playlist` | Download all videos in a playlist |
| `-f "bestvideo+bestaudio"` | Best quality (auto-merged) |
| `-f "best"` | Best single-file format (pre-merged, often worse quality) |

### Known Issues

- **JS challenge fails without EJS solver** — without `--remote-component ejs:github`, only "images are available for download"
- **Slow download** — yt-dlp on some connections can be slow; be patient
- **Member content only works if Chrome is logged into the paying account**
- **Output format will be `.webm`** for best quality (video+audio merged) - most players support this
