"""
src/transcription/caption_fetcher.py

Fetches YouTube's own captions/transcript for a video, if available.
Returns None (not an exception) when no usable captions exist, so the
caller can decide to fall back to whisper transcription.

Preference order:
1. Manually-created caption tracks (any language in LANGUAGE_PREFERENCES
   order) -- these are far more accurate than auto-generated ones.
2. Auto-generated caption tracks (same language order) as a fallback.

Compatible with youtube-transcript-api v1.x (instance-based API).
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import RequestBlocked

# Preferred languages, in order, WITHIN each tier (manual vs auto).
# English tracks tend to render Hinglish code-mixed speech more usefully
# for our embeddings than a Hindi-script auto-caption would.
LANGUAGE_PREFERENCES = ["en-IN", "en", "hi-IN", "hi"]


class CaptionsBlockedError(Exception):
    """
    Raised when YouTube is rate-limiting/blocking our caption requests
    entirely (RequestBlocked/IpBlocked). This is different from "no
    captions for this one video" -- it means EVERY subsequent caption
    request will likely also fail, so callers should stop trying
    captions for the rest of the run rather than hammering a blocked
    endpoint repeatedly (which can make the block worse/longer).
    """
    pass


def _pick_best(transcripts: list) -> "object | None":
    """Given a list of Transcript objects (all same tier), pick by language preference."""
    if not transcripts:
        return None
    for lang in LANGUAGE_PREFERENCES:
        for t in transcripts:
            if t.language_code == lang:
                return t
    return transcripts[0]  # fallback: whatever is available


def get_captions(video_id: str) -> list[dict] | None:
    """
    Returns a list of segments like:
        {"start": 12.3, "end": 15.8, "text": "..."}
    or None if no usable captions are available for this video.

    Raises CaptionsBlockedError if YouTube is blocking our requests
    entirely -- callers should catch this separately from a normal
    "no captions" case.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        all_transcripts = list(transcript_list)
        manual = [t for t in all_transcripts if not t.is_generated]
        auto = [t for t in all_transcripts if t.is_generated]

        transcript = _pick_best(manual) or _pick_best(auto)
        if transcript is None:
            return None

        source_note = "manual" if not transcript.is_generated else "auto"
        print(f"  [caption_fetcher] Using {source_note} '{transcript.language_code}' track")

        fetched = transcript.fetch()
        raw_segments = fetched.to_raw_data()

        segments = []
        for seg in raw_segments:
            start = seg["start"]
            duration = seg.get("duration", 0)
            segments.append({
                "start": round(start, 2),
                "end": round(start + duration, 2),
                "text": seg["text"].strip(),
            })

        return segments if segments else None

    except RequestBlocked as e:
        raise CaptionsBlockedError(str(e)) from e
    except Exception as e:
        print(f"  [caption_fetcher] No captions available for {video_id}: {e}")
        return None
