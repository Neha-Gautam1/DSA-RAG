"""
scripts/run_qdrant_indexing.py

Phase 7 entry point: upload all embedded chunks into Qdrant.

Resume-safe by design: re-running this script re-upserts the same
points (same chunk_id -> same point ID), so nothing gets duplicated.
We still track a simple "indexed" marker file per video so we can
skip re-reading/re-upserting videos that are already done, saving time
on large re-runs.
"""

import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.qdrant.qdrant_manager import upsert_chunks, ensure_collection

CHUNKS_DIR = "data/chunks"
INDEXED_MARKER_DIR = "data/metadata/indexed"


def is_embedded_file(filename: str) -> bool:
    return filename.endswith("_embedded.json")


def already_indexed(video_id: str) -> bool:
    return os.path.exists(os.path.join(INDEXED_MARKER_DIR, f"{video_id}.done"))


def mark_indexed(video_id: str) -> None:
    os.makedirs(INDEXED_MARKER_DIR, exist_ok=True)
    with open(os.path.join(INDEXED_MARKER_DIR, f"{video_id}.done"), "w") as f:
        f.write("done")


if __name__ == "__main__":
    ensure_collection()

    files = sorted(f for f in os.listdir(CHUNKS_DIR) if is_embedded_file(f))
    total = len(files)

    if total == 0:
        print("No embedded chunk files found. Run scripts/run_embeddings.py first.")
        sys.exit(1)

    for i, filename in enumerate(files, start=1):
        video_id = filename.replace("_embedded.json", "")

        if already_indexed(video_id):
            print(f"[{i}/{total}] {video_id} already indexed, skipping")
            continue

        path = os.path.join(CHUNKS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            embedded_chunks = json.load(f)

        count = upsert_chunks(embedded_chunks)
        mark_indexed(video_id)
        print(f"[{i}/{total}] {video_id}: upserted {count} points")

    print("\nDone.")
