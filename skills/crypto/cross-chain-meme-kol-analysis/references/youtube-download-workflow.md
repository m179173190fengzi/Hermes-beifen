# YouTube Video Download (yt-dlp) Workflow

`yt-dlp` is installed via pipx. Downloads YouTube videos including member-only content if Chrome has a logged-in YouTube session with active membership.

## Basic Public Video Download

```bash
yt-dlp --cookies-from-browser chrome \
  -f "bestvideo+bestaudio" \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  -o "/path/to/output.mp4"
```

## Member-Only Video Download

Requires Chrome with logged-in YouTube account that has membership to the target channel:

```bash
yt-dlp --remote-component ejs:github \
  --cookies-from-browser chrome \
  -f "bestvideo+bestaudio" \
  "https://www.youtube.com/watch?v=MEMBER_VIDEO_ID" \
  -o "/path/to/output.mp4"
```

## Prerequisites

```bash
# Install EJS challenge solver
yt-dlp --remote-component ejs:github

# Install secretstorage for cookie decryption
pip install secretstorage
```

## Error Handling

| Error | Cause | Fix |
|:------|:------|:-----|
| `n challenge solving failed` | Missing EJS solver | Run `--remote-component ejs:github` first |
| `Requested format is not available` | JS challenge blocked | Retry with `--remote-component ejs:github` |
| `cookie decryption failed` | Missing secretstorage | `pip install secretstorage` |
| YouTube blocking API | Anti-bot update | Upgrade yt-dlp: `pipx upgrade yt-dlp` |

## Limitations

- YouTube JS challenges change frequently; may break after updates
- **No transcript extraction** — transcript APIs blocked by YouTube; `youtube-transcript-api` package incompatible with Python 3.14
- Download speed varies (1-15 MiB/s) due to YouTube throttling
