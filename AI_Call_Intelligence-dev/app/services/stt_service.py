from pathlib import Path
import os
import whisper
from app.services.audio_extractor import _resolve_ffmpeg_binary
from app.logger import get_logger

logger = get_logger(__name__)


class STTService:
    def __init__(self, model_size: str = "base"):
        logger.info("Loading Whisper model: %s", model_size)
        ffmpeg_binary = _resolve_ffmpeg_binary()
        ffmpeg_bin_dir = str(Path(ffmpeg_binary).parent)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_bin_dir not in current_path:
            os.environ["PATH"] = ffmpeg_bin_dir + os.pathsep + current_path
        self.model = whisper.load_model(model_size)
        logger.info("Whisper model '%s' loaded", model_size)

    def transcribe(self, audio_path: str | Path) -> dict:
        audio_path = Path(audio_path)
        logger.info("Transcribing: %s", audio_path.name)
        result = self.model.transcribe(str(audio_path), fp16=False)
        language = result.get("language", "unknown")
        segments = [
            {
                "start": self._fmt(seg["start"]),
                "end":   self._fmt(seg["end"]),
                "text":  seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ]
        logger.info("Transcription done — language=%s, segments=%d", language, len(segments))
        return {"language": language, "text": result.get("text", "").strip(), "segments": segments}

    @staticmethod
    def _fmt(seconds: float) -> str:
        t = int(seconds)
        return f"{t // 3600:02d}:{(t % 3600) // 60:02d}:{t % 60:02d}"
