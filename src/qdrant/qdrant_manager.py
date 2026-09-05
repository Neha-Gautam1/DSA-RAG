"""
src/qdrant/qdrant_manager.py

Sets up a local (embedded, no server needed) Qdrant collection and
provides duplicate-safe batch upsert for embedded chunks.
"""

import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

DB_PATH = "data/qdrant_db"
COLLECTION_NAME = "dsa_chunks"
VECTOR_SIZE = 384  # must match the embedding model's output dimension

_client = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(path=DB_PATH)
    return _client


def ensure_collection() -> None:
    """Creates the collection if it doesn't already exist. Safe to call every run."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"  [qdrant] Created collection '{COLLECTION_NAME}'")
    else:
        print(f"  [qdrant] Collection '{COLLECTION_NAME}' already exists")


def _chunk_id_to_point_id(chunk_id: str) -> str:
    """
    Deterministically maps a chunk_id string to a UUID.
    Same chunk_id -> same UUID every time, which makes upserts
    duplicate-safe: re-uploading a chunk overwrites the same point.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


def upsert_chunks(embedded_chunks: list[dict], batch_size: int = 100) -> int:
    """
    Uploads embedded chunks into Qdrant. Returns the number of points upserted.
    """
    client = get_client()
    ensure_collection()

    points = []
    for chunk in embedded_chunks:
        point_id = _chunk_id_to_point_id(chunk["chunk_id"])
        points.append(
            PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "video_id": chunk["video_id"],
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "start": chunk["start"],
                    "end": chunk["end"],
                    "video_url": chunk["video_url"],
                },
            )
        )

    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    return len(points)


def search(query_vector: list[float], top_k: int = 8) -> list[dict]:
    """
    Runs a similarity search and returns a list of dicts with payload + score.
    """
    client = get_client()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    ).points

    return [
        {**point.payload, "score": point.score}
        for point in results
    ]
