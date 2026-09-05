"""
tests/test_llm_response.py

Phase 9 verification: runs a query through retrieval, then through the
LLM tutor, and prints the final Hinglish answer.
"""

import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

from src.retrieval.retriever import retrieve
from src.llm.tutor import generate_answer

TEST_QUERIES = [
    "flowchart aur pseudocode samjhao",
    "machine code aur compiler kya hota hai",
]

if __name__ == "__main__":
    for query in TEST_QUERIES:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print("=" * 60)

        result = retrieve(query)
        if result is None:
            print("No relevant results found.")
            continue

        answer = generate_answer(query, result)

        p = result["primary"]
        p_min, p_sec = divmod(p["start_seconds"], 60)

        print(f"\n[Video would jump to {p_min:02d}:{p_sec:02d} in '{p['title']}']\n")
        print("TUTOR ANSWER:")
        print(answer)
