"""
tests/test_typo_tolerance.py

Diagnostic: compares retrieval quality for a correctly-spelled query
vs. a misspelled version of the same query, to measure how much
typos actually degrade our current embedding-based search.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.embeddings.embedder import _get_model
from src.qdrant.qdrant_manager import search

PAIRS = [
    ("flowchart aur pseudocode samjhao", "flonchart aur psuedocode samjha do"),
    ("machine code aur compiler kya hota hai", "machin code aur compiller kya hota h"),
]

if __name__ == "__main__":
    model = _get_model()

    for correct, typo in PAIRS:
        print(f"\n{'='*60}")
        print(f"CORRECT: '{correct}'")
        correct_results = search(model.encode(correct).tolist(), top_k=3)
        for r in correct_results:
            print(f"  score={r['score']:.3f}  {r['text'][:70]}...")

        print(f"\nTYPO:    '{typo}'")
        typo_results = search(model.encode(typo).tolist(), top_k=3)
        for r in typo_results:
            print(f"  score={r['score']:.3f}  {r['text'][:70]}...")

        if correct_results and typo_results:
            drop = correct_results[0]["score"] - typo_results[0]["score"]
            print(f"\nTop score drop due to typos: {drop:.3f}")
