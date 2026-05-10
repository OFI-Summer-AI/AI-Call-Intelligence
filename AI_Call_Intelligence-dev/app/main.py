import argparse
import time
import shutil
from pathlib import Path
from app.config import (
    UPLOAD_DIR, OBS_WATCH_DIR,
    MEETING_POLL_INTERVAL, MEETING_END_GRACE_SECONDS,
)
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


def run_obs_mode():
    """Watch the OBS recording folder and auto-process new recordings."""
    from app.services.obs_watcher_service import OBSWatcherService

    if not OBS_WATCH_DIR:
        print(
            "ERROR: OBS_WATCH_DIR is not set.\n"
            "Set it in your .env file to the folder where OBS saves recordings.\n"
            "Example:  OBS_WATCH_DIR=C:/Users/you/Videos\n"
        )
        return

    print("=" * 60)
    print("  AI Call Intelligence — OBS Watch Mode")
    print("=" * 60)
    print(f"  Watching : {OBS_WATCH_DIR}")
    print(f"  Uploads  : {UPLOAD_DIR}")
    print("  Record a meeting in OBS. When OBS finishes writing,")
    print("  the pipeline will auto-process the video.")
    print("=" * 60)

    watcher = OBSWatcherService(on_new_recording=process_file)
    watcher.start()
    watcher.wait()


def run_auto_mode():
    """
    Auto-detect meetings, control OBS recording, then process.
    Requires OBS running with WebSocket server enabled.
    """
    from app.services.obs_controller import OBSController
    from app.services.meeting_detector import is_meeting_active

    print("=" * 60)
    print("  AI Call Intelligence — Auto-Record Mode")
    print("=" * 60)
    print("  Connecting to OBS WebSocket…")

    obs = OBSController()
    try:
        obs.connect()
    except Exception as e:
        print(
            f"\nERROR: Could not connect to OBS WebSocket: {e}\n\n"
            "Make sure:\n"
            "  1. OBS Studio is running\n"
            "  2. WebSocket server is enabled (Tools > WebSocket Server Settings)\n"
            "  3. OBS_WS_HOST / OBS_WS_PORT / OBS_WS_PASSWORD are correct in .env\n"
        )
        return

    print(f"  Poll interval     : {MEETING_POLL_INTERVAL}s")
    print(f"  End grace period  : {MEETING_END_GRACE_SECONDS}s")
    print("  Waiting for a meeting to start…")
    print("  (press Ctrl+C to stop)")
    print("=" * 60)

    recording = False
    grace_remaining = 0

    try:
        while True:
            active, title = is_meeting_active()

            if active and not recording:
                print(f"\n[AUTO] Meeting detected: {title}")
                obs.start_recording()
                recording = True
                grace_remaining = 0

            elif active and recording:
                # Still in meeting, reset grace timer
                grace_remaining = 0

            elif not active and recording:
                if grace_remaining == 0:
                    print(f"[AUTO] Meeting window gone — waiting {MEETING_END_GRACE_SECONDS}s grace period…")
                grace_remaining += MEETING_POLL_INTERVAL
                if grace_remaining >= MEETING_END_GRACE_SECONDS:
                    print("[AUTO] Grace period over — stopping recording.")
                    output_path = obs.stop_recording()
                    recording = False
                    grace_remaining = 0
                    if output_path:
                        # Wait for OBS to finish writing the file
                        time.sleep(3)
                        dest = UPLOAD_DIR / Path(output_path).name
                        shutil.copy2(output_path, str(dest))
                        print(f"[AUTO] Copied to: {dest}")
                        print("[AUTO] Running pipeline…")
                        process_file(str(dest))
                        print("\n[AUTO] Waiting for next meeting…")

            time.sleep(MEETING_POLL_INTERVAL)

    except KeyboardInterrupt:
        if recording:
            print("\n[AUTO] Stopping recording before exit…")
            output_path = obs.stop_recording()
            if output_path:
                time.sleep(2)
                dest = UPLOAD_DIR / Path(output_path).name
                shutil.copy2(output_path, str(dest))
                print(f"[AUTO] Saved: {dest}")
                print("[AUTO] Run with --mode file --input <path> to process later.")
        obs.disconnect()
        print("[AUTO] Stopped.")


def main():
    parser = argparse.ArgumentParser(description="AI Call Intelligence")
    parser.add_argument(
        "--mode",
        choices=["file", "obs", "auto"],
        default="file",
        help="'file' = process a video, 'obs' = watch folder, 'auto' = detect meetings & record via OBS",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to video file (only used with --mode file)",
    )
    args = parser.parse_args()

    if args.mode == "auto":
        run_auto_mode()
    elif args.mode == "obs":
        run_obs_mode()
    else:
        run_file_mode(args.input)


if __name__ == "__main__":
    main()