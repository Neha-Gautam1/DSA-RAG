"""
scripts/validate_transcripts.py

Phase 4: validate every saved transcript against the storage schema.
Run this any time after Phase 3 ingestion to catch corrupted or
malformed transcript files before they reach chunking/embeddings.
"""

import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.utils.transcript_schema import validate_transcript

TRANSCRIPTS_DIR = "data/transcripts"

if __name__ == "__main__":
    if not os.path.isdir(TRANSCRIPTS_DIR):
        print(f"No transcripts directory found at {TRANSCRIPTS_DIR}")
        sys.exit(1)

    files = sorted(f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".json"))

    if not files:
        print("No transcript files found. Run scripts/run_transcription.py first.")
        sys.exit(1)

    total = len(files)
    valid_count = 0
    invalid_count = 0

    for i, filename in enumerate(files, start=1):
        path = os.path.join(TRANSCRIPTS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        problems = validate_transcript(data)

        title = data.get("title", filename)
        segment_count = len(data.get("segments", []))

        if problems:
            invalid_count += 1
            print(f"[{i}/{total}] INVALID  {title} ({segment_count} segments)")
            for p in problems:
                print(f"    - {p}")
        else:
            valid_count += 1
            print(f"[{i}/{total}] OK       {title} ({segment_count} segments)")

    print(f"\n{valid_count}/{total} transcripts valid, {invalid_count}/{total} invalid.")

    sys.exit(0 if invalid_count == 0 else 1)
