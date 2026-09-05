"""
src/transcription/whisper_transcriber.py

Fallback transcription for videos without usable YouTube captions.
Downloads audio only (via yt-dlp) and transcribes it locally with
faster-whisper. Cleans up the temp audio file afterward.
"""

import os
import tempfile
from yt_dlp import YoutubeDL
from faster_whisper import WhisperModel

# Loaded lazily so importing this module doesn't immediately load the model
# (useful for videos that never need whisper at all).
_model = None

MODEL_SIZE = "small"  # good balance of speed/accuracy on CPU for this project


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        print("  [whisper] Loading faster-whisper model (first time only)...")
        # device="auto" will use CUDA if available, otherwise CPU.
        _model = WhisperModel(MODEL_SIZE, device="auto", compute_type="int8")
    return _model


def _download_audio(video_url: str, dest_dir: str) -> str:
    """Downloads best available audio-only stream. Returns the file path."""
    output_template = os.path.join(dest_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        return ydl.prepare_filename(info)


def transcribe_with_whisper(video_id: str, video_url: str) -> list[dict] | None:
    """
    Downloads audio for the given video and transcribes it with faster-whisper.
    Returns segments in the same shape as caption_fetcher.get_captions(), or
    None if download/transcription fails.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            print(f"  [whisper] Downloading audio for {video_id}...")
            audio_path = _download_audio(video_url, tmp_dir)
        except Exception as e:
            print(f"  [whisper] Audio download failed for {video_id}: {e}")
            return None

        try:
            model = _get_model()
            print(f"  [whisper] Transcribing {video_id} (this may take a few minutes)...")
            raw_segments, _info = model.transcribe(audio_path, language=None, vad_filter=True)  # auto-detect, skip silence

            segments = []
            for seg in raw_segments:
                segments.append({
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": seg.text.strip(),
                })

            return segments if segments else None

        except Exception as e:
            import traceback
            print(f"  [whisper] Transcription failed for {video_id}: {e}")
            print(traceback.format_exc())
            return None
        # audio_path is inside tmp_dir, which is auto-deleted on exit
