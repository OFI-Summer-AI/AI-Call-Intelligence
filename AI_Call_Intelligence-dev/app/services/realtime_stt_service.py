"""Real-time Speech-to-Text service using Whisper on audio chunks."""

import io
import tempfile
import numpy as np
import whisper
import soundfile as sf
from pathlib import Path
import time


class RealtimeSTTService:
    """Transcribes audio chunks in real-time using Whisper."""

    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)
        self.audio_buffer = bytearray()
        self.chunk_count = 0
        # Process after collecting ~15 seconds of audio (roughly 7-8 chunks at 2-3 sec intervals)
        self.chunks_to_accumulate = 8
        self.idle_timeout = 3.0  # Auto-flush after 3 seconds of silence
        self.last_chunk_time = time.time()

    def _process_buffer(self) -> str:
        """Process the accumulated audio buffer and return transcribed text."""
        if len(self.audio_buffer) == 0:
            return ""
        
        try:
            audio_data = bytes(self.audio_buffer)
            
            # Write accumulated bytes to a temp file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            result = self.model.transcribe(tmp_path, fp16=False, language="en")
            text = result.get("text", "").strip()

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)
            
            return text
        except Exception as e:
            print(f"[RealtimeSTT] Transcription error: {e}")
            return ""

    def transcribe_chunk(self, audio_bytes: bytes) -> str:
        """
        Accumulate audio chunks and transcribe when:
        1. Buffer reaches 5 chunks (~10-15 seconds), OR
        2. More than 2 seconds elapsed since last chunk (natural pause)
        
        Returns the transcribed text or empty string.
        """
        current_time = time.time()
        time_since_last_chunk = current_time - self.last_chunk_time
        self.last_chunk_time = current_time
        
        # Check if we need to flush due to idle timeout
        if time_since_last_chunk > self.idle_timeout and len(self.audio_buffer) > 0:
            print(f"[RealtimeSTT] Idle timeout ({time_since_last_chunk:.2f}s > {self.idle_timeout}s). Flushing {self.chunk_count} chunks ({len(self.audio_buffer)} bytes).")
            text = self._process_buffer()
            self.audio_buffer.clear()
            self.chunk_count = 0
            if text:
                print(f"[RealtimeSTT] Idle flush result: '{text}'")
            return text
        
        # Accumulate new chunk
        self.audio_buffer.extend(audio_bytes)
        self.chunk_count += 1
        print(f"[RealtimeSTT] Chunk {self.chunk_count} accumulated. Buffer: {len(self.audio_buffer)} bytes. Time since last: {time_since_last_chunk:.2f}s")

        # Check if we've reached the threshold (lowered to 5 for faster response)
        if self.chunk_count >= self.chunks_to_accumulate:
            print(f"[RealtimeSTT] Threshold reached ({self.chunk_count} chunks, {len(self.audio_buffer)} bytes). Processing buffer.")
            text = self._process_buffer()
            self.audio_buffer.clear()
            self.chunk_count = 0
            if text:
                print(f"[RealtimeSTT] Threshold result: '{text}'")
            return text

        return ""
