"""
FastAPI WebSocket server for real-time audio transcription.

Flow:
  Browser Mic → MediaRecorder API → Chunk audio every 1-3 sec
  → WebSocket → This server → Whisper Transcription → Live text back to client
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.services.realtime_stt_service import RealtimeSTTService
from app.config import WHISPER_MODEL_SIZE, UPLOAD_DIR

app = FastAPI(title="AI Call Intelligence - Live Transcription")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the standalone HTML UI
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

# Shared transcription service (loaded once)
stt_service: RealtimeSTTService | None = None


def get_stt_service() -> RealtimeSTTService:
    global stt_service
    if stt_service is None:
        stt_service = RealtimeSTTService(model_size=WHISPER_MODEL_SIZE)
    return stt_service


# Store active transcripts for Streamlit to poll
active_transcripts: dict[str, list[dict]] = {}


@app.on_event("startup")
async def startup():
    """Pre-load the Whisper model."""
    get_stt_service()
    print("[Server] Whisper model loaded. Ready for connections.")


@app.get("/health")
async def health():
    return {"status": "ok", "model": WHISPER_MODEL_SIZE}


@app.get("/api/transcripts")
async def get_transcripts():
    """Return all active session transcripts (for Streamlit polling)."""
    return active_transcripts


@app.get("/api/transcripts/{session_id}")
async def get_transcript(session_id: str):
    """Return transcript for a specific session."""
    return active_transcripts.get(session_id, [])


@app.post("/api/upload-recording")
async def upload_recording(file: UploadFile = File(...)):
    """Save an uploaded recording to the uploads directory."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = Path(file.filename).name if file.filename else f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
    dest = UPLOAD_DIR / safe_name

    # Avoid overwriting
    if dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        counter = 1
        while dest.exists():
            dest = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    print(f"[Server] Recording saved: {dest}")
    return JSONResponse({"status": "saved", "path": str(dest), "filename": dest.name})


@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for live audio transcription.
    Client sends binary audio chunks, server returns JSON with transcribed text.
    """
    await websocket.accept()
    print(f"[WebSocket] New client connected")

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    active_transcripts[session_id] = []
    stt = get_stt_service()

    # Send session info to client
    await websocket.send_json({"type": "session_start", "session_id": session_id})
    print(f"[WebSocket] Session started: {session_id}")

    chunk_count = 0
    try:
        while True:
            # Receive binary audio chunk from browser
            audio_data = await websocket.receive_bytes()

            if not audio_data:
                continue
            
            chunk_count += 1
            print(f"[WebSocket] Chunk {chunk_count} received: {len(audio_data)} bytes")

            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None, stt.transcribe_chunk, audio_data
            )

            if text:
                timestamp = datetime.now().strftime("%H:%M:%S")
                entry = {"time": timestamp, "text": text}
                active_transcripts[session_id].append(entry)
                print(f"[WebSocket] Transcription: {text}")

                # Send transcription back to client
                await websocket.send_json({
                    "type": "transcription",
                    "session_id": session_id,
                    "time": timestamp,
                    "text": text,
                })
            else:
                print(f"[WebSocket] No text returned from transcription service")

    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected. Session: {session_id}, Total chunks: {chunk_count}")
        await websocket.close()
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
