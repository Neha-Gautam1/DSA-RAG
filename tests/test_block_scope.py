"""
tests/test_block_scope.py

Checks whether the YouTube caption block is IP-wide (affects any
video/channel) or somehow scoped narrower than that, by testing a
video from a completely different channel/playlist (Striver's DSA
course) than the one we've been indexing.
"""

import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import RequestBlocked

TEST_VIDEO_ID = "EAR7De6Goz4"  # Striver's A2Z DSA Course - C++ Basics

if __name__ == "__main__":
    print(f"Testing FULL caption fetch (list + fetch) for a DIFFERENT channel's video: {TEST_VIDEO_ID}")
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(TEST_VIDEO_ID)
        transcripts = list(transcript_list)
        print(f"list() SUCCESS -- found {len(transcripts)} caption track(s).")

        transcript = transcripts[0]
        fetched = transcript.fetch()
        raw = fetched.to_raw_data()
        print(f"fetch() SUCCESS -- retrieved {len(raw)} segments. Block is NOT affecting this request.")

    except RequestBlocked as e:
        print(f"STILL BLOCKED -- {e}")
        print("\nThis confirms the block is IP-wide, not specific to Love Babbar's playlist/channel.")
        print("Switching to a different playlist will NOT bypass it.")
    except Exception as e:
        print(f"Different error (not a block): {e}")
