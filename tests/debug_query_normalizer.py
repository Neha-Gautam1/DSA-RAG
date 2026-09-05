"""
tests/debug_query_normalizer.py

Debug helper: calls the Groq API directly for query normalization and
prints the FULL raw response, so we can see exactly what's coming
back (empty content? an error we're not surfacing? unexpected format?).
"""

import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv()

from groq import Groq
from src.llm.query_normalizer import SYSTEM_PROMPT, DEFAULT_NORMALIZER_MODEL

query = "flonchart aur psuedocode samjha do"

api_key = os.getenv("GROQ_API_KEY")
print(f"GROQ_API_KEY present: {bool(api_key)}")

model = os.getenv("GROQ_QUERY_MODEL", DEFAULT_NORMALIZER_MODEL)
print(f"Using model: {model}")

client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.0,
        max_tokens=60,
    )
    print("\nFull response object:")
    print(response)
    print("\nExtracted content:")
    print(repr(response.choices[0].message.content))

except Exception as e:
    print(f"\nEXCEPTION: {e}")
