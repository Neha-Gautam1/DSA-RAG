"""
src/llm/query_normalizer.py

Cleans up the user's raw query (fixes typos, tightens loose phrasing)
BEFORE it gets embedded for retrieval. This runs as a small, fast LLM
call separate from the main tutor answer generation.

IMPORTANT: if this call fails for any reason (network, deprecated
model, etc.), we fall back to the original raw query rather than
breaking retrieval entirely -- this is a quality enhancement, not a
dependency the whole pipeline should collapse without.
"""

import os
from groq import Groq

# A smaller/faster model is fine here -- this is a simple text-cleanup
# task, not something that needs a large model's reasoning.
DEFAULT_NORMALIZER_MODEL = "openai/gpt-oss-20b"

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not found in environment.")
        _client = Groq(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You clean up short search queries about Data Structures & Algorithms (DSA) topics. The queries are often in Hinglish (Hindi-English mix) and may contain spelling mistakes or typos.

Rules:
- Fix obvious spelling mistakes and typos (e.g. "flonchart" -> "flowchart", "psuedocode" -> "pseudocode").
- Keep the query short and in the same rough language mix the user used.
- Output ONLY the corrected query text. No explanation, no quotes, no extra words.
"""


def normalize_query(raw_query: str) -> str:
    """
    Returns a cleaned-up version of the query for embedding/retrieval.
    Falls back to the original raw_query if the LLM call fails.
    """
    try:
        client = _get_client()
        model = os.getenv("GROQ_QUERY_MODEL", DEFAULT_NORMALIZER_MODEL)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_query},
            ],
            temperature=0.0,
            max_tokens=150,
            reasoning_effort="low",
        )

        cleaned = response.choices[0].message.content.strip()
        if not cleaned:
            print("  [query_normalizer] Empty content returned, falling back to raw query")
            return raw_query
        return cleaned

    except Exception as e:
        print(f"  [query_normalizer] Falling back to raw query, normalization failed: {e}")
        return raw_query
