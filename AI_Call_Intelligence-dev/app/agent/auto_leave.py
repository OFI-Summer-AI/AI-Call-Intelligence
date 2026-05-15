import asyncio
import logging
import os
import httpx
from datetime import datetime, timezone
from typing import Callable, Awaitable

logger = logging.getLogger("auto_leave")

POLL_INTERVAL_SEC = int(os.getenv("BOT_POLL_INTERVAL_SEC", "10"))
GRACE_PERIOD_SEC  = int(os.getenv("BOT_GRACE_SECONDS", "30"))

async def watch_and_leave(
    session_id              : str,
    platform                : str,           # "meet" | "zoom" | "teams"
    get_participant_count   : Callable[[], Awaitable[int]],
    leave_meeting           : Callable[[], Awaitable[None]],
    run_pipeline            : Callable[[str], Awaitable[dict]],
    cancel_event            : asyncio.Event | None = None,
) -> None:
    """
    Polls participant count every POLL_INTERVAL_SEC seconds.
    
    EMPTY defined as: count == 0  OR  count == 1 (only the bot itself).
    
    Grace period logic:
      - First empty poll  → start grace countdown, log WARNING
      - Each subsequent empty poll → log remaining grace time
      - If participant rejoins during grace → reset counter, log INFO
      - Grace period expires → execute leave sequence
    
    Cancel logic:
      - If cancel_event is set externally (manual stop) → exit loop cleanly
        without calling leave_meeting (caller handles that separately)
    """

    empty_streak   = 0                          # consecutive empty polls
    max_streak     = GRACE_PERIOD_SEC // POLL_INTERVAL_SEC
    rejoined_once  = False                      # for logging context

    logger.info(f"[auto_leave] STARTED  session={session_id} platform={platform} "
                f"poll={POLL_INTERVAL_SEC}s grace={GRACE_PERIOD_SEC}s")

    while True:
        # ── Check for external cancellation ──────────────────────────────
        if cancel_event and cancel_event.is_set():
            logger.info(f"[auto_leave] CANCELLED externally  session={session_id}")
            return

        await asyncio.sleep(POLL_INTERVAL_SEC)

        # ── Poll participant count ────────────────────────────────────────
        try:
            count = await get_participant_count()
        except Exception as exc:
            logger.warning(f"[auto_leave] poll ERROR session={session_id}: {exc}")
            continue

        # ── Meeting is active ─────────────────────────────────────────────
        if count > 1:
            if empty_streak > 0:
                logger.info(f"[auto_leave] participant REJOINED  session={session_id} "
                            f"count={count} — grace reset")
                rejoined_once = True
            empty_streak = 0
            logger.info(f"[auto_leave] ACTIVE  session={session_id} "
                        f"platform={platform} participants={count}")
            continue

        # ── Meeting is empty ──────────────────────────────────────────────
        empty_streak += 1
        elapsed_sec  = empty_streak * POLL_INTERVAL_SEC
        remaining    = GRACE_PERIOD_SEC - elapsed_sec

        if empty_streak == 1:
            logger.warning(f"[auto_leave] EMPTY DETECTED  session={session_id} "
                           f"count={count} — grace period starting ({GRACE_PERIOD_SEC}s)")
        else:
            logger.warning(f"[auto_leave] STILL EMPTY  session={session_id} "
                           f"elapsed={elapsed_sec}s remaining={max(0,remaining)}s")

        # ── Grace period expired ──────────────────────────────────────────
        if empty_streak >= max_streak:
            logger.warning(f"[auto_leave] GRACE EXPIRED  session={session_id} "
                           f"— triggering auto-leave sequence")
            await _execute_leave_sequence(
                session_id   = session_id,
                platform     = platform,
                leave_meeting= leave_meeting,
                run_pipeline = run_pipeline,
                reason       = "all_participants_left",
            )
            return


async def _execute_leave_sequence(
    session_id    : str,
    platform      : str,
    leave_meeting : Callable[[], Awaitable[None]],
    run_pipeline  : Callable[[str], Awaitable[dict]],
    reason        : str,
) -> None:
    """
    Full ordered shutdown:
      Step 1 — Stop audio recording
      Step 2 — Leave / end the meeting on the platform
      Step 3 — Run transcription + field extraction + risk report
      Step 4 — Save result JSON
      Step 5 — Notify FastAPI backend
      Step 6 — Log completion
    """
    ended_at = datetime.now(timezone.utc).isoformat()

    # Step 1: Platform leave
    logger.info(f"[auto_leave] Step 1/5 — leaving {platform} meeting  session={session_id}")
    try:
        await leave_meeting()
        logger.info(f"[auto_leave] Step 1/5 — left successfully")
    except Exception as exc:
        logger.error(f"[auto_leave] Step 1/5 — leave FAILED: {exc} (continuing pipeline)")

    # Step 2: Run full pipeline (transcribe → extract → risk)
    logger.info(f"[auto_leave] Step 2/5 — running analysis pipeline  session={session_id}")
    try:
        result = await run_pipeline(session_id)
        job_id = result.get("job_id", session_id)
        logger.info(f"[auto_leave] Step 2/5 — pipeline complete  job_id={job_id}")
    except Exception as exc:
        logger.error(f"[auto_leave] Step 2/5 — pipeline FAILED: {exc}")
        job_id = session_id
        result = {}

    # Step 3: Notify FastAPI so dashboard updates
    logger.info(f"[auto_leave] Step 3/5 — notifying backend  session={session_id}")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                "http://localhost:8000/api/meeting-ended",
                json={
                    "session_id" : session_id,
                    "job_id"     : job_id,
                    "ended_at"   : ended_at,
                    "reason"     : reason,
                    "platform"   : "unknown",
                    "auto_left"  : True,
                },
            )
        logger.info(f"[auto_leave] Step 3/5 — backend notified")
    except Exception as exc:
        logger.warning(f"[auto_leave] Step 3/5 — notify FAILED: {exc}")

    # Step 4: Update shared AGENT_STATE (imported from routes)
    logger.info(f"[auto_leave] Step 4/5 — updating agent state")
    try:
        from app.api.routes import AGENT_STATE, SESSION_REGISTRY
        AGENT_STATE["status"]           = "idle"
        AGENT_STATE["current_session"]  = None
        SESSION_REGISTRY[session_id]    = {
            "status"    : "completed",
            "job_id"    : job_id,
            "ended_at"  : ended_at,
            "reason"    : reason,
        }
    except Exception as exc:
        logger.warning(f"[auto_leave] Step 4/5 — state update failed: {exc}")

    # Step 5: Done
    logger.info(
        f"[auto_leave] ✓ AUTO-LEAVE COMPLETE  "
        f"session={session_id} job_id={job_id} reason={reason} ended_at={ended_at}"
    )