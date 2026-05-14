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

        segments = []
        for seg in result.get("segments", []):
            segments.append(
                {
                    "start": self._seconds_to_timestamp(seg["start"]),
                    "end": self._seconds_to_timestamp(seg["end"]),
                    "text": seg["text"].strip(),
                }
            )

        logger.info(
            "Transcription complete — language=%s, segments=%d, words=%d",
            language,
            len(segments),
            len(result.get("text", "").split()),
        )
        return {
            "language": language,
            "text": result.get("text", "").strip(),
            "segments": segments,
        }

    @staticmethod
    def _seconds_to_timestamp(seconds: float) -> str:
        total_seconds = int(seconds)
        hh = total_seconds // 3600
        mm = (total_seconds % 3600) // 60
        ss = total_seconds % 60
        return f"{hh:02d}:{mm:02d}:{ss:02d}"