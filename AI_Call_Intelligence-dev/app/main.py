import argparse
from pathlib import Path
from app.config import UPLOAD_DIR
from app.orchestrator.pipeline import Pipeline
from app.services.audio_extractor import _resolve_ffmpeg_binary


def process_file(mp4_path: str):
    """Run the full pipeline on a single video file."""
    pipeline = Pipeline()
    result = pipeline.run(mp4_path)
    print(f"\nPipeline completed for: {mp4_path}\n")
    print(result)
    return result


def run_file_mode(filepath: str | None = None):
    """Process a specific video file (original behaviour)."""
    ffmpeg_binary = _resolve_ffmpeg_binary()
    print(f"Using FFmpeg: {ffmpeg_binary}")

    mp4_file = Path(filepath) if filepath else UPLOAD_DIR / "client_call_01.mp4"

    if not mp4_file.exists():
        raise FileNotFoundError(f"File not found: {mp4_file}")

    process_file(str(mp4_file))


def main():
    parser = argparse.ArgumentParser(description="AI Call Intelligence")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to video file to process",
    )
    args = parser.parse_args()
    run_file_mode(args.input)


if __name__ == "__main__":
    main()