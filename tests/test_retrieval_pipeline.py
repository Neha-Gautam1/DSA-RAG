"""
tests/test_retrieval_pipeline.py

Phase 8 verification: runs several sample queries through the full
retrieval pipeline and prints the primary + related structure,
INCLUDING raw scores so we can sanity-check the relevance threshold.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.embeddings.embedder import _get_model
from src.qdrant.qdrant_manager import search
from src.retrieval.retriever import retrieve

TEST_QUERIES = [
    "flowchart and pseudocode",
    "machine code and compiler",
    "how to write your first program",
]

if __name__ == "__main__":
    model = _get_model()

    for query in TEST_QUERIES:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print("=" * 60)

        # Show RAW scores first (before filtering/dedup) for diagnosis
        query_vector = model.encode(query).tolist()
        raw = search(query_vector, top_k=8)
        print("\nRAW top 8 (score, timestamp, text preview):")
        for r in raw:
            m, s = divmod(int(r["start"]), 60)
            print(f"  {r['score']:.3f}  {m:02d}:{s:02d}  {r['text'][:70]}...")

        # Now the actual pipeline output
        result = retrieve(query)
        if result is None:
            print("\nNo relevant results found (below relevance threshold).")
            continue

        p = result["primary"]
        p_min, p_sec = divmod(p["start_seconds"], 60)
        print(f"\nPRIMARY: {p_min:02d}:{p_sec:02d} - {p['title']}")

        print(f"RELATED ({len(result['related'])}):")
        for r in result["related"]:
            r_min, r_sec = divmod(r["start_seconds"], 60)
            print(f"  {r_min:02d}:{r_sec:02d}  {r['label']}")
