"""
src/llm/tutor.py

Generates a natural Hinglish tutor-style explanation using retrieved
transcript context, via the Groq API.

IMPORTANT: The LLM only ever sees transcript TEXT as context. It never
receives, and is never asked to produce, timestamps or video IDs --
those come directly from the retrieval pipeline's structured data
(Phase 8), never from LLM output. This guarantees the project's
"never let the LLM invent timestamps" requirement structurally.
"""

import os
from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not found in environment. "
                "Add GROQ_API_KEY=your_key_here to your .env file."
            )
        _client = Groq(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You are a friendly, experienced DSA (Data Structures & Algorithms) tutor talking to a student in natural Hinglish (Hindi-English mix, written in Roman script) -- the same conversational style an Indian coding YouTuber uses.

Rules you must always follow:
- Answer using ONLY the CONTEXT provided. Do not add outside DSA knowledge that isn't grounded in the context, even if you personally know more about the topic.
- Before answering, check: does the CONTEXT actually explain what the student is asking about? If the context only mentions the topic in passing, or covers a different topic entirely, that is NOT enough to answer from.
- If the context doesn't clearly and substantially cover the question, say so honestly in Hinglish (e.g. "Ye topic maine abhi tak cover nahi kiya hai is context mein") instead of explaining the concept from general knowledge. A partial or tangential mention in the context is not the same as the context actually covering the topic -- when in doubt, say you don't have it rather than filling the gap yourself.
- Never mention timestamps, video IDs, or phrases like "at X minutes in the video" -- that is handled separately by the app, not by you.
- If the student asks about code and code appears in the context, explain it clearly. If no code is present in the context, say you don't have that code available right now.
- Keep it conversational and encouraging, like you're chatting with a student -- not writing a textbook.
- Keep your answer focused and reasonably concise (roughly 150-250 words) rather than writing an exhaustive essay -- this is a quick chat-style explanation, not a full lecture transcript.
"""


def build_context(retrieval_result: dict) -> str:
    """Combines primary + related chunk text into one context block for the LLM."""
    parts = [retrieval_result["primary"]["text"]]
    for r in retrieval_result.get("related", []):
        if "text" in r:
            parts.append(r["text"])
    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, retrieval_result: dict) -> str:
    context = build_context(retrieval_result)

    user_prompt = f"""CONTEXT (transcript excerpts from DSA lecture videos):
---
{context}
---

Student's question (in Hinglish): "{query}"

Give a natural, conversational Hinglish explanation using ONLY the context above."""

    client = _get_client()
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(
            f"Groq API call failed: {e}\n"
            f"If this mentions a decommissioned/unknown model, check current "
            f"available models at https://console.groq.com/docs/models and "
            f"set GROQ_MODEL in your .env accordingly."
        )
