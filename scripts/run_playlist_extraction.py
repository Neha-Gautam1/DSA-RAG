"""
scripts/run_playlist_extraction.py

Entry point for Phase 2: extract playlist metadata.
Run this from the project root.
"""

import os
import sys

# Allow "python scripts/run_playlist_extraction.py" to find src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from src.ingestion.playlist_extractor import extract_playlist_metadata

load_dotenv()

if __name__ == "__main__":
    playlist_url = os.getenv("PLAYLIST_URL")

    if not playlist_url:
        print("ERROR: PLAYLIST_URL not set in .env")
        sys.exit(1)

    force = "--force" in sys.argv

    videos = extract_playlist_metadata(playlist_url, force_refresh=force)
    print(f"\nTotal videos in playlist: {len(videos)}")