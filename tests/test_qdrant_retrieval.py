"""
tests/test_qdrant_retrieval.py

Phase 7 verification: embeds a test query and runs a real similarity
search against Qdrant, printing the top results with their timestamps.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.embeddings.embedder import _get_model
from src.qdrant.qdrant_manager import search

QUERY = "flowchart and pseudocode"

if __name__ == "__main__":
    model = _get_model()
    query_vector = model.encode(QUERY).tolist()

    results = search(query_vector, top_k=5)

    if not results:
        print("No results returned. Did indexing run successfully?")
        sys.exit(1)

    print(f"Query: '{QUERY}'\n")
    for r in results:
        start_min, start_sec = divmod(int(r["start"]), 60)
        print(f"score={r['score']:.3f}  {start_min:02d}:{start_sec:02d}  {r['title']}")
        print(f"  {r['text'][:150]}...\n")

    from src.qdrant.qdrant_manager import get_client
    get_client().close()
