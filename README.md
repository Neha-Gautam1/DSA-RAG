# DSA Revision Tutor (Love Babbar Playlist RAG)

A Hinglish-speaking DSA revision assistant built on Love Babbar's DSA YouTube playlist. Ask a question in natural Hinglish, get a grounded explanation, and the relevant part of the actual lecture video loads automatically with clickable related timestamps.

## How it works

```
YouTube playlist -> captions (or faster-whisper fallback) -> timestamp-aware chunks
-> embeddings -> Qdrant vector DB -> retrieval (primary + related) -> Groq LLM (Hinglish tutor)
-> FastAPI backend -> chat + embedded YouTube player frontend
```

- **Captions-first, whisper-fallback**: fast free YouTube captions where available; local `faster-whisper` transcription when they're not.
- **Every retrieved chunk keeps its timestamp** end-to-end, so the LLM explains concepts but never invents video navigation data — that always comes straight from Qdrant's stored metadata.
- **Local, embedded Qdrant** (no server/Docker needed) — the whole vector database is just a folder on disk.
- **Groq API** powers the Hinglish tutor responses (fast, generous free tier).

## Project structure

```
data/
  videos/        playlist metadata (video_id, title, url)
  transcripts/   one JSON per video: timestamped segments
  chunks/        timestamp-aware chunks + embeddings
  qdrant_db/     the built vector database (this ships with deployment)
  metadata/      ingestion progress/failure logs

src/
  ingestion/       playlist metadata extraction (yt-dlp)
  transcription/   caption fetching + whisper fallback
  chunking/        timestamp-aware chunking
  embeddings/      sentence-transformers wrapper
  qdrant/          vector DB setup, indexing, search
  retrieval/       full retrieval pipeline (primary/related selection)
  llm/             Hinglish tutor + query normalization (Groq)

app/
  backend/   FastAPI app (serves API + frontend)
  frontend/  chat UI, YouTube player, timestamp list (plain HTML/JS/CSS)

scripts/   command-line entry points for each pipeline stage
tests/     verification scripts for each stage
```

## Setup

**1. Clone and create a virtual environment**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**2. Install dependencies**
```powershell
pip install -r requirements.txt
```

**3. Configure environment variables**

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Notes |
|---|---|---|
| `PLAYLIST_URL` | Only for re-running ingestion | The YouTube playlist URL |
| `GROQ_API_KEY` | Yes | From console.groq.com |
| `GROQ_MODEL` | Yes | e.g. `openai/gpt-oss-120b` — check console.groq.com/docs/models if this ever errors as deprecated |
| `GROQ_QUERY_MODEL` | Optional | Defaults to `openai/gpt-oss-20b`, used for query typo-correction before retrieval |

`GROQ_API_KEY` is the only one that must never be committed to git — it's already in `.gitignore`.

## Running the app (data already built)

```powershell
uvicorn app.backend.main:app --reload
```
Open `http://127.0.0.1:8000/`.

## Rebuilding the knowledge base from scratch (ingestion pipeline)

Run these in order. Each step is resumable — safe to interrupt and rerun; already-completed work is skipped automatically.

```powershell
# 1. Get playlist video list
python scripts\run_playlist_extraction.py

# 2. Transcribe (captions first, whisper fallback)
python scripts\run_transcription.py --all
#   If YouTube blocks caption requests mid-run, it auto-switches to
#   whisper for the rest. To defer whisper and grab fast captions
#   for everything possible first instead, use:
python scripts\run_transcription.py --all --captions-only
python scripts\run_transcription.py --whisper-pending   # process what's left, later

# 3. Chunk transcripts into timestamp-aware pieces
python scripts\run_chunking.py

# 4. Generate embeddings
python scripts\run_embeddings.py

# 5. Index into Qdrant (stop uvicorn first -- only one process can access
#    the local Qdrant folder at a time)
python scripts\run_qdrant_indexing.py

# Check overall status anytime:
python scripts\check_progress.py
```

**Important**: after adding new videos, you must run steps 3-5 again before they become searchable in the app — transcription alone isn't enough.

## Testing

Each pipeline stage has a corresponding test in `tests/`:

```powershell
python tests\test_transcript.py           # inspect a saved transcript
python tests\test_chunks.py               # inspect chunking output
python tests\test_embeddings.py           # verify embedding shape/dimension
python tests\test_qdrant_retrieval.py     # raw similarity search
python tests\test_retrieval_pipeline.py   # full primary/related pipeline
python tests\test_llm_response.py         # end-to-end retrieval + Hinglish answer
python tests\test_cross_video.py          # find queries spanning multiple videos
python tests\test_typo_tolerance.py       # measure typo impact on retrieval
python tests\test_query_normalization.py  # verify typo-correction fix
```

## Deployment

This app ships its own built Qdrant database (`data/qdrant_db/`) as part of the deployment — no external database or persistent disk needed, since the app only reads from it at runtime.

**Render (recommended, free tier):**
1. Push this repo to GitHub (`data/qdrant_db/` must be committed; other `data/` subfolders stay gitignored).
2. New Web Service on render.com, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.backend.main:app --host 0.0.0.0 --port $PORT`
5. Add `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_QUERY_MODEL` as environment variables in the Render dashboard.

Free tier note: the service sleeps after 15 minutes idle; the first request after that takes about a minute to wake up.

## Troubleshooting

**"YouTube is blocking requests from your IP" during transcription**
YouTube rate-limits the captions API after heavy use. It's temporary (can take hours) and outside our control. The transcription script auto-detects this and switches to whisper (or defers to a pending list in `--captions-only` mode) rather than repeatedly failing. Check `tests\test_block_scope.py` periodically to see if it's cleared.

**Groq model errors ("model decommissioned")**
Groq periodically retires models. Check current options at console.groq.com/docs/models and update `GROQ_MODEL`/`GROQ_QUERY_MODEL` in `.env`.

**`RuntimeError: Storage folder ... already accessed by another instance of Qdrant`**
Local embedded Qdrant only allows one process at a time. Stop `uvicorn` before running any script that touches Qdrant (indexing, retrieval tests, etc.), then restart it afterward.

**Frontend changes not showing up on refresh**
The backend sets `Cache-Control: no-store` on `/static/` files specifically to prevent this — if you still see stale content, hard-refresh (`Ctrl+Shift+R`) once, and confirm `uvicorn` picked up the `main.py` change (restart if needed).

**Video doesn't load / "embed nahi ho pa raha"**
Some videos have embedding disabled by the uploader. This is a YouTube-side restriction, not a bug — the player falls back to a message rather than failing silently.

**A question returns "no content found" even though it seems like it should be covered**
Check `python scripts\check_progress.py` — if `Chunked`/`Embedded`/`Indexed` are behind `Transcribed`, the video's content hasn't made it into the searchable index yet. Run steps 3-5 of the ingestion pipeline.