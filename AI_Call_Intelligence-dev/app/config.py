from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads")))
AUDIO_DIR = DATA_DIR / "audio"
OUTPUT_DIR = DATA_DIR / "outputs"

for folder in [UPLOAD_DIR, AUDIO_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
DIARIZATION_HF_TOKEN = os.getenv("DIARIZATION_HF_TOKEN", "")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
ENABLE_DIARIZATION = os.getenv("ENABLE_DIARIZATION", "false").lower() == "true"

# --- Meeting Agent ---
BOT_NAME = os.getenv("BOT_NAME", "AI Notetaker")
JOIN_EARLY_SECONDS = int(os.getenv("JOIN_EARLY_SECONDS", "120"))
CALENDAR_POLL_INTERVAL = int(os.getenv("CALENDAR_POLL_INTERVAL", "5"))
ENABLE_GOOGLE_CALENDAR = os.getenv("ENABLE_GOOGLE_CALENDAR", "true").lower() == "true"
ENABLE_OUTLOOK_CALENDAR = os.getenv("ENABLE_OUTLOOK_CALENDAR", "false").lower() == "true"
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", str(BASE_DIR / "credentials.json"))
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", str(BASE_DIR / "google_token.json"))
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")