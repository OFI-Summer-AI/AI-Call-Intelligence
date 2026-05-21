"""
Central configuration — loaded from environment variables and optional .env file.
Merges the rich artifact layout from AI_Call_Intelligence_copy with Railway/Docker
defaults from AI_Call_Intelligence-dev.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
# Use /tmp/app_data in Docker/Railway; fall back to repo-local data/ locally
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(DATA_DIR / "uploads")))
AUDIO_DIR = DATA_DIR / "audio"
OUTPUT_DIR = DATA_DIR / "outputs"  # legacy compatibility

# Rich artifact layout (one stage → one file)
TRANSCRIPTS_RAW_DIR = DATA_DIR / "transcripts" / "raw"
TRANSCRIPTS_MERGED_DIR = DATA_DIR / "transcripts" / "merged"
TRANSCRIPTS_ROLE_MAPPED_DIR = DATA_DIR / "transcripts" / "role_mapped"
DIARIZATION_DIR = DATA_DIR / "diarization"
POLISHED_DIR = DATA_DIR / "polished"
EXTRACTED_DIR = DATA_DIR / "extracted"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_FINAL_DIR = DATA_DIR / "reports" / "final"
METADATA_DIR = DATA_DIR / "metadata"
LOGS_DIR = DATA_DIR / "logs"

_ARTIFACT_DIRS = (
    UPLOAD_DIR, AUDIO_DIR, OUTPUT_DIR,
    TRANSCRIPTS_RAW_DIR, TRANSCRIPTS_MERGED_DIR, TRANSCRIPTS_ROLE_MAPPED_DIR,
    DIARIZATION_DIR, POLISHED_DIR, EXTRACTED_DIR,
    REPORTS_DIR, REPORTS_FINAL_DIR, METADATA_DIR, LOGS_DIR,
)
for _folder in _ARTIFACT_DIRS:
    _folder.mkdir(parents=True, exist_ok=True)

# --- Speech-to-text ---
STT_BACKEND = os.getenv("STT_BACKEND", "whisper").strip().lower()
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe-diarize").strip()

# --- OpenAI (LLM) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# --- Diarization (optional, requires pyannote + HF token) ---
DIARIZATION_HF_TOKEN = os.getenv("DIARIZATION_HF_TOKEN", "").strip()
ENABLE_DIARIZATION = os.getenv("ENABLE_DIARIZATION", "false").lower() == "true"

# --- Pipeline ---
PIPELINE_RESUME = os.getenv("PIPELINE_RESUME", "false").lower() in ("1", "true", "yes")
PIPELINE_VERSION = os.getenv("PIPELINE_VERSION", "3.0").strip()

# --- FFmpeg (optional — set full path if not on system PATH) ---
# FFMPEG_PATH and FFPROBE_PATH are read directly by audio_extractor.py / video_metadata.py
# via os.getenv; no need to re-export here.

# --- Meeting Agent ---
BOT_NAME = os.getenv("BOT_NAME", "Clario")
JOIN_EARLY_SECONDS = int(os.getenv("JOIN_EARLY_SECONDS", "120"))
CALENDAR_POLL_INTERVAL = int(os.getenv("CALENDAR_POLL_INTERVAL", "5"))
BOT_POLL_INTERVAL_SEC = int(os.getenv("BOT_POLL_INTERVAL_SEC", "10"))
BOT_GRACE_SECONDS = int(os.getenv("BOT_GRACE_SECONDS", "30"))
ENABLE_GOOGLE_CALENDAR = os.getenv("ENABLE_GOOGLE_CALENDAR", "false").lower() == "true"
ENABLE_OUTLOOK_CALENDAR = os.getenv("ENABLE_OUTLOOK_CALENDAR", "false").lower() == "true"
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "google_token.json")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
# Google bot login (used by meeting_bot.py for browser-based Google sign-in)
GOOGLE_ACCOUNT_EMAIL = os.getenv("GOOGLE_ACCOUNT_EMAIL", "")
GOOGLE_ACCOUNT_PASSWORD = os.getenv("GOOGLE_ACCOUNT_PASSWORD", "")

# --- Server ---
PORT = int(os.getenv("PORT", "8000"))

# --- Other ---
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()

# Validate critical values
_STT_ALLOWED = frozenset({"whisper", "openai_diarize"})
if STT_BACKEND not in _STT_ALLOWED:
    raise ValueError(f"STT_BACKEND must be one of {sorted(_STT_ALLOWED)}, got {STT_BACKEND!r}")
