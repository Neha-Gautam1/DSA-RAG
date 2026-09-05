"""
src/retrieval/retriever.py

Full retrieval pipeline: embed query -> Qdrant search -> filter ->
deduplicate -> split into primary + related results.

This is the ONLY place that decides what counts as "primary" vs
"related". The LLM (Phase 9) will only ever receive this already-
resolved structure -- it never sees raw scores or invents timestamps.
"""

from src.embeddings.embedder import _get_model
from src.qdrant.qdrant_manager import search
from src.llm.query_normalizer import normalize_query

TOP_K = 8
MIN_SCORE = 0.35
DEDUP_WINDOW_SECONDS = 20
MAX_RELATED = 5
LABEL_MAX_CHARS = 60

# Recurring channel-intro boilerplate that shows up near-identically at the
# start of most videos. It's never the actual answer to a DSA question, but
# scores moderately on almost any query, so we filter it explicitly rather
# than relying on the score threshold alone.
BOILERPLATE_KEYWORDS = [
    "hello ji",
    "welcome to the channel",
    "welcome to my channel",
    "welcome to codehelp",
]


def _is_boilerplate(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in BOILERPLATE_KEYWORDS)


def _build_label(text: str) -> str:
    text = text.strip()
    if len(text) <= LABEL_MAX_CHARS:
        return text
    truncated = text[:LABEL_MAX_CHARS]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."


def _deduplicate(results: list[dict]) -> list[dict]:
    """
    Assumes results are already sorted by score descending.
    Keeps a result only if it's not within DEDUP_WINDOW_SECONDS of an
    already-kept result from the SAME video.
    """
    kept = []
    for r in results:
        is_duplicate = any(
            r["video_id"] == k["video_id"]
            and abs(r["start"] - k["start"]) < DEDUP_WINDOW_SECONDS
            for k in kept
        )
        if not is_duplicate:
            kept.append(r)
    return kept


def retrieve(query_text: str) -> dict | None:
    """
    Returns:
    {
        "primary": {video_id, title, start_seconds, end_seconds, video_url, text},
        "related": [
            {video_id, title, start_seconds, end_seconds, video_url, label}, ...
        ]
    }
    or None if nothing relevant was found.
    """
    model = _get_model()
    normalized_query = normalize_query(query_text)
    query_vector = model.encode(normalized_query).tolist()

    raw_results = search(query_vector, top_k=TOP_K)

    filtered = [
        r for r in raw_results
        if r["score"] >= MIN_SCORE and not _is_boilerplate(r["text"])
    ]
    if not filtered:
        return None

    filtered.sort(key=lambda r: r["score"], reverse=True)
    deduped = _deduplicate(filtered)

    if not deduped:
        return None

    primary_raw = deduped[0]
    related_raw = deduped[1:1 + MAX_RELATED]

    # sort related for natural reading order: grouped by video, then by time
    related_raw.sort(key=lambda r: (r["video_id"], r["start"]))

    primary = {
        "video_id": primary_raw["video_id"],
        "title": primary_raw["title"],
        "start_seconds": int(primary_raw["start"]),
        "end_seconds": int(primary_raw["end"]),
        "video_url": primary_raw["video_url"],
        "text": primary_raw["text"],
    }

    related = [
        {
            "video_id": r["video_id"],
            "title": r["title"],
            "start_seconds": int(r["start"]),
            "end_seconds": int(r["end"]),
            "video_url": r["video_url"],
            "label": _build_label(r["text"]),
            "text": r["text"],
        }
        for r in related_raw
    ]

    return {"primary": primary, "related": related}
