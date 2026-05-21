"""Real-time Speech-to-Text service using Whisper on audio chunks."""

import tempfile
import whisper
from pathlib import Path
import time

from app.logger import get_logger

logger = get_logger(__name__)

# Whisper hallucinates these on silence — discard them
_HALLUCINATIONS = {
    "you", "you.", "you,",
    "thank you", "thank you.", "thank you,",
    "thanks", "thanks.",
    "bye", "bye.", "bye bye", "bye bye.",
    ".", "..", "...", " ",
}


def _is_hallucination(text: str) -> bool:
    return text.lower().strip().rstrip(".").strip() in _HALLUCINATIONS or len(text.strip()) <= 3


class RealtimeSTTService:
    """Transcribes audio chunks in real-time using Whisper."""

    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)
        self.audio_buffer = bytearray()
        self.chunk_count = 0
        # WebM: first chunk is EBML header — prepend to every batch so ffmpeg can decode
        self._webm_header: bytes | None = None
        # 5 chunks × 2s = ~10s window — enough context for Whisper to detect speech
        self.chunks_to_accumulate = 5
        self.idle_timeout = 3.0
        self.last_chunk_time = time.time()
        # Minimum bytes to bother transcribing — opus is very efficient, 300 bytes = real audio
        self._min_audio_bytes = 300

    def transcribe_chunk(self, audio_bytes: bytes) -> str:
        current_time = time.time()
        time_since_last_chunk = current_time - self.last_chunk_time
        self.last_chunk_time = current_time

        # Save WebM header from first chunk
        if self._webm_header is None:
            self._webm_header = audio_bytes
            logger.info("RealtimeSTT: WebM header captured (%d bytes)", len(audio_bytes))
            return ""

        # Flush on idle timeout
        if time_since_last_chunk > self.idle_timeout and len(self.audio_buffer) > 0:
            logger.info("RealtimeSTT: idle flush — %d chunks, %d bytes", self.chunk_count, len(self.audio_buffer))
            text = self._process_buffer()
            self.audio_buffer.clear()
            self.chunk_count = 0
            return text

        self.audio_buffer.extend(audio_bytes)
        self.chunk_count += 1
        logger.info("RealtimeSTT: chunk %d — buffer %d bytes", self.chunk_count, len(self.audio_buffer))

        if self.chunk_count >= self.chunks_to_accumulate:
            text = self._process_buffer()
            self.audio_buffer.clear()
            self.chunk_count = 0
            return text

        return ""

    def _process_buffer(self) -> str:
        if len(self.audio_buffer) < self._min_audio_bytes:
            logger.info("RealtimeSTT: buffer too small (%d bytes) — likely silence, skipping", len(self.audio_buffer))
            return ""
        try:
            data = (self._webm_header or b"") + bytes(self.audio_buffer)
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            result = self.model.transcribe(tmp_path, fp16=False, language="en")
            text = result.get("text", "").strip()
            Path(tmp_path).unlink(missing_ok=True)

            # avg_logprob is the reliable quality signal:
            # real speech > -1.0, noise/hallucination typically < -1.5
            # no_speech_prob is unreliable for mic audio — don't use it
            segments = result.get("segments", [])
            if segments:
                avg_logprob = sum(s.get("avg_logprob", -2.0) for s in segments) / len(segments)
                no_speech = sum(s.get("no_speech_prob", 1.0) for s in segments) / len(segments)
                logger.info("RealtimeSTT: no_speech_prob=%.2f avg_logprob=%.2f text='%s'", no_speech, avg_logprob, text)
                if avg_logprob < -1.5:
                    logger.info("RealtimeSTT: low confidence — discarding (hallucination)")
                    return ""

            if not text or _is_hallucination(text):
                logger.info("RealtimeSTT: filtered — '%s'", text)
                return ""

            logger.info("RealtimeSTT: transcribed — '%s'", text)
            return text
        except Exception as e:
            logger.error("RealtimeSTT: error — %s", e)
            return ""
