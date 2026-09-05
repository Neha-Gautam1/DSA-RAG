"""
scripts/check_progress.py

Quick status check across the whole pipeline: how many videos have
transcripts, chunks, embeddings, and are indexed in Qdrant -- plus
any logged transcription failures. Safe to run anytime, including
while run_transcription.py is still running in another terminal.
"""

import os
import json

PLAYLIST_PATH = "data/videos/playlist.json"
TRANSCRIPTS_DIR = "data/transcripts"
CHUNKS_DIR = "data/chunks"
INDEXED_MARKER_DIR = "data/metadata/indexed"
FAILURES_PATH = "data/metadata/transcription_failures.json"

if __name__ == "__main__":
    with open(PLAYLIST_PATH, "r", encoding="utf-8") as f:
        total_videos = len(json.load(f))

    transcribed = len([f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".json")]) \
        if os.path.isdir(TRANSCRIPTS_DIR) else 0

    chunked = len([f for f in os.listdir(CHUNKS_DIR) if f.endswith(".json") and not f.endswith("_embedded.json")]) \
        if os.path.isdir(CHUNKS_DIR) else 0

    embedded = len([f for f in os.listdir(CHUNKS_DIR) if f.endswith("_embedded.json")]) \
        if os.path.isdir(CHUNKS_DIR) else 0

    indexed = len([f for f in os.listdir(INDEXED_MARKER_DIR) if f.endswith(".done")]) \
        if os.path.isdir(INDEXED_MARKER_DIR) else 0

    failures = 0
    if os.path.exists(FAILURES_PATH):
        with open(FAILURES_PATH, "r", encoding="utf-8") as f:
            failures = len(json.load(f))

    print(f"Total videos in playlist: {total_videos}")
    print(f"Transcribed:              {transcribed}/{total_videos}")
    print(f"Chunked:                  {chunked}/{total_videos}")
    print(f"Embedded:                 {embedded}/{total_videos}")
    print(f"Indexed in Qdrant:        {indexed}/{total_videos}")
    print(f"Logged failures:          {failures}")

    if failures > 0:
        print(f"\nSee {FAILURES_PATH} for details on failed videos.")
