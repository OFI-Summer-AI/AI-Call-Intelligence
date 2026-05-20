"""
FastAPI WebSocket server for real-time audio transcription.

Flow:
  Browser Mic → MediaRecorder API → Chunk audio every 1-3 sec
  → WebSocket → This server → Whisper Transcription → Live text back to client
"""

import asyncio
import json
import re
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, Response

from app.services.realtime_stt_service import RealtimeSTTService
from app.config import WHISPER_MODEL_SIZE, UPLOAD_DIR, OUTPUT_DIR, AUDIO_DIR
from app.api.routes import router as api_router

app = FastAPI(title="AI Call Intelligence - Live Transcription")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

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


# ── In-memory job status store ────────────────────────────────────────────────
_processing_jobs: dict[str, dict] = {}


# ── Serve React dashboard at root ─────────────────────────────────────────────
@app.get("/")
async def serve_app():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"error": "React app not built yet"}, status_code=404)


@app.get("/favicon.ico")
async def favicon():
    ico = STATIC_DIR / "favicon.ico"
    if ico.exists():
        return FileResponse(str(ico))
    return Response(status_code=204)


# ── Recordings API ────────────────────────────────────────────────────────────
@app.get("/api/recordings")
async def list_recordings():
    results = []
    for p in sorted(OUTPUT_DIR.glob("*_result.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            results.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return results


@app.get("/api/recordings/{job_id}")
async def get_recording(job_id: str):
    path = OUTPUT_DIR / f"{job_id}_result.json"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/recordings/{job_id}/reanalyze")
async def reanalyze_recording(job_id: str):
    result_path = OUTPUT_DIR / f"{job_id}_result.json"
    if not result_path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    data = json.loads(result_path.read_text(encoding="utf-8"))
    transcript = data.get("transcript", [])
    from app.services.field_extractor import FieldExtractor
    from app.services.risk_report_service import RiskReportService
    data["extracted_fields"] = FieldExtractor().extract(transcript)
    data["risk_report"] = RiskReportService().generate(data["extracted_fields"], transcript)
    result_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


@app.get("/api/recordings/{job_id}/pdf")
async def download_pdf(job_id: str):
    result_path = OUTPUT_DIR / f"{job_id}_result.json"
    if not result_path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    rec = json.loads(result_path.read_text(encoding="utf-8"))
    pdf_bytes = _generate_pdf(rec)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={job_id}_report.pdf"})


# ── File processing pipeline ──────────────────────────────────────────────────
@app.post("/api/process")
async def process_file(background_tasks: BackgroundTasks, filename: str):
    job_id = re.sub(r"[^\w\-]", "_", Path(filename).stem)
    if _processing_jobs.get(job_id, {}).get("status") == "processing":
        return {"job_id": job_id, "status": "already_processing"}
    _processing_jobs[job_id] = {"status": "processing", "started": datetime.now().isoformat()}
    background_tasks.add_task(_run_pipeline, filename, job_id)
    return {"job_id": job_id, "status": "processing"}


@app.get("/api/process-status/{job_id}")
async def process_status(job_id: str):
    if (OUTPUT_DIR / f"{job_id}_result.json").exists():
        return {"status": "done"}
    return _processing_jobs.get(job_id, {"status": "not_found"})


def _run_pipeline(filename: str, job_id: str):
    try:
        from app.services.audio_extractor import extract_audio
        from app.services.stt_service import STTService
        from app.services.transcript_cleaner import clean_segments
        from app.services.field_extractor import FieldExtractor
        from app.services.risk_report_service import RiskReportService
        from app.services.storage_service import StorageService

        src = UPLOAD_DIR / filename
        audio_out = AUDIO_DIR / f"{job_id}.wav"
        extract_audio(src, audio_out)
        stt = STTService(model_size=WHISPER_MODEL_SIZE).transcribe(audio_out)
        segs = clean_segments(stt["segments"])
        fields = FieldExtractor().extract(segs)
        risk = RiskReportService().generate(fields, segs)
        storage = StorageService()
        storage.save_json({"language": stt.get("language"), "segments": segs},
                          OUTPUT_DIR / f"{job_id}_transcript.json")
        storage.save_json({"job_id": job_id, "source_file": str(src), "audio_file": str(audio_out),
                           "transcript": segs, "speaker_segments": [],
                           "extracted_fields": fields, "risk_report": risk},
                          OUTPUT_DIR / f"{job_id}_result.json")
        _processing_jobs[job_id] = {"status": "done"}
    except Exception as e:
        _processing_jobs[job_id] = {"status": "error", "error": str(e)}


# ── PDF generation (server-side) ──────────────────────────────────────────────
def _generate_pdf(rec: dict) -> bytes:
    from fpdf import FPDF
    from datetime import datetime as dt

    def _s(v):
        if v is None: return "-"
        return (str(v).replace("’", "'").replace("‘", "'")
                .replace("“", '"').replace("”", '"')
                .replace("—", "-").replace("–", "-")
                .replace("•", "*").replace("→", "->")
                .encode("latin-1", "replace").decode("latin-1"))

    job_id = rec.get("job_id", "recording")
    fields = rec.get("extracted_fields") or {}
    risk = rec.get("risk_report") or {}
    risks = risk.get("risks") or []
    gen_time = dt.now().strftime("%B %d, %Y at %I:%M %p")

    GOLD = (160, 120, 48); DARK = (31, 41, 55); GRAY = (100, 116, 139)
    BORD = (220, 220, 220)

    pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page(); pdf.set_margins(20, 20, 20)
    W = pdf.w - 40

    title = re.sub(r"_\d{4}-\d{2}-\d{2}T[\d-]+$", "", job_id).replace("_", " ").title()
    pdf.set_font("Helvetica", "B", 17); pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 9, _s(title), ln=True)
    pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, f"Generated {_s(gen_time)}", ln=True)
    pdf.set_draw_color(*BORD); pdf.line(pdf.l_margin, pdf.get_y()+2, pdf.w-pdf.r_margin, pdf.get_y()+2)
    pdf.ln(8)

    def sec(text):
        pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*GOLD)
        pdf.cell(0, 5, text.upper(), ln=True)
        pdf.set_draw_color(*BORD); pdf.line(pdf.l_margin, pdf.get_y(), pdf.w-pdf.r_margin, pdf.get_y())
        pdf.ln(5); pdf.set_text_color(*DARK)

    conf = fields.get("conformance_score")
    call = fields.get("call_score")
    ind  = fields.get("individual_score")
    sec("Summary Scores")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Conformance: {int(float(conf))}/100  |  Call: {float(call):.1f}/10  |  Individual: {float(ind):.1f}/10  |  Risks: {len(risks)}", ln=True)
    pdf.ln(4)

    for label, val in [("Client", fields.get("client_name")), ("Problem", fields.get("client_problem")),
                       ("Timeline", fields.get("timeline")), ("Budget", fields.get("budget"))]:
        if val:
            pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*GOLD)
            pdf.cell(30, 5, label.upper())
            pdf.set_font("Helvetica", "", 8.5); pdf.set_text_color(*DARK)
            pdf.multi_cell(W-30, 5, _s(val), ln=True)
    pdf.ln(2)

    if fields.get("call_summary"):
        sec("Call Summary")
        pdf.set_font("Helvetica", "", 8.5); pdf.multi_cell(W, 5, _s(fields["call_summary"]), ln=True); pdf.ln(2)

    if risks:
        sec(f"Risk Report ({len(risks)} items)")
        for r in risks:
            desc = r if isinstance(r, str) else (r.get("description") or str(r))
            pdf.set_font("Helvetica", "", 8.5); pdf.multi_cell(W, 5, f"- {_s(desc)}", ln=True)
        pdf.ln(2)

    reqs = fields.get("strict_requirements") or []
    if reqs:
        sec(f"Requirements ({len(reqs)} items)")
        for i, r in enumerate(reqs, 1):
            pdf.set_font("Helvetica", "B", 7); pdf.set_text_color(*GOLD); pdf.cell(18, 5, f"REQ {i:02d}")
            pdf.set_font("Helvetica", "", 8.5); pdf.set_text_color(*DARK); pdf.multi_cell(W-18, 5, _s(r), ln=True)

    pdf.set_y(-18); pdf.set_draw_color(*BORD); pdf.line(pdf.l_margin, pdf.get_y(), pdf.w-pdf.r_margin, pdf.get_y())
    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, f"Call Intelligence  -  AI-Generated Report  -  {_s(gen_time)}", align="C")
    return bytes(pdf.output())


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
