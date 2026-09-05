"""
scripts/run_transcription.py

Phase 3 entry point: for each video in the playlist, get a transcript
either from YouTube captions or (fallback) faster-whisper.

Resumable: skips any video that already has data/transcripts/{video_id}.json

Modes:
  (default)          Try captions, fall back to whisper immediately per video.
  --limit N          Only process the first N videos.
  --all              Process all videos.
  --captions-only    Try captions only. If unavailable/blocked, defer the
                      video to a "pending whisper" list and move on
                      immediately -- no waiting on whisper at all.
  --whisper-pending  Process ONLY videos previously deferred to the
                      pending whisper list (run this later, e.g. overnight).

Includes a circuit-breaker: if YouTube blocks our caption requests
(RequestBlocked/IpBlocked), we stop attempting captions for the rest
of this run and go straight to whisper (or the pending list, in
--captions-only mode) for remaining videos.
"""

import os
import sys
import json
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.transcription.caption_fetcher import get_captions, CaptionsBlockedError
from src.transcription.whisper_transcriber import transcribe_with_whisper

PLAYLIST_PATH = "data/videos/playlist.json"
TRANSCRIPTS_DIR = "data/transcripts"
FAILURES_PATH = "data/metadata/transcription_failures.json"
PENDING_WHISPER_PATH = "data/metadata/pending_whisper.json"

DELAY_BETWEEN_VIDEOS_SECONDS = 1.5

captions_blocked = False


def load_playlist() -> list[dict]:
    with open(PLAYLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def already_done(video_id: str) -> bool:
    return os.path.exists(os.path.join(TRANSCRIPTS_DIR, f"{video_id}.json"))


def save_transcript(video: dict, segments: list[dict], source: str) -> None:
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    out = {
        "video_id": video["video_id"],
        "title": video["title"],
        "video_url": video["url"],
        "source": source,
        "segments": segments,
    }
    path = os.path.join(TRANSCRIPTS_DIR, f"{video['video_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def log_failure(video: dict, reason: str) -> None:
    os.makedirs(os.path.dirname(FAILURES_PATH), exist_ok=True)
    failures = []
    if os.path.exists(FAILURES_PATH):
        with open(FAILURES_PATH, "r", encoding="utf-8") as f:
            failures = json.load(f)
    failures.append({"video_id": video["video_id"], "title": video["title"], "reason": reason})
    with open(FAILURES_PATH, "w", encoding="utf-8") as f:
        json.dump(failures, f, ensure_ascii=False, indent=2)


def load_pending() -> list[dict]:
    if not os.path.exists(PENDING_WHISPER_PATH):
        return []
    with open(PENDING_WHISPER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(pending: list[dict]) -> None:
    os.makedirs(os.path.dirname(PENDING_WHISPER_PATH), exist_ok=True)
    with open(PENDING_WHISPER_PATH, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)


def add_to_pending(video: dict) -> None:
    pending = load_pending()
    if not any(p["video_id"] == video["video_id"] for p in pending):
        pending.append(video)
        save_pending(pending)


def remove_from_pending(video_id: str) -> None:
    pending = load_pending()
    pending = [p for p in pending if p["video_id"] != video_id]
    save_pending(pending)


def process_video_captions_only(video: dict, position: int, total: int) -> None:
    """Tries captions only. Defers to pending list on failure/block -- never calls whisper."""
    global captions_blocked

    vid = video["video_id"]
    print(f"[{position}/{total}] {video['title']}")

    if already_done(vid):
        print(f"[{position}/{total}] already has a transcript, skipping")
        return

    if captions_blocked:
        print(f"[{position}/{total}] captions still blocked, deferring to pending list")
        add_to_pending(video)
        return

    try:
        captions = get_captions(vid)
    except CaptionsBlockedError:
        print(f"[{position}/{total}] YouTube blocked captions. Deferring remaining videos to pending list.")
        captions_blocked = True
        add_to_pending(video)
        return

    if captions:
        print(f"[{position}/{total}] captions found, using them ({len(captions)} segments)")
        save_transcript(video, captions, source="caption")
    else:
        print(f"[{position}/{total}] no captions available, deferring to pending list")
        add_to_pending(video)


def process_video_full(video: dict, position: int, total: int) -> None:
    """Default mode: tries captions, falls back to whisper immediately."""
    global captions_blocked

    vid = video["video_id"]
    print(f"[{position}/{total}] {video['title']}")

    if already_done(vid):
        print(f"[{position}/{total}] already has a transcript, skipping")
        return

    captions = None
    if not captions_blocked:
        try:
            captions = get_captions(vid)
        except CaptionsBlockedError:
            print(f"[{position}/{total}] YouTube is blocking caption requests. Switching to whisper-only for the rest of this run.")
            captions_blocked = True

    if captions:
        print(f"[{position}/{total}] captions found, using them ({len(captions)} segments)")
        save_transcript(video, captions, source="caption")
        return

    print(f"[{position}/{total}] no usable captions, falling back to whisper")
    whisper_segments = transcribe_with_whisper(vid, video["url"])
    if whisper_segments:
        print(f"[{position}/{total}] whisper transcription done ({len(whisper_segments)} segments)")
        save_transcript(video, whisper_segments, source="whisper")
        return

    print(f"[{position}/{total}] FAILED (no captions, whisper also failed)")
    log_failure(video, "no captions and whisper transcription failed")


def run_whisper_pending() -> None:
    pending = load_pending()
    total = len(pending)

    if total == 0:
        print("No videos in the pending whisper list.")
        return

    print(f"Processing {total} pending video(s) with whisper\n")

    for i, video in enumerate(pending, start=1):
        vid = video["video_id"]
        print(f"[{i}/{total}] {video['title']}")

        if already_done(vid):
            print(f"[{i}/{total}] already has a transcript, skipping")
            remove_from_pending(vid)
            continue

        whisper_segments = transcribe_with_whisper(vid, video["url"])
        if whisper_segments:
            print(f"[{i}/{total}] whisper transcription done ({len(whisper_segments)} segments)")
            save_transcript(video, whisper_segments, source="whisper")
            remove_from_pending(vid)
        else:
            print(f"[{i}/{total}] FAILED (whisper also failed)")
            log_failure(video, "whisper transcription failed")
            remove_from_pending(vid)


if __name__ == "__main__":
    if "--whisper-pending" in sys.argv:
        run_whisper_pending()
        print("\nDone.")
        sys.exit(0)

    videos = load_playlist()

    if "--all" in sys.argv:
        limit = len(videos)
    elif "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])
    else:
        limit = 3

    subset = videos[:limit]
    total = len(subset)
    captions_only = "--captions-only" in sys.argv

    mode_label = "captions-only (deferring whisper)" if captions_only else "captions + whisper fallback"
    print(f"Processing {total} video(s) (of {len(videos)} total in playlist) -- mode: {mode_label}\n")

    for i, video in enumerate(subset, start=1):
        if captions_only:
            process_video_captions_only(video, i, total)
        else:
            process_video_full(video, i, total)
        time.sleep(DELAY_BETWEEN_VIDEOS_SECONDS)

    if captions_only:
        pending_count = len(load_pending())
        print(f"\n{pending_count} video(s) deferred to the pending whisper list.")
        print("Run 'python scripts\\run_transcription.py --whisper-pending' later to process them.")

    print("\nDone.")
