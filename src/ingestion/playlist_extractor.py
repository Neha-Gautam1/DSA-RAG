"""
src/ingestion/playlist_extractor.py

Fetches metadata (video_id, title, url, duration) for every video in a
YouTube playlist using yt-dlp, WITHOUT downloading any video/audio.

Resumable: if data/videos/playlist.json already exists, it is loaded
and reused unless force_refresh=True is passed.
"""

import json
import os
from yt_dlp import YoutubeDL

OUTPUT_PATH = "data/videos/playlist.json"


def extract_playlist_metadata(playlist_url: str, force_refresh: bool = False) -> list[dict]:
    """
    Returns a list of dicts like:
    {
        "video_id": "WQoB2z67hvY",
        "title": "...",
        "url": "https://www.youtube.com/watch?v=...",
        "duration": 1234,   # seconds, may be None
        "index": 1          # position in playlist, 1-based
    }
    """
    if os.path.exists(OUTPUT_PATH) and not force_refresh:
        print(f"Found existing {OUTPUT_PATH}, loading it (use force_refresh=True to re-fetch).")
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    print("Fetching playlist metadata from YouTube (this does not download video/audio)...")

    ydl_opts = {
        "extract_flat": True,   # don't resolve each video fully, just list them
        "quiet": True,
        "skip_download": True,
    }

    videos = []
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        entries = info.get("entries", [])

        for idx, entry in enumerate(entries, start=1):
            if entry is None:
                # Sometimes yt-dlp returns None for deleted/private videos
                print(f"[{idx}] Skipped: entry unavailable (deleted/private video)")
                continue

            video_id = entry.get("id")
            title = entry.get("title", "Unknown title")
            duration = entry.get("duration")

            videos.append({
                "video_id": video_id,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": duration,
                "index": idx,
            })
            print(f"[{idx}] {title}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(videos)} videos to {OUTPUT_PATH}")
    return videos
