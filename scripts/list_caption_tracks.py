"""
Quick diagnostic: list all available caption tracks for a video,
showing language and whether each is auto-generated or manually created.
"""
import sys
from youtube_transcript_api import YouTubeTranscriptApi

video_id = sys.argv[1] if len(sys.argv) > 1 else "WQoB2z67hvY"

ytt_api = YouTubeTranscriptApi()
transcript_list = ytt_api.list(video_id)

print(f"Available caption tracks for {video_id}:\n")
for t in transcript_list:
    kind = "AUTO-GENERATED" if t.is_generated else "MANUALLY CREATED"
    print(f"  language={t.language} ({t.language_code})  type={kind}  translatable={t.is_translatable}")