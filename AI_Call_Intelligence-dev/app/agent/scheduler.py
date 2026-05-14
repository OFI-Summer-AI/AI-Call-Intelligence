"""
APScheduler-based orchestrator.

Every CALENDAR_POLL_INTERVAL minutes:
  1. Fetch upcoming meetings from Google Calendar and/or Outlook
  2. For each meeting starting within JOIN_EARLY_SECONDS + poll interval,
     schedule a one-shot job to join & record it
  3. After recording completes, trigger Pipeline 2 automatically
"""

import os
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.agent.meeting_bot import MeetingBot
from app.agent.calendar_watcher import MeetingEvent
from app.logger import get_logger
from app.orchestrator.pipeline import Pipeline

logger = get_logger(__name__)

POLL_INTERVAL_MINUTES = int(os.getenv("CALENDAR_POLL_INTERVAL", "5"))
JOIN_EARLY_SECONDS = int(os.getenv("JOIN_EARLY_SECONDS", "120"))
ENABLE_GOOGLE = os.getenv("ENABLE_GOOGLE_CALENDAR", "true").lower() == "true"
ENABLE_OUTLOOK = os.getenv("ENABLE_OUTLOOK_CALENDAR", "false").lower() == "true"


def _run_meeting_job(event: MeetingEvent) -> None:
    """Called by scheduler just before a meeting starts."""
    logger.info("=== Meeting job starting: '%s' ===", event.title)
    bot = MeetingBot()
    try:
        recording_path = bot.join_and_record(event)
    except Exception as exc:
        logger.error("Meeting bot failed for '%s': %s", event.title, exc)
        return

    if not recording_path.exists() or recording_path.stat().st_size < 1024:
        logger.error(
            "Recording is empty or missing (%s) — skipping Pipeline 2. "
            "Check that WASAPI loopback is enabled in Windows Sound settings "
            "(right-click speaker icon → Sounds → Recording → enable Stereo Mix).",
            recording_path.name,
        )
        return

    logger.info("Recording saved: %s — starting Pipeline 2", recording_path.name)
    try:
        pipeline = Pipeline()
        result = pipeline.run(str(recording_path))
        risks = result.get("risk_report", {}).get("risks", [])
        logger.info(
            "Pipeline complete for '%s' — %d risk(s): %s",
            event.title, len(risks), "; ".join(risks) or "none",
        )
    except Exception as exc:
        logger.error("Pipeline 2 failed for '%s': %s", event.title, exc)


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
            next_run_time=datetime.now(timezone.utc),  # run immediately on start
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
                    continue  # already scheduled

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
