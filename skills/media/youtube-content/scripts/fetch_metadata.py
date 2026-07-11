#!/usr/bin/env python3
"""
Fallback: Fetch YouTube video metadata (title, description) when transcript APIs are blocked.

Uses the oEmbed API which requires no auth and works from most networks.
Also tries to extract the description from the YouTube page HTML as a second fallback.

Usage:
    python fetch_metadata.py <url_or_video_id> [--text-only]

Output (JSON):
    {
        "title": "...",
        "description": "...",
        "author_name": "...",
        "video_id": "...",
        "source": "oembed"
    }

No pip dependency required (uses stdlib only).
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def extract_video_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    patterns = [
        r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def fetch_oembed(video_id: str, proxy: str = None) -> dict:
    """Fetch video metadata from YouTube oEmbed API."""
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)"
    })
    opener = urllib.request.build_opener()
    if proxy:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({
                'http': proxy,
                'https': proxy,
            })
        )
    with opener.open(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return {
            "title": data.get("title", ""),
            "author_name": data.get("author_name", ""),
            "author_url": data.get("author_url", ""),
            "thumbnail_url": data.get("thumbnail_url", ""),
            "video_id": video_id,
            "source": "oembed",
        }


def fetch_page_description(video_id: str, proxy: str = None) -> str:
    """Try to extract description from YouTube page HTML."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })
    opener = urllib.request.build_opener()
    if proxy:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({
                'http': proxy,
                'https': proxy,
            })
        )
    try:
        with opener.open(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            # Try meta description
            m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
            if m:
                return m.group(1)
            # Try og:description
            m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


def fetch_with_ytdlp(video_id: str) -> dict:
    """Try yt-dlp with cookies from browser."""
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'yt_dlp',
             '--cookies-from-browser', 'chrome',
             '--skip-download',
             '--print', '%(title)s|||%(description)s',
             f'https://www.youtube.com/watch?v={video_id}'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.split('|||', 1)
            return {
                "title": parts[0].strip() if parts else "",
                "description": parts[1].strip() if len(parts) > 1 else "",
                "video_id": video_id,
                "source": "yt-dlp",
            }
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube video metadata")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--text-only", action="store_true",
                        help="Output plain text (title + description) instead of JSON")
    parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"),
                        help="HTTP proxy (default: $HTTP_PROXY)")
    parser.add_argument("--ytdlp-fallback", action="store_true",
                        help="Try yt-dlp with Chrome cookies as final fallback")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)

    # Step 1: oEmbed (fastest, lowest chance of being blocked)
    try:
        meta = fetch_oembed(video_id, args.proxy)
    except Exception as e:
        print(f"oEmbed failed: {e}", file=sys.stderr)
        meta = {"title": "", "author_name": "", "video_id": video_id, "source": "oembed"}

    # Step 2: Try to get description from page HTML
    description = ""
    try:
        description = fetch_page_description(video_id, args.proxy)
    except Exception:
        pass
    meta["description"] = description

    # Step 3: yt-dlp fallback (if requested)
    if args.ytdlp_fallback and (not meta["description"] or not meta["title"]):
        yt_data = fetch_with_ytdlp(video_id)
        if yt_data:
            if not meta["title"] and yt_data.get("title"):
                meta["title"] = yt_data["title"]
            if not meta["description"] and yt_data.get("description"):
                meta["description"] = yt_data["description"]
            meta["source"] = yt_data["source"]

    if args.text_only:
        if meta["title"]:
            print(f"Title: {meta['title']}")
        if meta.get("author_name"):
            print(f"Author: {meta['author_name']}")
        if meta.get("description"):
            print(f"\nDescription:\n{meta['description']}")
        return

    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
