"""
FastAPI server — serves the React dashboard and all API endpoints.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import WHISPER_MODEL_SIZE, UPLOAD_DIR
from app.logger import get_logger
from app.api.routes import router as agent_router
from app.api.recordings import router as recordings_router

logger = get_logger(__name__)

app = FastAPI(title="Clario — Call Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PermissionsPolicyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Permissions-Policy"] = "microphone=*, display-capture=*, camera=*"
        return response

app.add_middleware(PermissionsPolicyMiddleware)

app.include_router(agent_router)
app.include_router(recordings_router)

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

# ── Shared live-transcription service ─────────────────────────────────────────
_stt_service = None


def _get_stt():
    global _stt_service
    if _stt_service is None:
        from app.services.realtime_stt_service import RealtimeSTTService
        _stt_service = RealtimeSTTService(model_size=WHISPER_MODEL_SIZE)
    return _stt_service


# Active WebSocket transcripts (polled by frontend)
_active_transcripts: dict[str, list[dict]] = {}


@app.on_event("startup")
async def startup() -> None:
    _get_stt()
    logger.info("Clario server ready. Whisper model loaded.")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "model": WHISPER_MODEL_SIZE}


# ── React app root ─────────────────────────────────────────────────────────────
@app.get("/")
async def serve_app():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"error": "Frontend not found"}, status_code=404)


@app.get("/favicon.ico")
async def favicon():
    ico = STATIC_DIR / "favicon.ico"
    if ico.exists():
        return FileResponse(str(ico))
    return Response(status_code=204)


@app.get("/static/{path:path}.map")
async def sourcemap(_path: str):
    return Response(status_code=204)


# ── Upload recording ───────────────────────────────────────────────────────────
@app.post("/api/upload-recording")
async def upload_recording(file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name if file.filename else f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
    dest = UPLOAD_DIR / safe_name
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        counter = 1
        while dest.exists():
            dest = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
            counter += 1
    # Stream to disk in 8MB chunks so multi-GB files don't exhaust RAM
    chunk_size = 8 * 1024 * 1024
    total_bytes = 0
    with dest.open("wb") as f:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            total_bytes += len(chunk)
    logger.info("Recording saved: %s (%.1f MB)", dest.name, total_bytes / 1024 / 1024)
    return JSONResponse({"status": "saved", "path": str(dest), "filename": dest.name})


# ── Transcript polling (optional Streamlit / external consumers) ───────────────
@app.get("/api/transcripts")
async def get_transcripts():
    return _active_transcripts


@app.get("/api/transcripts/{session_id}")
async def get_transcript(session_id: str):
    return _active_transcripts.get(session_id, [])


# ── WebSocket live transcription ───────────────────────────────────────────────
@app.websocket("/ws/transcribe")
async def ws_transcribe(websocket: WebSocket):
    await websocket.accept()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    _active_transcripts[session_id] = []
    stt = _get_stt()
    await websocket.send_json({"type": "session_start", "session_id": session_id})
    logger.info("WebSocket session started: %s", session_id)

    chunk_count = 0
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            if not audio_data:
                continue
            chunk_count += 1
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, stt.transcribe_chunk, audio_data)
            if text:
                ts = datetime.now().strftime("%H:%M:%S")
                entry = {"time": ts, "text": text}
                _active_transcripts[session_id].append(entry)
                await websocket.send_json({"type": "transcription", "session_id": session_id, "time": ts, "text": text})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s (%d chunks)", session_id, chunk_count)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
