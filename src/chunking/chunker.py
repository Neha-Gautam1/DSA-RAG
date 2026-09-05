"""
src/chunking/chunker.py

Merges short transcript segments (caption lines) into larger,
semantically-useful chunks while preserving accurate start/end
timestamps traceable back to the original video.
"""

TARGET_CHARS = 600       # aim for roughly this many characters per chunk
MAX_DURATION_SECONDS = 90  # never let a single chunk span longer than this


def chunk_transcript(transcript_data: dict) -> list[dict]:
    """
    transcript_data: the loaded contents of a data/transcripts/{video_id}.json file
    Returns a list of chunk dicts, each traceable back to the source video.
    """
    video_id = transcript_data["video_id"]
    title = transcript_data["title"]
    video_url = transcript_data["video_url"]
    segments = transcript_data["segments"]

    chunks = []
    buffer_segments = []
    buffer_text_len = 0
    chunk_index = 0

    def finalize_chunk():
        nonlocal chunk_index
        if not buffer_segments:
            return
        chunk_index += 1
        text = " ".join(s["text"] for s in buffer_segments).strip()
        chunks.append({
            "chunk_id": f"{video_id}_{chunk_index:04d}",
            "video_id": video_id,
            "title": title,
            "text": text,
            "start": buffer_segments[0]["start"],
            "end": buffer_segments[-1]["end"],
            "video_url": video_url,
        })

    for seg in segments:
        buffer_segments.append(seg)
        buffer_text_len += len(seg["text"]) + 1

        duration_so_far = seg["end"] - buffer_segments[0]["start"]

        if buffer_text_len >= TARGET_CHARS or duration_so_far >= MAX_DURATION_SECONDS:
            finalize_chunk()
            buffer_segments = []
            buffer_text_len = 0

    finalize_chunk()  # flush any leftover segments as the final chunk

    return chunks
