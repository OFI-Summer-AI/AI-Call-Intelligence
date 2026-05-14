import time
from pathlib import Path
from app.config import AUDIO_DIR, OUTPUT_DIR, WHISPER_MODEL_SIZE, ENABLE_DIARIZATION
from app.services.audio_extractor import extract_audio
from app.services.stt_service import STTService
from app.services.transcript_cleaner import clean_segments
from app.services.field_extractor import FieldExtractor
from app.services.risk_report_service import RiskReportService
from app.services.storage_service import StorageService
from app.logger import get_logger

logger = get_logger(__name__)


class Pipeline:
    def __init__(self):
        logger.info("Initialising pipeline")
        self.stt_service = STTService(model_size=WHISPER_MODEL_SIZE)
        self.field_extractor = FieldExtractor()
        self.risk_service = RiskReportService()
        self.storage_service = StorageService()
        logger.info("Pipeline ready")

    def run(self, mp4_path: str) -> dict:
        mp4_path = Path(mp4_path)
        job_name = mp4_path.stem
        pipeline_start = time.perf_counter()

        logger.info("=== Job started: %s ===", job_name)

        audio_path = AUDIO_DIR / f"{job_name}.wav"
        transcript_path = OUTPUT_DIR / f"{job_name}_transcript.json"
        result_path = OUTPUT_DIR / f"{job_name}_result.json"

        # Step 1: Extract audio
        t = time.perf_counter()
        extract_audio(mp4_path, audio_path)
        logger.info("Step 1 done (%.1fs) — audio extraction", time.perf_counter() - t)

        # Step 2: STT
        t = time.perf_counter()
        stt_result = self.stt_service.transcribe(audio_path)
        cleaned_segments = clean_segments(stt_result["segments"])
        logger.info("Step 2 done (%.1fs) — STT, %d segments", time.perf_counter() - t, len(cleaned_segments))

        # Step 3: Diarization (optional)
        speaker_segments = []
        if ENABLE_DIARIZATION:
            t = time.perf_counter()
            try:
                from app.services.diarization_service import DiarizationService
                diarization_service = DiarizationService()
                speaker_segments = diarization_service.diarize(audio_path)
                logger.info("Step 3 done (%.1fs) — diarization, %d speaker segments", time.perf_counter() - t, len(speaker_segments))
            except Exception as exc:
                logger.warning("Diarization failed, skipping: %s", exc)
                speaker_segments = []
        else:
            logger.debug("Step 3 skipped — diarization disabled")

        # Step 4: Field extraction
        t = time.perf_counter()
        extracted_fields = self.field_extractor.extract(cleaned_segments)
        logger.info("Step 4 done (%.1fs) — field extraction", time.perf_counter() - t)

        # Step 5: Risk report
        t = time.perf_counter()
        risk_report = self.risk_service.generate(extracted_fields, cleaned_segments)
        logger.info("Step 5 done (%.1fs) — risk report", time.perf_counter() - t)

        # Step 6: Save outputs
        final_output = {
            "job_id": job_name,
            "source_file": str(mp4_path),
            "audio_file": str(audio_path),
            "transcript": cleaned_segments,
            "speaker_segments": speaker_segments,
            "extracted_fields": extracted_fields,
            "risk_report": risk_report,
        }

        self.storage_service.save_json(
            {"language": stt_result.get("language"), "segments": cleaned_segments},
            transcript_path,
        )
        self.storage_service.save_json(final_output, result_path)

        elapsed = time.perf_counter() - pipeline_start
        logger.info("=== Job complete: %s — total %.1fs ===", job_name, elapsed)
        return final_output