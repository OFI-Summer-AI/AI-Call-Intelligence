"""
APScheduler-based orchestrator.

Every CALENDAR_POLL_INTERVAL minutes:
  1. Fetch upcoming meetings from Google Calendar and/or Outlook
  2. For each meeting starting within JOIN_EARLY_SECONDS + poll interval,
     schedule a one-shot job to join & record it
  3. After recording completes, trigger the same processing pipeline
     that runs when a file is manually uploaded through the UI
     (POST /api/process) so results appear in the dashboard identically.
"""

import os
import threading
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.agent.meeting_bot import MeetingBot
from app.agent.calendar_watcher import MeetingEvent
from app.logger import get_logger

logger = get_logger(__name__)

POLL_INTERVAL_MINUTES = int(os.getenv("CALENDAR_POLL_INTERVAL", "5"))
JOIN_EARLY_SECONDS    = int(os.getenv("JOIN_EARLY_SECONDS", "120"))
ENABLE_GOOGLE         = os.getenv("ENABLE_GOOGLE_CALENDAR",  "true").lower()  == "true"
ENABLE_OUTLOOK        = os.getenv("ENABLE_OUTLOOK_CALENDAR", "false").lower() == "true"
SERVER_PORT           = int(os.getenv("PORT", "8080"))


def _trigger_pipeline(recording_path: Path) -> None:
    """
    Trigger the processing pipeline for a completed recording by calling
    POST /api/process — the exact same endpoint the UI upload uses.

    This guarantees:
      - Identical pipeline steps (audio extraction → Whisper → field
        extraction → risk report)
      - Progress tracked in _processing_jobs so the UI shows live status
      - Output files written to OUTPUT_DIR in the same format the
        dashboard reads
    """
    filename = recording_path.name
    url = f"http://localhost:{SERVER_PORT}/api/process"

    logger.info("Triggering pipeline for '%s' via %s", filename, url)
    try:
        resp = requests.post(url, params={"filename": filename}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        job_id = data.get("job_id", filename)
        logger.info("Pipeline started — job_id=%s  status=%s", job_id, data.get("status"))

        # Poll /api/process-status until done (or up to 30 minutes)
        status_url = f"http://localhost:{SERVER_PORT}/api/process-status/{job_id}"
        deadline = time.time() + 1800   # 30 min max
        while time.time() < deadline:
            time.sleep(10)
            try:
                st = requests.get(status_url, timeout=10).json()
                step   = st.get("step", "")
                detail = st.get("detail", "")
                status = st.get("status", "")
                logger.info("Pipeline [%s] step=%-30s  %s", job_id, step, detail)
                if status == "done":
                    logger.info("=== Pipeline complete for '%s' (job_id=%s) ===",
                                filename, job_id)
                    return
                if status == "error":
                    logger.error("Pipeline error for '%s': %s",
                                 filename, st.get("error", "unknown"))
                    return
            except Exception as exc:
                logger.debug("Status poll error (will retry): %s", exc)

        logger.warning("Pipeline timed out after 30 min for '%s'", filename)

    except requests.exceptions.ConnectionError:
        logger.error(
            "Could not reach server at %s — "
            "falling back to direct Pipeline() call", url
        )
        _pipeline_fallback(recording_path)
    except Exception as exc:
        logger.error("Pipeline trigger failed for '%s': %s — falling back", filename, exc)
        _pipeline_fallback(recording_path)


def _pipeline_fallback(recording_path: Path) -> None:
    """
    Direct pipeline call used only if the HTTP trigger fails
    (e.g. server not yet listening).
    """
    logger.info("Running pipeline directly (fallback) for '%s'", recording_path.name)
    try:
        from app.pipeline.pipeline import Pipeline
        result = Pipeline().run(str(recording_path))
        risks = result.get("risk_report", {}).get("risks", [])
        logger.info(
            "=== Pipeline complete (fallback) — %d risk(s): %s ===",
            len(risks), "; ".join(str(r) for r in risks) or "none",
        )
    except Exception as exc:
        logger.error("Pipeline fallback also failed: %s", exc)


def _run_meeting_job(event: MeetingEvent) -> None:
    """Called by scheduler just before a meeting starts."""
    logger.info("=== Meeting job starting: '%s' (platform=%s) ===",
                event.title, event.platform)

    # Playwright's sync API uses greenlets that are tied to the calling thread.
    # APScheduler's ThreadPoolExecutor can cause greenlet context conflicts.
    # Fix: always run the entire browser session in a FRESH dedicated thread.
    recording_result = [None]
    bot_error        = [None]

    def _bot_thread():
        try:
            bot = MeetingBot()
            recording_result[0] = bot.join_and_record(event)
        except Exception as exc:
            bot_error[0] = exc

    t = threading.Thread(target=_bot_thread,
                         name=f"bot_{event.event_id}", daemon=True)
    t.start()
    t.join()   # block until recording + pipeline complete

    if bot_error[0]:
        logger.error("Meeting bot failed for '%s': %s", event.title, bot_error[0])
        return

    recording_path = recording_result[0]
    if recording_path is None:
        logger.error("Meeting bot returned no path for '%s'", event.title)
        return

    if not recording_path.exists():
        logger.warning("Recording file not created: %s", recording_path)
        return

    size_kb = recording_path.stat().st_size // 1024
    logger.info("Recording saved: %s (%d KB)", recording_path.name, size_kb)

    if size_kb == 0:
        logger.warning(
            "Recording is empty — bot was likely in the waiting room and "
            "never admitted, or no audio tracks were established. "
            "File: %s", recording_path.name,
        )
        return

    # Trigger the same pipeline as a manual UI upload
    _trigger_pipeline(recording_path)


class MeetingAgentScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._scheduled_ids: set[str] = set()
        self._watchers = []
        self._lock = threading.Lock()

        if ENABLE_GOOGLE:
            from app.agent.calendar_watcher import GoogleCalendarWatcher
            self._watchers.append(GoogleCalendarWatcher())
            logger.info("Google Calendar watcher enabled")

        if ENABLE_OUTLOOK:
            from app.agent.calendar_watcher import OutlookCalendarWatcher
            self._watchers.append(OutlookCalendarWatcher())
            logger.info("Outlook Calendar watcher enabled")

        if not self._watchers:
            logger.warning(
                "No calendar sources enabled. "
                "Set ENABLE_GOOGLE_CALENDAR=true or ENABLE_OUTLOOK_CALENDAR=true in .env"
            )

    def start(self) -> None:
        self._scheduler.add_job(
            self._poll_calendars,
            trigger=IntervalTrigger(minutes=POLL_INTERVAL_MINUTES),
            id="calendar_poll",
            next_run_time=datetime.now(timezone.utc),   # run immediately on start
        )
        self._scheduler.start()
        logger.info(
            "Meeting agent started — polling every %d min, joining %ds early",
            POLL_INTERVAL_MINUTES, JOIN_EARLY_SECONDS,
        )

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Meeting agent stopped")

    def _poll_calendars(self) -> None:
        now = datetime.now(timezone.utc)
        look_ahead_hours = max(24, (POLL_INTERVAL_MINUTES + 1) / 60 + 1)

        all_events: list[MeetingEvent] = []
        for watcher in self._watchers:
            try:
                events = watcher.get_upcoming_meetings(hours_ahead=int(look_ahead_hours) + 1)
                all_events.extend(events)
            except Exception as exc:
                logger.error("Calendar poll failed: %s", exc)

        logger.info("Calendar poll: %d meeting(s) found", len(all_events))

        with self._lock:
            for event in all_events:
                if event.event_id in self._scheduled_ids:
                    continue   # already scheduled

                if not event.join_url:
                    logger.info("Skipping '%s' — no join link found", event.title)
                    continue

                join_time = event.start_time - timedelta(seconds=JOIN_EARLY_SECONDS)
                if join_time < now:
                    # Meeting already started — join immediately if still running
                    if event.end_time > now:
                        join_time = now + timedelta(seconds=5)
                    else:
                        logger.debug("Skipping past event: '%s'", event.title)
                        continue

                self._scheduler.add_job(
                    _run_meeting_job,
                    trigger=DateTrigger(run_date=join_time),
                    args=[event],
                    id=f"meeting_{event.event_id}",
                    replace_existing=True,
                )
                self._scheduled_ids.add(event.event_id)
                logger.info(
                    "Scheduled join for '%s' at %s (platform=%s)",
                    event.title, join_time.strftime("%H:%M:%S UTC"), event.platform,
                )
