"""
scripts/run_embeddings.py

Phase 6 entry point: generate embeddings for every chunked video.

Resumable: skips any video that already has data/chunks/{video_id}_embedded.json
"""

import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.embeddings.embedder import embed_chunks

CHUNKS_DIR = "data/chunks"


def is_raw_chunk_file(filename: str) -> bool:
    return filename.endswith(".json") and not filename.endswith("_embedded.json")


def already_embedded(video_id: str) -> bool:
    return os.path.exists(os.path.join(CHUNKS_DIR, f"{video_id}_embedded.json"))


if __name__ == "__main__":
    files = sorted(f for f in os.listdir(CHUNKS_DIR) if is_raw_chunk_file(f))
    total = len(files)

    if total == 0:
        print("No chunk files found. Run scripts/run_chunking.py first.")
        sys.exit(1)

    for i, filename in enumerate(files, start=1):
        video_id = filename.replace(".json", "")

        if already_embedded(video_id):
            print(f"[{i}/{total}] {video_id} already embedded, skipping")
            continue

        path = os.path.join(CHUNKS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"[{i}/{total}] Embedding {video_id} ({len(chunks)} chunks)...")
        embedded_chunks = embed_chunks(chunks)

        out_path = os.path.join(CHUNKS_DIR, f"{video_id}_embedded.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(embedded_chunks, f)  # no indent: keeps file size down for vectors

        print(f"[{i}/{total}] Saved {out_path}")

    print("\nDone.")
