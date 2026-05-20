"""
Playwright-based meeting bot.

Joins Zoom / Google Meet / Microsoft Teams in a headed Chrome browser,
intercepts the WebRTC audio stream via an injected MediaRecorder (no
WASAPI loopback needed), and saves a WAV recording after the meeting.

Echo fix: --mute-audio silences Chrome's speaker output so the bot's
browser never plays audio through the user's physical speakers.
Audio is captured directly from the WebRTC peer-connection tracks and
shipped to Python as base64 WebM chunks via expose_function.
"""

import base64
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

GOOGLE_ACCOUNT_EMAIL    = os.getenv("GOOGLE_ACCOUNT_EMAIL", "")
GOOGLE_ACCOUNT_PASSWORD = os.getenv("GOOGLE_ACCOUNT_PASSWORD", "")

# ---------------------------------------------------------------------------
# JS injected into every page — intercepts RTCPeerConnection audio tracks
# and ships them to Python via window.pyReceiveAudioChunk(base64_webm_chunk).
#
# Echo prevention: instead of --mute-audio (which breaks the AudioContext),
# each incoming track is split: one path goes to the speaker through a
# gain=0 node (completely silent), the other path goes to the MediaRecorder
# at full volume. No echo, full-fidelity recording.
# ---------------------------------------------------------------------------
_WEBRTC_CAPTURE_SCRIPT = r"""
(function () {
    var OrigPC = window.RTCPeerConnection;
    if (!OrigPC) return;

    var audioCtx = null, silentGain = null, mergedDest = null, recorder = null;

    function ensureCtx() {
        if (audioCtx) return;
        audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        // silentGain routes audio to ctx.destination at volume 0 — prevents echo
        // without breaking the AudioContext render loop.
        silentGain = audioCtx.createGain();
        silentGain.gain.value = 0;
        silentGain.connect(audioCtx.destination);
        mergedDest = audioCtx.createMediaStreamDestination();
    }

    function addTrack(track) {
        ensureCtx();
        try {
            var s = new MediaStream([track]);
            var src = audioCtx.createMediaStreamSource(s);
            src.connect(silentGain);   // to speaker, gain=0 → silent (no echo)
            src.connect(mergedDest);   // to recorder, full volume
        } catch (e) {}
    }

    function startRecorder() {
        if (recorder || !mergedDest) return;
        var mimes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
        var mime = mimes.find(function(m) { return MediaRecorder.isTypeSupported(m); }) || '';
        recorder = new MediaRecorder(mergedDest.stream, mime ? { mimeType: mime } : {});
        recorder.ondataavailable = function (e) {
            if (!e.data || e.data.size === 0) return;
            e.data.arrayBuffer().then(function (buf) {
                var u8 = new Uint8Array(buf);
                var s = '', chunk = 8192;
                for (var i = 0; i < u8.length; i += chunk)
                    s += String.fromCharCode.apply(null, u8.subarray(i, Math.min(i + chunk, u8.length)));
                try { window.pyReceiveAudioChunk(btoa(s)); } catch (_) {}
            }).catch(function() {});
        };
        recorder.start(2000);
    }

    window.RTCPeerConnection = function () {
        var pc = new (Function.prototype.bind.apply(OrigPC, [null].concat(Array.prototype.slice.call(arguments))))();
        pc.addEventListener('track', function (e) {
            if (e.track.kind !== 'audio') return;
            addTrack(e.track);
            setTimeout(startRecorder, 300);
        });
        return pc;
    };
    window.RTCPeerConnection.prototype = OrigPC.prototype;
    Object.defineProperty(window.RTCPeerConnection, 'name', { value: 'RTCPeerConnection' });
})();
"""


