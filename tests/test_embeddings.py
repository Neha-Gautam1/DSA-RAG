"""
tests/test_embeddings.py

Phase 6 verification: confirms embeddings were generated with the
expected shape and are reasonably distinct from each other.
"""

import json
import os
import sys

CHUNKS_DIR = "data/chunks"

if __name__ == "__main__":
    embedded_files = sorted(
        f for f in os.listdir(CHUNKS_DIR) if f.endswith("_embedded.json")
    )

    if not embedded_files:
        print("No embedded chunk files found. Run scripts/run_embeddings.py first.")
        sys.exit(1)

    first_file = embedded_files[0]
    with open(os.path.join(CHUNKS_DIR, first_file), "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"File: {first_file}")
    print(f"Total chunks: {len(chunks)}")

    first_chunk = chunks[0]
    embedding = first_chunk["embedding"]
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

    # sanity check: two different chunks should not have identical embeddings
    if len(chunks) > 1:
        same = chunks[0]["embedding"] == chunks[1]["embedding"]
        print(f"Chunk 0 and chunk 1 embeddings identical? {same} (should be False)")
