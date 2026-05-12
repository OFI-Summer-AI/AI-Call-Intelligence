"""Real-time Speech-to-Text service using Whisper on audio chunks."""

import io
import tempfile
import numpy as np
import whisper
import soundfile as sf
from pathlib import Path


class RealtimeSTTService:
    """Transcribes audio chunks in real-time using Whisper."""

    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)

    def transcribe_chunk(self, audio_bytes: bytes) -> str:
        """
        Transcribe a single audio chunk (WebM/opus or WAV bytes).
        Returns the transcribed text or empty string.
        """
        try:
            # Write bytes to a temp file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            result = self.model.transcribe(tmp_path, fp16=False, language="en")
            text = result.get("text", "").strip()

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)
            return text
        except Exception as e:
            print(f"[RealtimeSTT] Transcription error: {e}")
            return ""
