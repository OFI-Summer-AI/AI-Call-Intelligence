import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.config import OBS_WATCH_DIR, UPLOAD_DIR

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".flv", ".avi", ".mov", ".webm", ".ts"}
STABLE_WAIT_SECONDS = 3
STABLE_CHECK_INTERVAL = 1


class _RecordingHandler(FileSystemEventHandler):
    """Detects new video files in the OBS output folder."""

    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in VIDEO_EXTENSIONS:
            self._wait_until_stable(path)
            self._callback(path)

    def on_moved(self, event):
        path = Path(event.dest_path)
        if path.suffix.lower() in VIDEO_EXTENSIONS:
            self._wait_until_stable(path)
            self._callback(path)

    @staticmethod
    def _wait_until_stable(path: Path):
        """Wait until the file size stops changing (OBS finished writing)."""
        previous_size = -1
        while True:
            try:
                current_size = path.stat().st_size
            except OSError:
                return
            if current_size == previous_size and current_size > 0:
                return
            previous_size = current_size
            time.sleep(STABLE_CHECK_INTERVAL)


class OBSWatcherService:
    """
    Watches the OBS recording output folder.
    When a new video appears, copies it to the uploads directory
    and calls the provided callback with the destination path.
    """

    def __init__(self, on_new_recording):
        self._on_new_recording = on_new_recording
        self._observer = Observer()

    def start(self):
        watch_dir = Path(OBS_WATCH_DIR)
        if not watch_dir.exists():
            raise FileNotFoundError(
                f"OBS watch directory does not exist: {watch_dir}\n"
                "Set OBS_WATCH_DIR in .env to your OBS recording output folder."
            )

        handler = _RecordingHandler(self._handle_file)
        self._observer.schedule(handler, str(watch_dir), recursive=False)
        self._observer.start()
        print(f"[OBS Watcher] Monitoring: {watch_dir}")
        print("[OBS Watcher] Waiting for new recordings… (press Ctrl+C to stop)")

    def _handle_file(self, source_path: Path):
        dest = UPLOAD_DIR / source_path.name
        print(f"[OBS Watcher] New recording detected: {source_path.name}")
        shutil.copy2(str(source_path), str(dest))
        print(f"[OBS Watcher] Copied to: {dest}")
        self._on_new_recording(str(dest))

    def wait(self):
        try:
            while self._observer.is_alive():
                self._observer.join(timeout=1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._observer.stop()
        self._observer.join()
        print("[OBS Watcher] Stopped.")
