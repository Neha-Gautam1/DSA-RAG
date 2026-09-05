"""
src/embeddings/embedder.py

Generates sentence embeddings for chunk text using sentence-transformers
(all-MiniLM-L6-v2). Model is loaded lazily so importing this module is
cheap when embeddings aren't actually needed yet.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"  [embedder] Loading model '{MODEL_NAME}' (first time only)...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_chunks(chunks: list[dict], batch_size: int = 32) -> list[dict]:
    """
    Takes a list of chunk dicts (from chunker.py) and returns a new list
    where each chunk dict has an added "embedding" field: a list of floats.
    """
    model = _get_model()
    texts = [c["text"] for c in chunks]

    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    embedded_chunks = []
    for chunk, vector in zip(chunks, vectors):
        new_chunk = dict(chunk)  # copy, don't mutate original
        new_chunk["embedding"] = vector.tolist()
        embedded_chunks.append(new_chunk)

    return embedded_chunks
