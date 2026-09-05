"""
tests/test_transcript.py

Phase 3 verification: prints the transcript for the first video that has
one saved, so you can eyeball timestamp/text quality.
"""

import json
import os
import sys

TRANSCRIPTS_DIR = "data/transcripts"

if __name__ == "__main__":
    if not os.path.isdir(TRANSCRIPTS_DIR) or not os.listdir(TRANSCRIPTS_DIR):
        print("No transcripts found yet. Run scripts/run_transcription.py first.")
        sys.exit(1)

    files = sorted(os.listdir(TRANSCRIPTS_DIR))
    first_file = files[0]

    with open(os.path.join(TRANSCRIPTS_DIR, first_file), "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Video: {data['title']}")
    print(f"Source: {data['source']}")
    print(f"Segments: {len(data['segments'])}\n")

    for seg in data["segments"][:10]:
        start_min = int(seg["start"] // 60)
        start_sec = int(seg["start"] % 60)
        print(f"{start_min:02d}:{start_sec:02d} -> {seg['text']}")

    if len(data["segments"]) > 10:
        print(f"... ({len(data['segments']) - 10} more segments)")
