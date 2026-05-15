import argparse
from pathlib import Path
from app.config import UPLOAD_DIR
from app.logger import setup_logging, get_logger
from app.pipeline.pipeline import Pipeline
from app.services.audio_extractor import _resolve_ffmpeg_binary

SUPPORTED_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".wav", ".mp3", ".m4a"}

logger = get_logger(__name__)


def process_file(file_path: str) -> dict:
    pipeline = Pipeline()
    result = pipeline.run(file_path)
    return result


def run_file_mode(filepath: str | None = None):
    ffmpeg_binary = _resolve_ffmpeg_binary()
    print(f"Using FFmpeg: {ffmpeg_binary}")

    input_file = Path(filepath) if filepath else UPLOAD_DIR / "client_call_01.mp4"
    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_file}")

    process_file(str(input_file))


def run_batch_mode(upload_dir: Path | None = None):
    ffmpeg_binary = _resolve_ffmpeg_binary()
    print(f"Using FFmpeg: {ffmpeg_binary}")

    target_dir = upload_dir or UPLOAD_DIR
    files = [f for f in sorted(target_dir.iterdir()) if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not files:
        print(f"No supported media files found in: {target_dir}")
        return

    print(f"\nFound {len(files)} file(s) in {target_dir}:")
    for f in files:
        print(f"  {f.name}")

    results = []
    errors = []
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file_path.name}")
        try:
            result = process_file(str(file_path))
            results.append((file_path.name, result))
        except Exception as exc:
            print(f"  ERROR: {exc}")
            errors.append((file_path.name, str(exc)))

    print(f"\n{'='*60}")
    print(f"Batch complete — {len(results)} succeeded, {len(errors)} failed")
    for name, _ in results:
        risks = _.get("risk_report", {}).get("risks", [])
        print(f"  OK  {name} — {len(risks)} risk(s) flagged")
    for name, err in errors:
        print(f"  ERR {name} — {err}")


def main():
    parser = argparse.ArgumentParser(description="AI Call Intelligence")
    parser.add_argument("--input", type=str, default=None, help="Path to a single media file to process")
    parser.add_argument("--batch", action="store_true", help="Process all media files in the uploads directory")
    parser.add_argument("--uploads-dir", type=str, default=None, help="Override uploads directory for --batch mode")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR")
    args = parser.parse_args()

    setup_logging(level=args.log_level)
    logger.info("AI Call Intelligence starting — log level: %s", args.log_level)

    if args.batch:
        upload_dir = Path(args.uploads_dir) if args.uploads_dir else None
        run_batch_mode(upload_dir)
    else:
        run_file_mode(args.input)


if __name__ == "__main__":
    main()