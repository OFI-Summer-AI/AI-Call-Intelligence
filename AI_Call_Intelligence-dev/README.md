# Sales Call Intelligence

AI-powered Sales Call Intelligence platform for processing MP4 meeting recordings and extracting structured business intelligence from conversations.

The system focuses on:

- Speech-to-text transcription with timestamps
- Speaker diarization (who spoke what)
- Client requirement extraction
- Client pain point identification
- Tech stack / platform extraction
- Risk report generation
- Timestamp-based traceability
- Future-ready video intelligence support

---

# Project Objective

Sales calls often contain critical business and technical information that is:
- undocumented
- misunderstood
- lost across teams
- difficult to trace later

This project converts raw meeting recordings into structured, searchable, and auditable sales intelligence.

---

# Current Scope (MVP)

## Audio Intelligence (Offline Pipeline)

- MP4 upload
- Audio extraction
- Timestamped speech-to-text
- Speaker diarization (optional)
- Transcript cleaning
- Sales field extraction
- Risk report generation
- Structured JSON output

## Live Transcription (Real-Time)

- Browser-based microphone capture
- Browser-based screen/meeting capture (OBS alternative)
- Real-time audio streaming via WebSocket
- Whisper-powered live transcription
- Streamlit UI with session history
- Downloadable meeting recordings

---

# Planned Future Scope

## Video Intelligence
- Key frame extraction
- Dashboard/chart detection
- OCR from shared screens
- Timestamp-linked visual evidence

## Governance & Intelligence
- Human review workflows
- Confidence scoring
- Semantic validation
- Requirement drift detection

---

# High-Level Flow

## Offline Pipeline

```text
MP4 Upload → Audio Extraction → Speech-to-Text → Speaker Diarization
   → Transcript Cleaning → Sales Field Extraction → Risk Report → JSON Output
```

## Live Transcription

```text
Browser Mic / Screen Capture
   ↓
MediaRecorder API (audio/webm chunks every 1-3s)
   ↓
WebSocket
   ↓
FastAPI Backend
   ↓
Whisper Transcription
   ↓
Live Transcript Stream
   ↓
Streamlit UI / Browser
```

---

# Project Structure

```text
AI_Call_Intelligence/
├── app/
│   ├── main.py                      # CLI entry point (offline pipeline)
│   ├── config.py                    # Central configuration
│   ├── realtime_server.py           # FastAPI WebSocket server (live transcription)
│   ├── streamlit_app.py             # Streamlit UI
│   ├── orchestrator/
│   │   └── pipeline.py              # Offline pipeline orchestrator
│   ├── services/
│   │   ├── audio_extractor.py       # FFmpeg audio extraction
│   │   ├── stt_service.py           # Offline Whisper transcription
│   │   ├── realtime_stt_service.py  # Real-time Whisper transcription
│   │   ├── diarization_service.py   # Speaker diarization (pyannote)
│   │   ├── transcript_cleaner.py    # Transcript cleanup
│   │   ├── field_extractor.py       # Sales field extraction
│   │   ├── risk_report_service.py   # Risk report generation
│   │   ├── storage_service.py       # JSON output storage
│   │   └── job_service.py           # Job tracking (placeholder)
│   └── static/
│       └── live_transcription.html  # Standalone browser UI
│
├── data/
│   ├── uploads/                     # Input video files
│   ├── audio/                       # Extracted audio
│   └── outputs/                     # JSON results
│
├── requirements.txt
└── README.md
```

---

# Core Modules

## `pipeline.py`

Main orchestrator responsible for:

- coordinating the full workflow
- calling services in sequence
- managing processing flow

---

## `audio_extractor.py`

Responsible for:

- extracting audio from MP4
- audio conversion
- audio preprocessing

---

## `stt_service.py`

Responsible for:

- speech-to-text conversion
- timestamp generation
- transcript generation

---

## `diarization_service.py`

Responsible for:

- speaker segmentation
- speaker labeling
- identifying speaker timelines

---

## `transcript_cleaner.py`

Responsible for:

- transcript formatting
- punctuation cleanup
- transcript normalization

---

## `field_extractor.py`

Responsible for extracting:

- client name
- client problem
- strict requirements
- platforms/tech stack
- timelines
- dependencies
- action items

---

## `risk_report_service.py`

Responsible for generating:

- missing clarification points
- ambiguous requirements
- delivery risks
- commercial risks
- technical concerns

---

# Example Transcript Output

```json
[
  {
    "start": "00:01:12",
    "end": "00:01:18",
    "speaker": "Speaker_1",
    "text": "We need SAP integration in phase one."
  }
]
```

