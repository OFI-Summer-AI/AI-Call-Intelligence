"""
Async wrapper around the synchronous Pipeline so it can be awaited
from FastAPI / asyncio contexts without blocking the event loop.
"""
import asyncio
from pathlib import Path
from app.config import UPLOAD_DIR
from app.logger import get_logger

logger = get_logger(__name__)


async def run_full_pipeline(session_id: str) -> dict:
    """
    Locate the recording for session_id, run the full pipeline
    (audio extract → Whisper STT → field extraction → risk report → save JSON)
    and return the result dict.

    The recording is expected to exist in UPLOAD_DIR with a filename
    that starts with session_id or equals session_id + common extensions.
    """
    # Find the recording file
    recording_path = _find_recording(session_id)
    if recording_path is None:
        logger.error("[pipeline_runner] No recording found for session %s in %s",
                     session_id, UPLOAD_DIR)
        return {"job_id": session_id, "error": "recording_not_found"}

    logger.info("[pipeline_runner] Running pipeline for session=%s file=%s",
                session_id, recording_path.name)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _sync_pipeline, str(recording_path))
        return result
    except Exception as exc:
        logger.error("[pipeline_runner] Pipeline failed for session %s: %s", session_id, exc)
        return {"job_id": session_id, "error": str(exc)}


def _find_recording(session_id: str) -> Path | None:
    """Return the first file in UPLOAD_DIR whose stem matches session_id."""
    for ext in (".wav", ".webm", ".mp4", ".mkv", ".mov", ".mp3", ".m4a"):
        candidate = UPLOAD_DIR / f"{session_id}{ext}"
        if candidate.exists():
            return candidate
    # Fallback: glob for any file that starts with session_id
    matches = sorted(UPLOAD_DIR.glob(f"{session_id}*"))
    return matches[0] if matches else None


def _sync_pipeline(recording_path: str) -> dict:
    from app.pipeline.pipeline import Pipeline
    return Pipeline().run(recording_path)
