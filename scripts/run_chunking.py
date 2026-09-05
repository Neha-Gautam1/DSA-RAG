"""
scripts/run_chunking.py

Phase 5 entry point: chunk every saved transcript into timestamp-aware,
semantically-useful pieces ready for embedding.

Resumable: skips any video that already has a data/chunks/{video_id}.json
"""

import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.chunking.chunker import chunk_transcript

TRANSCRIPTS_DIR = "data/transcripts"
CHUNKS_DIR = "data/chunks"


def already_chunked(video_id: str) -> bool:
    return os.path.exists(os.path.join(CHUNKS_DIR, f"{video_id}.json"))


def save_chunks(video_id: str, chunks: list[dict]) -> None:
    os.makedirs(CHUNKS_DIR, exist_ok=True)
    path = os.path.join(CHUNKS_DIR, f"{video_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    files = sorted(f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".json"))
    total = len(files)

    if total == 0:
        print("No transcripts found. Run scripts/run_transcription.py first.")
        sys.exit(1)

    for i, filename in enumerate(files, start=1):
        video_id = filename.replace(".json", "")

        if already_chunked(video_id):
            print(f"[{i}/{total}] {video_id} already chunked, skipping")
            continue

        path = os.path.join(TRANSCRIPTS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        chunks = chunk_transcript(transcript_data)
        save_chunks(video_id, chunks)
        print(f"[{i}/{total}] {transcript_data['title']} -> {len(chunks)} chunks")

    print("\nDone.")
