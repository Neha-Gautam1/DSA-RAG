"""
src/utils/transcript_schema.py

Defines and enforces the transcript storage contract used across the
whole pipeline. Every transcript file (regardless of caption or whisper
source) must conform to this shape:

{
    "video_id": str,
    "title": str,
    "video_url": str,
    "source": "caption" | "whisper",
    "segments": [
        {"start": float, "end": float, "text": str},
        ...
    ]
}

validate_transcript() returns a list of human-readable problem strings.
An empty list means the transcript is valid.
"""

REQUIRED_TOP_LEVEL_FIELDS = ["video_id", "title", "video_url", "source", "segments"]
VALID_SOURCES = {"caption", "whisper"}


def validate_transcript(data: dict) -> list[str]:
    problems = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in data:
            problems.append(f"Missing top-level field: '{field}'")

    if problems:
        # Can't safely check further without the basics
        return problems

    if data["source"] not in VALID_SOURCES:
        problems.append(f"Invalid source: '{data['source']}' (expected one of {VALID_SOURCES})")

    segments = data["segments"]
    if not isinstance(segments, list) or len(segments) == 0:
        problems.append("segments must be a non-empty list")
        return problems

    prev_end = -1.0
    for i, seg in enumerate(segments):
        for field in ["start", "end", "text"]:
            if field not in seg:
                problems.append(f"Segment {i}: missing field '{field}'")
                continue

        if "start" in seg and "end" in seg:
            if seg["end"] < seg["start"]:
                problems.append(
                    f"Segment {i}: end ({seg['end']}) is before start ({seg['start']})"
                )
            if seg["start"] < prev_end - 3.0:
                # small tolerance for slight overlaps that are normal in captions
                problems.append(
                    f"Segment {i}: start ({seg['start']}) goes backwards past "
                    f"previous end ({prev_end})"
                )
            prev_end = seg["end"]

        if "text" in seg and not seg["text"].strip():
            problems.append(f"Segment {i}: empty text")

    return problems
