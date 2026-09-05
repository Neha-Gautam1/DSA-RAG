"""
tests/test_cross_video.py

Phase 16 verification: checks whether any test query's results span
multiple videos, so we can confirm cross-video navigation actually
gets exercised with real data (not just exist in code, untested).
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.retrieval.retriever import retrieve

CANDIDATE_QUERIES = [
    "code likhna kaise sikhe",
    "example samjhao",
    "programming language kya hoti hai",
    "condition kaise likhte hain",
    "loop kaise kaam karta hai",
]

if __name__ == "__main__":
    for query in CANDIDATE_QUERIES:
        result = retrieve(query)
        if result is None:
            print(f"'{query}': no results")
            continue

        video_ids = {result["primary"]["video_id"]}
        for r in result["related"]:
            video_ids.add(r["video_id"])

        marker = "CROSS-VIDEO" if len(video_ids) > 1 else "single video"
        print(f"'{query}': {marker} -- {len(video_ids)} distinct video(s): {video_ids}")
