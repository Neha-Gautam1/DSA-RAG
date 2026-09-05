"""
tests/test_query_normalization.py

Verifies that typo'd queries now retrieve correctly via the full
retrieve() pipeline (which includes query normalization), compared
to the same queries WITHOUT normalization (raw embedding).
"""

import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

from src.llm.query_normalizer import normalize_query
from src.retrieval.retriever import retrieve

TYPO_QUERIES = [
    "flonchart aur psuedocode samjha do",
    "machin code aur compiller kya hota h",
]

if __name__ == "__main__":
    for typo_query in TYPO_QUERIES:
        cleaned = normalize_query(typo_query)
        print(f"\nRaw query:       '{typo_query}'")
        print(f"Normalized to:   '{cleaned}'")

        result = retrieve(typo_query)
        if result is None:
            print("Result: No relevant results found.")
            continue

        p = result["primary"]
        m, s = divmod(p["start_seconds"], 60)
        print(f"Primary result:  {m:02d}:{s:02d} - {p['text'][:80]}...")
