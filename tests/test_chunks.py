"""
tests/test_chunks.py

Phase 5 verification: prints a few sample chunks so you can eyeball
whether they're semantically coherent and timestamps look sane.
"""

import json
import os
import sys

CHUNKS_DIR = "data/chunks"

if __name__ == "__main__":
    if not os.path.isdir(CHUNKS_DIR) or not os.listdir(CHUNKS_DIR):
        print("No chunks found yet. Run scripts/run_chunking.py first.")
        sys.exit(1)

    files = sorted(os.listdir(CHUNKS_DIR))
    first_file = files[0]

    with open(os.path.join(CHUNKS_DIR, first_file), "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"File: {first_file}")
    print(f"Total chunks: {len(chunks)}\n")

    for c in chunks[:5]:
        start_min, start_sec = divmod(int(c["start"]), 60)
        end_min, end_sec = divmod(int(c["end"]), 60)
        print(f"[{c['chunk_id']}] {start_min:02d}:{start_sec:02d} -> {end_min:02d}:{end_sec:02d}")
        print(f"  {c['text'][:200]}{'...' if len(c['text']) > 200 else ''}\n")
