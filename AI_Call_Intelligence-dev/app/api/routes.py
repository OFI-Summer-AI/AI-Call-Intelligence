import asyncio, os, signal, subprocess
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Shared mutable state — single source of truth for Streamlit polling
AGENT_STATE = {
    "status"          : "stopped",   # "stopped"|"starting"|"running"|"idle"
    "pid"             : None,
    "started_at"      : None,
    "current_session" : None,
    "sessions_handled": 0,
}

SESSION_REGISTRY: dict[str, dict] = {}
# { session_id: { status, job_id, participants, ended_at, reason } }

_watcher_tasks: dict[str, asyncio.Task] = {}
# { session_id: asyncio.Task } — so we can cancel watchers externally




# ── Agent lifecycle ──────────────────────────────────────────────

@router.post("/api/agent-start")
async def agent_start():
    if AGENT_STATE["status"] == "running":
        return {"status": "already_running", "pid": AGENT_STATE["pid"]}
    proc = subprocess.Popen(
        ["python", "-m", "app.main_agent"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    AGENT_STATE.update({
        "status"    : "starting",
        "pid"       : proc.pid,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "starting", "pid": proc.pid}

@router.get("/api/agent-status")
async def agent_status():
    pid = AGENT_STATE.get("pid")
    current_session = AGENT_STATE.get("current_session")
    status = AGENT_STATE.get("status", "stopped")

    # Check subprocess-based agent (started via agent-start)
    pid_alive = False
    if pid:
        try:
            os.kill(pid, 0)
            pid_alive = True
        except (ProcessLookupError, PermissionError):
            pid_alive = False
        if not pid_alive and status == "running":
            AGENT_STATE["status"] = "stopped"
            status = "stopped"

    # For asyncio-task joins (join-now), there is no PID —
    # trust AGENT_STATE directly when a session is active.
    task_alive = (current_session is not None and status in ("running", "starting"))

    uptime = 0
    started_at = AGENT_STATE.get("started_at")
    if started_at and (pid_alive or task_alive):
        uptime = int(
            (datetime.now(timezone.utc) -
             datetime.fromisoformat(started_at)).total_seconds()
        )

    effective_status = status if (pid_alive or task_alive) else (
        status if status in ("idle", "stopped") else "stopped"
    )

    return {
        "status"           : effective_status,
        "pid"              : pid if pid_alive else None,
        "started_at"       : started_at,
        "uptime_sec"       : uptime,
        "sessions_handled" : AGENT_STATE.get("sessions_handled", 0),
        "current_session"  : current_session,
    }

@router.post("/api/agent-stop")
async def agent_stop():
    pid = AGENT_STATE.get("pid")
    if not pid:
        return {"status": "already_stopped"}
    try:
        os.kill(pid, signal.SIGTERM)
        await asyncio.sleep(5)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)   # force kill if still alive
        except ProcessLookupError:
            pass                            # already dead after SIGTERM
    except ProcessLookupError:
        pass
    AGENT_STATE.update({"status":"stopped","pid":None,"current_session":None})
    return {"status": "stopped", "message": "Agent stopped cleanly"}

# ── Participant polling (called by auto_leave watcher internally) ─

@router.get("/api/participants/{session_id}")
async def get_participants(session_id: str):
    """
    Returns current participant count for a live session.
    In production: query the platform SDK / Playwright page state.
    For now: read from SESSION_REGISTRY or return a mock.
    """
    session = SESSION_REGISTRY.get(session_id, {})
    count   = session.get("participants", 0)
    names   = session.get("participant_names", [])
    return {"count": count, "names": names, "session_id": session_id}

@router.post("/api/participants/{session_id}/update")
async def update_participants(session_id: str, body: dict):
    """
    Called by the bot process whenever participant list changes.
    Body: { count: int, names: list[str] }
    """
    if session_id not in SESSION_REGISTRY:
        SESSION_REGISTRY[session_id] = {}
    SESSION_REGISTRY[session_id]["participants"]       = body.get("count", 0)
    SESSION_REGISTRY[session_id]["participant_names"]  = body.get("names", [])
    return {"ok": True}

# ── Auto-leave trigger ───────────────────────────────────────────

class MeetingEndedBody(BaseModel):
    session_id : str
    job_id     : str
    ended_at   : str
    reason     : str
    platform   : str = "unknown"
    auto_left  : bool = True

@router.post("/api/meeting-ended")
async def meeting_ended(body: MeetingEndedBody):
    SESSION_REGISTRY[body.session_id] = {
        "status"   : "completed",
        "job_id"   : body.job_id,
        "ended_at" : body.ended_at,
        "reason"   : body.reason,
        "auto_left": body.auto_left,
    }
    AGENT_STATE["status"]           = "idle"
    AGENT_STATE["current_session"]  = None
    AGENT_STATE["sessions_handled"] = AGENT_STATE.get("sessions_handled", 0) + 1
    return {"ok": True, "job_id": body.job_id}

# ── Start watcher when bot joins ─────────────────────────────────

@router.post("/api/start-watcher/{session_id}")
async def start_watcher(session_id: str, platform: str = "meet"):
    """
    Spawns the auto_leave watcher as a background asyncio task.
    Call this immediately after the bot successfully joins a meeting.
    """
    from app.agent.auto_leave import watch_and_leave
    from app.services.pipeline_runner import run_full_pipeline

    cancel_ev = asyncio.Event()

    async def _get_count():
        info = SESSION_REGISTRY.get(session_id, {})
        return info.get("participants", 0)

    async def _leave():
        # Add platform-specific leave logic here
        SESSION_REGISTRY.setdefault(session_id, {})["status"] = "leaving"

    async def _pipeline(sid):
        return await run_full_pipeline(sid)

    task = asyncio.create_task(
        watch_and_leave(
            session_id            = session_id,
            platform              = platform,
            get_participant_count = _get_count,
            leave_meeting         = _leave,
            run_pipeline          = _pipeline,
            cancel_event          = cancel_ev,
        ),
        name=f"watcher_{session_id}",
    )
    _watcher_tasks[session_id] = task
    SESSION_REGISTRY[session_id] = SESSION_REGISTRY.get(session_id, {})
    SESSION_REGISTRY[session_id]["cancel_event"] = cancel_ev
    return {"ok": True, "message": f"Watcher started for {session_id}"}

@router.post("/api/cancel-watcher/{session_id}")
async def cancel_watcher(session_id: str):
    """Cancel the auto-leave watcher (e.g. manual stop clicked)."""
    ev = SESSION_REGISTRY.get(session_id, {}).get("cancel_event")
    if ev:
        ev.set()
    task = _watcher_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()
    return {"ok": True}


# ── Manual join-now (triggered from UI) ─────────────────────────

class JoinNowBody(BaseModel):
    meeting_url : str
    platform    : str = "meet"
    title       : str = "Manual Join"


@router.post("/api/join-now")
async def join_now(body: JoinNowBody):
    """
    Directly start the meeting bot for a given URL without needing the calendar.
    Returns immediately; the bot runs as a background asyncio task.
    """
    from app.agent.meeting_bot import MeetingBot
    from app.agent.calendar_watcher import MeetingEvent

    if AGENT_STATE.get("status") in ("running", "starting"):
        return {"error": "agent_already_running", "status": AGENT_STATE["status"]}

    now        = datetime.now(timezone.utc)
    session_id = now.strftime("%Y%m%d_%H%M%S")

    event = MeetingEvent(
        event_id   = session_id,
        title      = body.title,
        start_time = now,
        end_time   = now + timedelta(hours=2),
        join_url   = body.meeting_url,
        platform   = body.platform,
        source     = "manual",
    )

    AGENT_STATE.update({
        "status"          : "starting",
        "started_at"      : now.isoformat(),
        "current_session" : session_id,
    })
    SESSION_REGISTRY[session_id] = {"status": "joining", "platform": body.platform}

    loop = asyncio.get_event_loop()

    async def _run():
        AGENT_STATE["status"] = "running"
        recording_path = None
        try:
            recording_path = await loop.run_in_executor(
                None, lambda: MeetingBot().join_and_record(event)
            )
            SESSION_REGISTRY[session_id]["status"] = "processing"
        except Exception as exc:
            logger.error("join-now bot error for session %s: %s", session_id, exc)
            SESSION_REGISTRY[session_id].update({"status": "error", "error": str(exc)})
        finally:
            AGENT_STATE.update({"status": "idle", "current_session": None})
            AGENT_STATE["sessions_handled"] = AGENT_STATE.get("sessions_handled", 0) + 1

        # Auto-run analysis pipeline on the recording
        if recording_path and recording_path.exists() and recording_path.stat().st_size > 1024:
            logger.info("join-now: recording ready (%d KB) — running pipeline",
                        recording_path.stat().st_size // 1024)
            SESSION_REGISTRY[session_id]["status"] = "analysing"
            try:
                from app.pipeline.pipeline import Pipeline
                await loop.run_in_executor(None, lambda: Pipeline().run(str(recording_path)))
                SESSION_REGISTRY[session_id]["status"] = "done"
                logger.info("join-now: pipeline complete for %s", recording_path.name)
            except Exception as exc:
                logger.error("join-now: pipeline failed for %s: %s", recording_path.name, exc)
                SESSION_REGISTRY[session_id].update({"status": "pipeline_error", "error": str(exc)})
        elif recording_path is not None:
            logger.warning("join-now: recording too small or missing — skipping pipeline (%s)",
                           recording_path)
            SESSION_REGISTRY[session_id]["status"] = "no_audio"

    asyncio.create_task(_run(), name=f"join_now_{session_id}")
    return {"session_id": session_id, "status": "starting"}


# ── Upcoming meetings (calendar feed for the UI) ─────────────────

@router.get("/api/upcoming-meetings")
async def upcoming_meetings():
    """
    Fetch the next 24 h of calendar meetings that have a join link.
    Queries Google Calendar and/or Outlook directly (no agent subprocess needed).
    """
    enable_google  = os.getenv("ENABLE_GOOGLE_CALENDAR",  "true").lower()  == "true"
    enable_outlook = os.getenv("ENABLE_OUTLOOK_CALENDAR", "false").lower() == "true"

    def _fetch():
        from app.agent.calendar_watcher import GoogleCalendarWatcher, OutlookCalendarWatcher
        results = []
        if enable_google:
            try:
                results.extend(GoogleCalendarWatcher().get_upcoming_meetings(hours_ahead=24))
            except Exception as exc:
                logger.warning("Google Calendar fetch failed: %s", exc)
        if enable_outlook and os.getenv("MICROSOFT_CLIENT_ID", ""):
            try:
                results.extend(OutlookCalendarWatcher().get_upcoming_meetings(hours_ahead=24))
            except Exception as exc:
                logger.warning("Outlook Calendar fetch failed: %s", exc)
        return results

    loop = asyncio.get_event_loop()
    events = await loop.run_in_executor(None, _fetch)

    return [
        {
            "event_id"   : e.event_id,
            "title"      : e.title,
            "start_time" : e.start_time.isoformat(),
            "end_time"   : e.end_time.isoformat(),
            "join_url"   : e.join_url,
            "platform"   : e.platform,
            "source"     : e.source,
        }
        for e in events
    ]