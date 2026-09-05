"""
app/backend/main.py

FastAPI backend exposing the DSA tutor's /query endpoint, and serving
the frontend (index.html, style.css, app.js) as static files.

Run with: uvicorn app.backend.main:app --reload
(from the project root, with .venv activated)
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.retrieval.retriever import retrieve
from src.llm.tutor import generate_answer

app = FastAPI(title="DSA Revision Tutor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    primary: dict | None
    related: list[dict]


NO_RESULTS_MESSAGE = (
    "Mujhe abhi is topic ke baare mein enough content nahi mila indexed videos mein. "
    "Thoda different tarike se pooch ke dekho, ya koi aur DSA topic try karo!"
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result = retrieve(request.query)

    if result is None:
        return QueryResponse(answer=NO_RESULTS_MESSAGE, primary=None, related=[])

    answer = generate_answer(request.query, result)

    return QueryResponse(
        answer=answer,
        primary=result["primary"],
        related=result["related"],
    )
