# Clario — Meeting Intelligence

AI-powered meeting intelligence platform. Clario joins your meetings as a bot, records audio, transcribes speech, extracts structured business intelligence, scores SOP conformance, and presents everything in a React dashboard.

---

## What It Does

- **Auto-joins meetings** — Playwright-based Chrome bot joins Google Meet, Zoom, and Teams from your calendar or a manual URL
- **Records audio** — captures WebRTC audio without echo using a JS gain-node approach
- **Transcribes** — OpenAI Whisper (`small` model) produces timestamped segments
- **Speaker diarization** — optional pyannote-based speaker identification
- **Extracts intelligence** — GPT-4o-mini pulls client name, problem, requirements, tech stack, timeline, budget, next steps, and conformance scores from the transcript
- **Flags risks** — auto-generated risk report highlights missing or ambiguous information
- **Dashboard** — React UI with Overview, Requirements, Conformance, Individual, Risks, and Transcript tabs
- **PDF export** — one-click PDF report per recording
- **Live transcription** — real-time WebSocket transcription from browser mic or screen capture

---

## Project Structure

```
AI_Call_Intelligence-dev/
├── run.py                        # Start the server (python run.py)
├── requirements.txt
├── .env                          # All configuration (see below)
├── credentials.json              # Google OAuth client secret
├── google_token.json             # Google OAuth token (auto-created)
│
├── app/
│   ├── config.py                 # Loads .env, defines paths
│   ├── logger.py                 # Logging setup
│   ├── main.py                   # CLI pipeline runner (offline batch)
│   ├── main_agent.py             # Meeting agent scheduler entry point
│   ├── realtime_server.py        # FastAPI app — serves dashboard + API
│   │
│   ├── api/
│   │   └── routes.py             # Agent, calendar, join-now routes
│   │
│   ├── pipeline/
│   │   └── pipeline.py           # Core 6-step analysis pipeline
│   │
│   ├── services/
│   │   ├── audio_extractor.py    # FFmpeg: video → 16 kHz mono WAV
│   │   ├── stt_service.py        # Whisper full-file transcription
│   │   ├── realtime_stt_service.py # Whisper live chunk transcription
│   │   ├── diarization_service.py  # pyannote speaker diarization
│   │   ├── transcript_cleaner.py   # Trim/normalize segments
│   │   ├── field_extractor.py    # LLM field + conformance extraction
│   │   ├── risk_report_service.py  # Risk flag generation
│   │   ├── storage_service.py    # JSON persistence
│   │   └── pipeline_runner.py    # Async pipeline wrapper for FastAPI
│   │
│   ├── agent/
│   │   ├── meeting_bot.py        # Playwright Chrome bot (record + join)
│   │   ├── scheduler.py          # APScheduler calendar-watcher
│   │   ├── calendar_watcher.py   # Google Calendar + Outlook fetch
│   │   ├── link_extractor.py     # Meeting URL detection (Meet/Zoom/Teams)
│   │   └── auto_leave.py         # Auto-leave on participant drop
│   │
│   ├── requirements/             # Requirements extraction subsystem
│   │   ├── extraction.py
│   │   ├── embedding.py
│   │   ├── ingestion.py
│   │   ├── scoring.py
│   │   └── reporting.py
│   │
│   └── static/
│       ├── index.html            # Dashboard entry
│       ├── app.jsx               # React source
│       ├── app.js                # Compiled React (served at runtime)
│       └── live_transcription.html  # Standalone WebSocket live UI
│
└── data/
    ├── uploads/                  # Uploaded / bot-recorded files
    ├── audio/                    # Extracted WAV files
    └── outputs/                  # JSON results (*_result.json)
```

---

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) — set `FFMPEG_PATH` in `.env` or add to PATH
- Google Chrome — required for the meeting bot
- An OpenAI API key — for LLM field extraction
- Node.js (optional) — only needed to recompile `app.jsx` after edits

---

## Installation

```bash
git clone https://github.com/OFI-Summer-AI/AI_Call_Intelligence.git
cd AI_Call_Intelligence/AI_Call_Intelligence-dev

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

---

## Configuration

Copy or edit `.env` in the project root:

```env
# ── Pipeline ──────────────────────────────────────────────
WHISPER_MODEL_SIZE=small          # tiny | base | small | medium | large
ENABLE_DIARIZATION=false          # true requires DIARIZATION_HF_TOKEN
DIARIZATION_HF_TOKEN=             # HuggingFace token (pyannote access)
FFMPEG_PATH=                      # Full path to ffmpeg.exe (or leave blank if on PATH)

