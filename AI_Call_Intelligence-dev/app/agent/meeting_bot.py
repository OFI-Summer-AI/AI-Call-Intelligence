"""
Playwright-based meeting bot.

Joins Zoom / Google Meet / Microsoft Teams in a headed Chromium browser,
records system audio via ffmpeg WASAPI loopback while the meeting runs,
then returns the path to the saved WAV recording.
"""

import os
import subprocess
import time
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

from app.agent.link_extractor import zoom_web_url
from app.agent.calendar_watcher import MeetingEvent
from app.config import UPLOAD_DIR
from app.logger import get_logger

logger = get_logger(__name__)

BOT_NAME = os.getenv("BOT_NAME", "AI Notetaker")
JOIN_TIMEOUT_MS = 30_000
PAGE_TIMEOUT_MS = 60_000


def _safe_filename(title: str) -> str:
    """Convert meeting title to a filename-safe string (no spaces or special chars)."""
    name = re.sub(r"[^\w]", "_", title)          # replace all non-alphanumeric with _
    name = re.sub(r"_+", "_", name).strip("_")   # collapse multiple underscores
    return name[:40]


class MeetingBot:
    def __init__(self):
        self._ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if not self._ffmpeg:
            raise RuntimeError("ffmpeg not found in PATH")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def join_and_record(self, event: MeetingEvent) -> Path:
        now = datetime.now(timezone.utc)
        duration_secs = max(
            int((event.end_time - now).total_seconds()) + 180,
            60,
        )

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        safe_title = _safe_filename(event.title)
        filename = f"{safe_title}_{timestamp}.wav"
        output_path = UPLOAD_DIR / filename

        logger.info(
            "Joining [%s] '%s' — platform=%s, duration=%ds, file=%s",
            event.source, event.title, event.platform, duration_secs, filename,
        )

        ffmpeg_proc = self._start_audio_recording(output_path)
        try:
            self._run_browser_session(event, duration_secs)
        finally:
            self._stop_audio_recording(ffmpeg_proc, output_path)

        return output_path

    # ------------------------------------------------------------------
    # Audio recording via ffmpeg WASAPI loopback
    # ------------------------------------------------------------------

    def _start_audio_recording(self, output_path: Path) -> subprocess.Popen:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try WASAPI loopback first (captures all system audio output)
        # Empty string "" = default render device loopback
        cmd = [
            self._ffmpeg, "-y",
            "-f", "wasapi",
            "-loopback",
            "-i", "",
            "-ar", "16000",
            "-ac", "1",
            str(output_path),
        ]
        logger.info("Starting WASAPI loopback audio capture -> %s", output_path.name)

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2)  # wait for ffmpeg to open the device

        # Check it actually started
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode(errors="ignore")
            logger.warning("WASAPI loopback failed, retrying with device index 0: %s", stderr[:200])
            # Fallback: try with explicit device index
            cmd[cmd.index("")] = "0"
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(2)

        if proc.poll() is not None:
            stderr = proc.stderr.read().decode(errors="ignore")
            logger.error("Audio capture failed to start: %s", stderr[:300])
        else:
            logger.info("Audio capture running (pid=%d)", proc.pid)

        return proc

    def _stop_audio_recording(self, proc: subprocess.Popen, output_path: Path) -> None:
        if proc.poll() is None:
            try:
                proc.stdin.write(b"q")
                proc.stdin.flush()
            except Exception:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        size_kb = output_path.stat().st_size // 1024 if output_path.exists() else 0
        if size_kb == 0:
            logger.warning(
                "Recording is 0 KB — WASAPI loopback may not be supported on this device. "
                "Check that 'Stereo Mix' or a loopback device is enabled in Windows Sound settings."
            )
        else:
            logger.info("Audio recording saved — %d KB at %s", size_kb, output_path.name)

    # ------------------------------------------------------------------
    # Browser session
    # ------------------------------------------------------------------

    def _run_browser_session(self, event: MeetingEvent, duration_secs: int) -> None:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=False,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = browser.new_context(
                permissions=["microphone", "camera"],
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            # Track if page closes unexpectedly
            page_closed = [False]
            page.on("close", lambda: page_closed.__setitem__(0, True))

            try:
                if event.platform == "meet":
                    self._join_google_meet(page, event.join_url, page_closed)
                elif event.platform == "zoom":
                    self._join_zoom(page, event.join_url)
                elif event.platform == "teams":
                    self._join_teams(page, event.join_url)
                else:
                    logger.warning("Unknown platform '%s', navigating directly", event.platform)
                    page.goto(event.join_url, timeout=PAGE_TIMEOUT_MS)

                if not page_closed[0]:
                    logger.info("In meeting — waiting up to %ds", duration_secs)
                    self._wait_for_meeting_end(page, event.platform, duration_secs, page_closed)

            except Exception as exc:
                logger.error("Browser session error: %s", exc)
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Platform-specific join handlers
    # ------------------------------------------------------------------

    def _join_google_meet(self, page: Page, url: str, page_closed: list) -> None:
        logger.info("Joining Google Meet: %s", url)
        page.goto(url, timeout=PAGE_TIMEOUT_MS)

        # Wait for page to fully settle
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PWTimeout:
            pass

        if page_closed[0]:
            logger.warning("Meet page closed immediately after navigation")
            return

        # Dismiss any "Got it" / "Dismiss" overlays
        for sel in ["button:has-text('Got it')", "button:has-text('Dismiss')",
                    "[aria-label='Close']"]:
            try:
                page.click(sel, timeout=2000)
            except PWTimeout:
                pass

        # Click "Join as a guest" if present (unauthenticated flow)
        for sel in ["button:has-text('Join as a guest')", "a:has-text('Join as a guest')"]:
            try:
                page.click(sel, timeout=3000)
                logger.info("Clicked 'Join as a guest'")
                time.sleep(1)
                break
            except PWTimeout:
                pass

        # Enter name in the pre-join name field (guest flow only)
        for sel in ["input[placeholder*='name' i]", "input[aria-label*='name' i]",
                    "input[aria-label*='Your name' i]"]:
            try:
                field = page.wait_for_selector(sel, timeout=4000)
                field.triple_click()
                field.fill(BOT_NAME)
                logger.info("Entered bot name: %s", BOT_NAME)
                break
            except PWTimeout:
                pass  # signed-in flow has no name field

        # Mute mic and camera
        for sel in ["[aria-label*='Turn off microphone' i]",
                    "[data-is-muted='false'][aria-label*='microphone' i]"]:
            try:
                page.click(sel, timeout=2000)
            except PWTimeout:
                pass
        for sel in ["[aria-label*='Turn off camera' i]",
                    "[data-is-muted='false'][aria-label*='camera' i]"]:
            try:
                page.click(sel, timeout=2000)
            except PWTimeout:
                pass

        # Click join / ask to join
        joined = False
        for sel in ["button:has-text('Ask to join')", "button:has-text('Join now')",
                    "button:has-text('Join')", "[jsname='Qx7uuf']"]:
            try:
                page.click(sel, timeout=JOIN_TIMEOUT_MS)
                logger.info("Clicked join on Google Meet")
                joined = True
                break
            except PWTimeout:
                continue

        if not joined:
            logger.warning("Could not find join button on Google Meet")

    def _join_zoom(self, page: Page, url: str) -> None:
        web_url = zoom_web_url(url)
        logger.info("Joining Zoom (web): %s", web_url)
        page.goto(web_url, timeout=PAGE_TIMEOUT_MS)
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PWTimeout:
            pass

        for sel in ["#inputname", "input[placeholder*='name' i]", "input[id*='name' i]"]:
            try:
                field = page.wait_for_selector(sel, timeout=5000)
                field.fill(BOT_NAME)
                break
            except PWTimeout:
                pass

        for sel in ["#joinBtn", "button:has-text('Join')", "button:has-text('Join Meeting')"]:
            try:
                page.click(sel, timeout=JOIN_TIMEOUT_MS)
                logger.info("Clicked join on Zoom")
                break
            except PWTimeout:
                continue

        for sel in ["button:has-text('Join Audio')", "button:has-text('Join by Computer Audio')"]:
            try:
                page.click(sel, timeout=8000)
            except PWTimeout:
                pass

    def _join_teams(self, page: Page, url: str) -> None:
        logger.info("Joining Microsoft Teams: %s", url)
        page.goto(url, timeout=PAGE_TIMEOUT_MS)
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except PWTimeout:
            pass

        for sel in ["button:has-text('Continue on this browser')",
                    "a:has-text('Continue on this browser')",
                    "[data-tid='joinOnWeb']"]:
            try:
                page.click(sel, timeout=8000)
                time.sleep(2)
                break
            except PWTimeout:
                pass

        for sel in ["input[placeholder*='name' i]",
                    "input[data-tid='prejoin-display-name-input']"]:
            try:
                field = page.wait_for_selector(sel, timeout=8000)
                field.fill(BOT_NAME)
                break
            except PWTimeout:
                pass

        for sel in ["[id*='microphone-button']", "button[aria-label*='Microphone' i]"]:
            try:
                page.click(sel, timeout=3000)
            except PWTimeout:
                pass

        for sel in ["button:has-text('Join now')", "[data-tid='prejoin-join-button']",
                    "button:has-text('Join')"]:
            try:
                page.click(sel, timeout=JOIN_TIMEOUT_MS)
                logger.info("Clicked join on Teams")
                break
            except PWTimeout:
                continue

    # ------------------------------------------------------------------
    # Meeting end detection
    # ------------------------------------------------------------------

    def _wait_for_meeting_end(self, page: Page, platform: str,
                               max_secs: int, page_closed: list) -> None:
        end_signals = {
            "meet": ["you've left the call", "the call has ended", "return to home screen"],
            "zoom": ["meeting is over", "this meeting has ended", "thank you for joining"],
            "teams": ["the meeting has ended", "you left the meeting"],
        }
        signals = end_signals.get(platform, [])
        poll_interval = 15
        elapsed = 0

        while elapsed < max_secs:
            time.sleep(poll_interval)
            elapsed += poll_interval

            if page_closed[0]:
                logger.info("Page closed — meeting ended")
                return

            try:
                content = page.content().lower()
                for signal in signals:
                    if signal in content:
                        logger.info("Meeting end detected: '%s'", signal)
                        return
            except Exception:
                logger.warning("Could not read page — assuming meeting ended")
                return

            remaining = max_secs - elapsed
            if elapsed % 300 < poll_interval:
                logger.info("Still in meeting — %ds remaining", remaining)

        logger.info("Max recording duration reached (%ds)", max_secs)
