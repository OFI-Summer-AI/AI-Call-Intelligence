from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR = DATA_DIR / "audio"
OUTPUT_DIR = DATA_DIR / "outputs"

for folder in [UPLOAD_DIR, AUDIO_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
DIARIZATION_HF_TOKEN = os.getenv("DIARIZATION_HF_TOKEN", "")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
ENABLE_DIARIZATION = os.getenv("ENABLE_DIARIZATION", "false").lower() == "true"

# OBS Watch Folder — set to your OBS "Recording Path" in OBS Settings > Output
OBS_WATCH_DIR = os.getenv("OBS_WATCH_DIR", "")

# OBS WebSocket — enable in OBS: Tools > WebSocket Server Settings
OBS_WS_HOST = os.getenv("OBS_WS_HOST", "localhost")
OBS_WS_PORT = int(os.getenv("OBS_WS_PORT", "4455"))
OBS_WS_PASSWORD = os.getenv("OBS_WS_PASSWORD", "")

# Meeting detection polling interval (seconds)
MEETING_POLL_INTERVAL = int(os.getenv("MEETING_POLL_INTERVAL", "5"))
# Seconds to wait after meeting window disappears before stopping recording
MEETING_END_GRACE_SECONDS = int(os.getenv("MEETING_END_GRACE_SECONDS", "15"))