---

# Example Structured Output

```json
{
  "client_name": "ABC Corp",
  "client_problem": "Manual reporting delays",
  "strict_requirements": [
    "SAP integration",
    "15-minute dashboard refresh"
  ],
  "techstack_platform": [
    "SAP",
    "Power BI"
  ],
  "risk_report": [
    "Timeline not fully confirmed",
    "API ownership unclear"
  ]
}
```

---

# Technology Stack

| Component            | Technology              |
| -------------------- | ----------------------- |
| Backend API          | FastAPI + WebSocket     |
| Speech-to-Text       | OpenAI Whisper          |
| Speaker Diarization  | Pyannote                |
| Real-Time UI         | Streamlit               |
| Audio Capture        | MediaRecorder API       |
| Screen Capture       | Screen Capture API      |
| Server               | Uvicorn                 |
| File Storage         | Local filesystem        |

---

# Installation

## Prerequisites

- **Python 3.10+**
- **FFmpeg** installed and available on PATH ([download](https://ffmpeg.org/download.html))
- A modern browser (Chrome, Edge, or Firefox) for live transcription

## Clone Repository

```bash
git clone https://github.com/OFI-Summer-AI/AI_Call_Intelligence.git
cd AI_Call_Intelligence
```

---

## Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables (Optional)

Create a `.env` file in the project root to customize settings:

```env
# Whisper model size: tiny, base, small, medium, large
WHISPER_MODEL_SIZE=base

# Speaker diarization (requires HuggingFace token)
ENABLE_DIARIZATION=false
DIARIZATION_HF_TOKEN=your_huggingface_token_here

# Field extraction confidence threshold
CONFIDENCE_THRESHOLD=0.80
```

If no `.env` file exists, the app uses sensible defaults.

---

# Running the Application

## Option 1: Offline Pipeline (process a video file)

```bash
python -m app.main --input path/to/meeting.mp4
```

Without `--input`, it processes `data/uploads/client_call_01.mp4` by default.

---

## Option 2: Live Transcription (real-time)

This requires **two terminals**:

### Terminal 1 - Start the FastAPI WebSocket server

```bash
python -m app.realtime_server
```

The server starts on `http://localhost:8000`. On first run, Whisper downloads the model (~140 MB for `base`).

### Terminal 2 - Start the Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

Opens at `http://localhost:8501`.

### Using the UI

1. Open `http://localhost:8501` in your browser
2. Choose a tab:
   - **Live Recording** -- captures microphone audio
   - **Screen Capture** -- captures system audio from any meeting app (Teams, Zoom, Meet). Check "Share audio" when prompted. Optionally mix your microphone. Download the full recording when done.
3. Click **Start** and speak or share your meeting window
4. Live transcript appears in real-time
5. View past sessions in the **Session History** tab

### Standalone HTML (no Streamlit needed)

With the FastAPI server running, open:

```
http://localhost:8000/static/live_transcription.html
```

---

# API Endpoints (Live Server)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `GET` | `/api/transcripts` | All session transcripts |
| `GET` | `/api/transcripts/{session_id}` | Single session transcript |
| `WS` | `/ws/transcribe` | WebSocket for live audio streaming |

---

# Processing Pipeline

## Step 1 — MP4 Upload

Store uploaded file and create job ID.

## Step 2 — Audio Extraction

Extract audio track from video.

## Step 3 — Speech-to-Text

Generate timestamped transcript.

## Step 4 — Speaker Diarization

Identify speaker segments.

## Step 5 — Transcript Cleaning

Normalize transcript structure.

## Step 6 — Sales Intelligence Extraction

Extract business-critical information.

## Step 7 — Risk Report Generation

Generate clarification and risk insights.

## Step 8 — Save Final Output

Store transcript and structured intelligence.

---

# Future Enhancements

## Audio Intelligence

- sentiment analysis
- confidence scoring
- semantic validation

## Video Intelligence

- frame summarization
- OCR extraction
- dashboard detection
- architecture diagram capture

## Governance

- human review workflows
- audit trails
- versioning
- requirement drift detection

---

# Design Principles

- Simple orchestrator architecture
- Modular services
- Production-ready structure
- Traceability via timestamps
- Extensible for multimodal AI
- Avoid overengineering in MVP

---

# Future Vision

The long-term goal is to build a multimodal conversational intelligence platform capable of understanding:

- sales calls
- client meetings
- project KT sessions
- internal discussions
- interview recordings

using:

- audio intelligence
- video intelligence
- semantic reasoning
- enterprise governance workflows

---

# License

Internal Research / Enterprise Use