def _safe_filename(title: str) -> str:
    name = re.sub(r"[^\w]", "_", title)
    name = re.sub(r"_+", "_", name).strip("_")
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

        self._run_browser_session(event, duration_secs, output_path)
        return output_path

    # ------------------------------------------------------------------
    # Audio: convert accumulated WebM chunks → WAV
    # ------------------------------------------------------------------

    def _save_webm_as_wav(self, chunks: list, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not chunks:
            logger.warning(
                "No audio chunks received from WebRTC capture — "
                "the meeting may have ended before any audio tracks were created, "
                "or the browser muted audio before the recorder could start."
            )
            output_path.write_bytes(b"")
            return

        webm_path = output_path.with_suffix(".webm")
        webm_path.write_bytes(b"".join(chunks))
        total_kb = webm_path.stat().st_size // 1024
        logger.info("WebM audio accumulated: %d KB — converting to WAV", total_kb)

        result = subprocess.run(
            [self._ffmpeg, "-y", "-i", str(webm_path),
             "-ar", "16000", "-ac", "1", str(output_path)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            logger.info("WAV conversion OK: %s", output_path.name)
            webm_path.unlink(missing_ok=True)
        else:
            logger.error("WAV conversion failed:\n%s", result.stderr[-400:])
            webm_path.rename(output_path)   # keep audio even if conversion fails

    # ------------------------------------------------------------------
    # Browser session
    # ------------------------------------------------------------------

    _BOT_PROFILE_DIR = Path(os.getenv("BOT_PROFILE_DIR", "/tmp/bot_profile"))

    def _run_browser_session(self, event: MeetingEvent, duration_secs: int,
                              output_path: Path) -> None:
        _LAUNCH_ARGS = [
            "--use-fake-ui-for-media-stream",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--ignore-certificate-errors",
            "--allow-running-insecure-content",
            # Echo is prevented by the JS gain=0 node in _WEBRTC_CAPTURE_SCRIPT,
            # NOT by --mute-audio. That flag disables the Web Audio render pipeline
            # entirely and causes the AudioContext to produce silence.
        ]

        profile_dir = str(self._BOT_PROFILE_DIR)
        self._BOT_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Using bot Chrome profile: %s", profile_dir)

        audio_chunks: list = []

        def _on_audio_chunk(b64_chunk: str) -> None:
            try:
                audio_chunks.append(base64.b64decode(b64_chunk))
            except Exception as exc:
                logger.warning("Audio chunk decode error: %s", exc)

        with sync_playwright() as pw:
            context = None
            for channel in ("chrome", "msedge", None):
                try:
                    kwargs = dict(
                        user_data_dir=profile_dir,
                        headless=os.getenv("BOT_HEADLESS", "true").lower() == "true",
                        args=_LAUNCH_ARGS,
                        permissions=["microphone", "camera"],
                    )
                    if channel:
                        context = pw.chromium.launch_persistent_context(channel=channel, **kwargs)
                    else:
                        context = pw.chromium.launch_persistent_context(**kwargs)
                    logger.info("Persistent context launched via %s", channel or "bundled-chromium")
                    break
                except Exception as exc:
                    logger.warning("Could not launch %s: %s", channel or "bundled-chromium", exc)

            if context is None:
                raise RuntimeError("No browser could be launched")

            # Register Python callback so JS can send audio data back
            context.expose_function("pyReceiveAudioChunk", _on_audio_chunk)

            # Inject automation mask + WebRTC audio interceptor into every page
            context.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3]});"
                "Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});"
                "window.chrome={runtime:{}};"
                + _WEBRTC_CAPTURE_SCRIPT
            )

            page = context.new_page()
            page_closed = [False]
            page.on("close", lambda: page_closed.__setitem__(0, True))

            try:
                if event.platform == "meet":
                    self._join_google_meet(page, event.join_url, page_closed, organizer=False)
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
                    context.close()
                except Exception:
                    pass

        logger.info("Browser closed — captured %d audio chunks (%.1f KB)",
                    len(audio_chunks),
                    sum(len(c) for c in audio_chunks) / 1024)
        self._save_webm_as_wav(audio_chunks, output_path)

    # ------------------------------------------------------------------
    # Google account sign-in (kept for reference; not called in guest mode)
    # ------------------------------------------------------------------

    def _sign_in_google(self, page: Page) -> bool:
        email    = GOOGLE_ACCOUNT_EMAIL.strip()
        password = GOOGLE_ACCOUNT_PASSWORD.strip()
        if not email or not password:
            return False

        try:
            page.goto("https://myaccount.google.com/", timeout=15_000)
            page.wait_for_load_state("domcontentloaded", timeout=10_000)
            time.sleep(1)
            if "myaccount.google.com" in page.url and "signin" not in page.url:
                logger.info("Already signed in to Google — skipping login flow")
                return True
        except Exception:
            pass

        logger.info("Not signed in — attempting Google sign-in for: %s", email)
        try:
            page.goto("https://accounts.google.com/signin/v2/identifier", timeout=PAGE_TIMEOUT_MS)
            page.wait_for_load_state("domcontentloaded", timeout=15_000)
            time.sleep(2)

            email_sel = None
            for sel in ["input[type='email']", "#identifierId", "input[name='identifier']"]:
                try:
                    page.wait_for_selector(sel, state="visible", timeout=6_000)
                    email_sel = sel
                    break
                except PWTimeout:
                    continue

            if not email_sel:
                logger.error("Could not find email input on Google sign-in page. URL: %s", page.url)
                return False

            page.click(email_sel)
            page.fill(email_sel, "")
            page.type(email_sel, email, delay=60)
            time.sleep(0.5)

            next_clicked = False
            for sel in ["#identifierNext", "[jsname='LgbsSe']",
                        "button:has-text('Next')", "input[value='Next']"]:
                try:
                    page.click(sel, timeout=4_000)
                    next_clicked = True
                    break
                except PWTimeout:
                    continue
            if not next_clicked:
                page.keyboard.press("Enter")

            time.sleep(2)
            page.wait_for_load_state("domcontentloaded", timeout=10_000)

            pwd_sel = None
            for sel in ["input[type='password']", "input[name='Passwd']",
                        "input[name='password']", "#password input"]:
                try:
                    page.wait_for_selector(sel, state="visible", timeout=8_000)
                    pwd_sel = sel
                    break
                except PWTimeout:
                    continue

            if not pwd_sel:
                logger.error("Could not find password field. URL: %s", page.url)
                return False

            page.click(pwd_sel)
            page.fill(pwd_sel, "")
            page.type(pwd_sel, password, delay=60)
            time.sleep(0.5)

            for sel in ["#passwordNext", "[jsname='LgbsSe']",
                        "button:has-text('Next')", "input[value='Next']"]:
                try:
                    page.click(sel, timeout=4_000)
                    break
                except PWTimeout:
                    continue
            else:
                page.keyboard.press("Enter")

            time.sleep(3)
            try:
                page.wait_for_url(lambda u: "accounts.google.com" not in u, timeout=15_000)
                return True
            except PWTimeout:
                current = page.url
                if "accounts.google.com" in current:
                    if any(k in current for k in ("challenge", "2-step", "totp")):
                        logger.warning("Google 2FA required — approve in the browser window")
                        try:
                            page.wait_for_url(lambda u: "accounts.google.com" not in u, timeout=30_000)
                            return True
                        except PWTimeout:
                            pass
                    return False
                return True

        except Exception as exc:
            logger.error("Google sign-in error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Platform-specific join handlers
    # ------------------------------------------------------------------

    def _join_google_meet(self, page: Page, url: str, page_closed: list,
                          organizer: bool = False) -> None:
        logger.info("Joining Google Meet (guest): %s", url)
        page.goto(url, timeout=PAGE_TIMEOUT_MS)

        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PWTimeout:
            pass

        if page_closed[0]:
            logger.warning("Meet page closed immediately after navigation")
            return

        for sel in [
            "button:has-text('Got it')", "button:has-text('Dismiss')",
            "[aria-label='Close']", "button:has-text('Use without an account')",
            "button:has-text('Learn More')",
            "[aria-label='Close dialog']",
        ]:
            try:
                page.click(sel, timeout=1500)
                logger.info("Dismissed banner via: %s", sel)
            except PWTimeout:
                pass

        time.sleep(1)

        try:
            content = page.content().lower()
            if "you can't join this video call" in content or "returning to home screen" in content:
                logger.error(
                    "Google Meet hard-blocked join — "
                    "link may be invalid/expired or guest access is disabled."
                )
                return
        except Exception:
            pass

        # Guest join — click "Continue without signing in" / "Join as a guest"
        for sel in [
            "button:has-text('Continue without signing in')",
            "button:has-text('Join as a guest')",
            "a:has-text('Join as a guest')",
            "button:has-text('Use without an account')",
        ]:
            try:
                page.click(sel, timeout=3000)
                logger.info("Clicked guest entry via: %s", sel)
                time.sleep(1.5)
                break
            except PWTimeout:
                pass

        # Fill in bot name
        name_entered = False
        for sel in [
            "input[placeholder*='name' i]",
            "input[aria-label*='name' i]",
            "input[aria-label*='Your name' i]",
            "input[type='text']",
        ]:
            try:
                page.wait_for_selector(sel, state="visible", timeout=5000)
                page.click(sel)
                page.fill(sel, "")
                page.type(sel, BOT_NAME, delay=40)
                logger.info("Bot name entered: %s", BOT_NAME)
                name_entered = True
                break
            except PWTimeout:
                pass

        if not name_entered:
            logger.warning("Could not find name field — proceeding anyway")

        time.sleep(2)

        # Mute microphone
        mic_muted = False
        for sel in [
            "[aria-label='Turn off microphone']",
            "[aria-label*='microphone' i][aria-pressed='true']",
            "[data-is-muted='false'][aria-label*='microphone' i]",
            "[jsname='BOHk6d']",
        ]:
            try:
                page.click(sel, timeout=2000)
                logger.info("Microphone muted via selector: %s", sel)
                mic_muted = True
                break
            except PWTimeout:
                pass
        if not mic_muted:
            try:
                page.keyboard.press("Control+d")
                logger.info("Microphone muted via Ctrl+D")
            except Exception:
                logger.warning("Could not mute microphone")

        # Mute camera
        cam_muted = False
        for sel in [
            "[aria-label='Turn off camera']",
            "[aria-label*='camera' i][aria-pressed='true']",
            "[data-is-muted='false'][aria-label*='camera' i]",
            "[jsname='R3R6if']",
        ]:
            try:
                page.click(sel, timeout=2000)
                logger.info("Camera muted via selector: %s", sel)
                cam_muted = True
                break
            except PWTimeout:
                pass
        if not cam_muted:
            try:
                page.keyboard.press("Control+e")
                logger.info("Camera muted via Ctrl+E")
            except Exception:
                logger.warning("Could not mute camera")

        # Click join
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