# ── LLM ───────────────────────────────────────────────────
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# ── Google Calendar ────────────────────────────────────────
ENABLE_GOOGLE_CALENDAR=true
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=google_token.json

# ── Microsoft Outlook ──────────────────────────────────────
ENABLE_OUTLOOK_CALENDAR=false
MICROSOFT_CLIENT_ID=
MICROSOFT_TENANT_ID=common

# ── Bot behaviour ──────────────────────────────────────────
BOT_NAME=Clario
JOIN_EARLY_SECONDS=120            # join N seconds before meeting starts
CALENDAR_POLL_INTERVAL=5          # poll calendar every N minutes
BOT_GRACE_SECONDS=30              # wait N seconds after all leave before stopping

# ── Google account (bot signs in to Meet) ──────────────────
GOOGLE_ACCOUNT_EMAIL=your@gmail.com
GOOGLE_ACCOUNT_PASSWORD=yourpassword
```

---

## Running

### Start the dashboard + API server

```bash
python run.py
```

Open **http://localhost:8000** in your browser.

### Process a recording from the command line

```bash
python -m app.main --input path/to/meeting.mp4
python -m app.main --batch                        # process all files in data/uploads/
```

### Start the calendar-watcher scheduler (auto-join mode)

```bash
python -m app.main_agent
```

The scheduler polls your calendar and automatically joins upcoming meetings.

---

## Analysis Pipeline

Each recording goes through 6 steps:

```
Upload / Bot Recording
      ↓
1. Audio Extraction      FFmpeg → 16 kHz mono WAV
      ↓
2. Transcription         Whisper → timestamped segments
      ↓
3. Diarization           pyannote → speaker labels (optional)
      ↓
4. Field Extraction      GPT-4o-mini → client, requirements, scores
      ↓
5. Risk Report           Rule-based → flags missing / ambiguous info
      ↓
6. Save Output           JSON → data/outputs/*_result.json
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health + Whisper model info |
| `GET` | `/api/recordings` | List all analyzed recordings |
| `GET` | `/api/recordings/{job_id}` | Get a single recording |
| `POST` | `/api/recordings/{job_id}/reanalyze` | Re-run LLM extraction |
| `GET` | `/api/recordings/{job_id}/pdf` | Download PDF report |
| `POST` | `/api/upload-recording` | Upload a media file |
| `POST` | `/api/process?filename=` | Trigger pipeline on uploaded file |
| `GET` | `/api/process-status/{job_id}` | Check processing status |
| `GET` | `/api/upcoming-meetings` | Fetch calendar meetings (next 24 h) |
| `POST` | `/api/join-now` | Start bot for a meeting URL |
| `GET` | `/api/agent-status` | Bot current status |
| `POST` | `/api/agent-start` | Start the calendar-watcher scheduler |
| `POST` | `/api/agent-stop` | Stop the agent |
| `WS` | `/ws/transcribe` | WebSocket live audio transcription |

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| **Overview** | Client, problem, timeline, budget, summary, highlights, next steps |
| **Requirements** | Searchable list of extracted requirements |
| **Conformance** | SOP score (0–100), passed / missed criteria |
| **Individual** | Per-speaker scores, conformance breakdown |
| **Risks** | Risk flags, needs-review status |
| **Transcript** | Full timestamped transcript with activity chart |

---

## Enabling Speaker Diarization

1. Accept model terms at [huggingface.co/pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
2. Create a token at huggingface.co/settings/tokens
3. Add to `.env`:
   ```env
   ENABLE_DIARIZATION=true
   DIARIZATION_HF_TOKEN=hf_your_token_here
   ```

---

## Enabling Google Calendar

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable the **Google Calendar API**
3. Create OAuth 2.0 credentials (Desktop app) → download as `credentials.json`
4. Place `credentials.json` in the project root
5. Set `ENABLE_GOOGLE_CALENDAR=true` in `.env`
6. Run `python -m app.main_agent` — a browser window opens for one-time OAuth consent

---

## Recompiling the Frontend

If you edit `app/static/app.jsx`:

```bash
cd app/static
npx babel app.jsx --presets @babel/preset-react --out-file app.js
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI + Uvicorn |
| WebSocket | FastAPI WebSocket |
| Speech-to-Text | OpenAI Whisper |
| LLM Extraction | OpenAI GPT-4o-mini |
| Speaker Diarization | pyannote-audio 4.x |
| Meeting Bot | Playwright (Chrome) |
| Calendar | Google Calendar API, Microsoft Graph |
| Frontend | React + Recharts + Tailwind CSS |
| Audio Processing | FFmpeg |
| PDF Generation | fpdf2 |

---

## License

Internal use — OFI
