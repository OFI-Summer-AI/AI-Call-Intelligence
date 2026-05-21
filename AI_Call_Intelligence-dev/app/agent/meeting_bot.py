"""
Playwright-based meeting bot.

Joins Zoom / Google Meet / Microsoft Teams in a headed Chrome browser,
intercepts the WebRTC audio stream via an injected MediaRecorder (no
WASAPI loopback needed), and saves a WAV recording after the meeting.

Echo prevention (TWO layers — neither breaks AudioContext/recording):
  Layer 1 — WebAudio path: incoming WebRTC tracks are routed through a
    gain=0 node connected to audioCtx.destination so no audio reaches
    the OS mixer.  The same tracks also go to mergedDest for recording.
  Layer 2 — DOM elements: <audio>/<video> elements are muted via
    page.evaluate() after joining and every 15 s during the meeting.
    This catches any audio Meet plays outside the WebAudio graph.

NOTE: --mute-audio and HTMLMediaElement prototype patching are both
intentionally NOT used — both break Chrome's AudioContext render loop
and produce 0-byte recordings.
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
    var connectedIds = {};   // track.id → true  (dedup: don't add same track twice)

    // ── AudioContext setup ──────────────────────────────────────────────
    // Created EAGERLY (not lazily) so user-gesture events during page load
    // can resume it before the first audio track arrives.
    // Chrome suspends AudioContext created without a user gesture; we poll
    // to resume it every second and also hook every user-interaction event.
    function ensureCtx() {
        if (!audioCtx) {
            try {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)(
                    { sampleRate: 16000 }
                );
                silentGain = audioCtx.createGain();
                silentGain.gain.value = 0;          // gain=0 → silent to speakers (no echo)
                silentGain.connect(audioCtx.destination);
                mergedDest = audioCtx.createMediaStreamDestination();
            } catch (e) { return false; }
        }
        if (audioCtx.state !== 'running') {
            audioCtx.resume().catch(function () {});
        }
        return audioCtx.state !== 'closed';
    }

    // Initialize immediately
    ensureCtx();

    // Poll every 1 s — keeps trying to resume after Chrome suspends
    setInterval(function () { if (audioCtx) ensureCtx(); }, 1000);

    // Resume on any user interaction (click, key, touch)
    ['click', 'mousedown', 'keydown', 'touchstart'].forEach(function (ev) {
        document.addEventListener(ev, function () {
            if (audioCtx && audioCtx.state !== 'running') {
                audioCtx.resume().catch(function () {});
            }
        }, true);
    });

    // ── Track routing ───────────────────────────────────────────────────
    function addTrack(track) {
        if (!track || track.kind !== 'audio') return;
        if (connectedIds[track.id]) return;   // already connected
        connectedIds[track.id] = true;
        if (!ensureCtx()) return;
        try {
            var s = new MediaStream([track]);
            var src = audioCtx.createMediaStreamSource(s);
            src.connect(silentGain);   // to speaker at gain=0 → silent (no echo)
            src.connect(mergedDest);   // to recorder at full volume
        } catch (e) {}
        setTimeout(startRecorder, 500);
    }

    // ── Recorder ────────────────────────────────────────────────────────
    function startRecorder() {
        if (recorder) return;
        if (!mergedDest || !ensureCtx()) { setTimeout(startRecorder, 1000); return; }
        if (audioCtx.state !== 'running')  { setTimeout(startRecorder, 1000); return; }

        var mimes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
        var mime = mimes.find(function (m) { return MediaRecorder.isTypeSupported(m); }) || '';
        try {
            recorder = new MediaRecorder(
                mergedDest.stream,
                mime ? { mimeType: mime } : {}
            );
            recorder.ondataavailable = function (e) {
                if (!e.data || e.data.size === 0) return;
                e.data.arrayBuffer().then(function (buf) {
                    var u8 = new Uint8Array(buf);
                    var s = '', chunk = 8192;
                    for (var i = 0; i < u8.length; i += chunk)
                        s += String.fromCharCode.apply(
                            null, u8.subarray(i, Math.min(i + chunk, u8.length))
                        );
                    try { window.pyReceiveAudioChunk(btoa(s)); } catch (_) {}
                }).catch(function () {});
            };
            recorder.start(2000);
        } catch (e) { recorder = null; }
    }

    // ── RTCPeerConnection intercept ─────────────────────────────────────
    window.RTCPeerConnection = function () {
        var pc = new (Function.prototype.bind.apply(
            OrigPC, [null].concat(Array.prototype.slice.call(arguments))
        ))();
        pc.addEventListener('track', function (e) {
            if (e.track.kind === 'audio') addTrack(e.track);
        });
        return pc;
    };
    window.RTCPeerConnection.prototype = OrigPC.prototype;
    Object.defineProperty(window.RTCPeerConnection, 'name', { value: 'RTCPeerConnection' });

    // ── Fallback: scan <audio>/<video> srcObject streams every 3 s ──────
    // Google Meet attaches MediaStreams directly to <audio> elements.
    // Even though those elements are muted (no echo), we can pull the
    // audio tracks from their .srcObject for recording.
    setInterval(function () {
        if (!ensureCtx()) return;
        document.querySelectorAll('audio, video').forEach(function (el) {
            if (!el.srcObject) return;
            try {
                el.srcObject.getAudioTracks().forEach(function (t) {
                    if (t.readyState === 'live') addTrack(t);
                });
            } catch (e) {}
        });
    }, 3000);
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

    _BOT_PROFILE_DIR = Path(
        os.getenv("BOT_PROFILE_DIR",
                  str(Path(__file__).resolve().parent.parent.parent / "data" / "bot_profile"))
    )

    def _run_browser_session(self, event: MeetingEvent, duration_secs: int,
                              output_path: Path) -> None:
        _LAUNCH_ARGS = [
            # ── Echo prevention (TWO layers) ─────────────────────────────────
            # Layer 1 — INPUT: replace the real system mic with Chrome's silent
            #   fake device so the bot never captures or re-transmits any audio
            #   from the host machine's microphone.
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            # NOTE: --mute-audio is intentionally NOT used here.
            # That flag suspends Chrome's AudioContext entirely, which breaks
            # _WEBRTC_CAPTURE_SCRIPT (it can no longer create AudioContext nodes
            # or process incoming tracks → zero-byte recording).
            # Speaker output is silenced instead via the JS patch below
            # (_MUTE_SPEAKER_SCRIPT) which mutes all <audio>/<video> elements.
            # ── Automation / sandbox ─────────────────────────────────────────
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--ignore-certificate-errors",
            "--allow-running-insecure-content",
        ]

        # Use a UNIQUE temp profile dir for each session.
        # Reusing a single profile dir across sessions causes Chrome to hold a
        # lock on it; when the previous session's Chrome process hasn't fully
        # exited, the next launch_persistent_context() fails immediately with
        # "user data directory is already in use" → 0-byte recording.
        # A fresh temp dir per session is always available, has no lock, and
        # still lets Playwright boot quickly via bundled Chromium.
        import tempfile
        _tmp_profile = tempfile.mkdtemp(prefix="bot_session_")
        profile_dir  = _tmp_profile
        logger.info("Using fresh Chrome profile: %s", profile_dir)

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

            # Inject automation mask + mic-silence + WebRTC recorder into every page.
            #
            # NOTE: we intentionally do NOT patch HTMLMediaElement.prototype or
            # AudioContext here.  Those "speaker mute" patches prevent Meet from
            # establishing WebRTC audio tracks (it checks volume/muted state to
            # verify the audio subsystem is healthy), which results in the
            # track-event never firing → zero audio chunks → 0-byte recording.
            # Echo is prevented at the INPUT level only:
            #   --use-fake-device-for-media-stream  → fake (silent) system mic
            #   _SILENCE_MIC_SCRIPT getUserMedia override → silent AudioContext stream
            _SILENCE_MIC_SCRIPT = r"""
(function () {
    var _origGUM = navigator.mediaDevices && navigator.mediaDevices.getUserMedia
                   ? navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices)
                   : null;
    if (!_origGUM) return;

    // Build a 1x1 black canvas stream once — reused for every video request.
    // This replaces the green animated test pattern that --use-fake-device-for-media-stream
    // sends into the meeting as the bot's camera feed.
    function _blackVideoTrack() {
        try {
            var canvas = document.createElement('canvas');
            canvas.width = 2; canvas.height = 2;
            var ctx2d = canvas.getContext('2d');
            ctx2d.fillStyle = 'black';
            ctx2d.fillRect(0, 0, 2, 2);
            var stream = canvas.captureStream(0);   // 0 fps = static black frame
            var vt = stream.getVideoTracks()[0];
            if (vt) return vt;
        } catch (e) {}
        return null;
    }

    navigator.mediaDevices.getUserMedia = async function (constraints) {
        var wantAudio = constraints && constraints.audio;
        var wantVideo = constraints && constraints.video;
        var tracks = [];

        // Audio → completely silent (gain = 0)
        if (wantAudio) {
            try {
                var actx = new (window.AudioContext || window.webkitAudioContext)();
                var dst  = actx.createMediaStreamDestination();
                var gain = actx.createGain();
                gain.gain.value = 0;
                gain.connect(dst);
                tracks = tracks.concat(dst.stream.getAudioTracks());
            } catch (e) {
                try {
                    var fb = await _origGUM({audio: true});
                    tracks = tracks.concat(fb.getAudioTracks());
                } catch (_) {}
            }
        }

        // Video → static black frame (no green fake-device animation)
        if (wantVideo) {
            var bt = _blackVideoTrack();
            if (bt) {
                tracks.push(bt);
            } else {
                try {
                    var vs = await _origGUM({video: wantVideo});
                    tracks = tracks.concat(vs.getVideoTracks());
                } catch (_) {}
            }
        }

        return new MediaStream(tracks);
    };

    // Also patch enumerateDevices so Meet does not show the fake green camera
    // as an available device in its device-picker UI.
    var _origEnum = navigator.mediaDevices.enumerateDevices
                    ? navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices)
                    : null;
    if (_origEnum) {
        navigator.mediaDevices.enumerateDevices = async function () {
            var devices = await _origEnum();
            // Keep audio devices; hide all videoinput entries so Meet thinks
            // there is no camera and leaves the video track off by default.
            return devices.filter(function(d) { return d.kind !== 'videoinput'; });
        };
    }
})();
"""
            # ── Speaker-mute script ──────────────────────────────────────────────────
            # Mutes every <audio>/<video> element the instant it appears so the bot
            # browser NEVER plays sound through physical speakers (= no echo).
            #
            # Three mechanisms work together:
            #  1. MutationObserver — fires synchronously when any element is added;
            #     mutes it before the first audio frame can play.
            #  2. srcObject setter intercept — mutes the element before the stream
            #     is even attached, catching the case where play() fires in the
            #     same microtask as the DOM insert.
            #  3. setInterval every 2 s — belt-and-suspenders sweep for anything
            #     that slipped through (e.g. dynamically re-created elements).
            #
            # SAFE for recording: this only sets .muted on individual elements.
            # It does NOT patch .volume on the prototype (that broke WebRTC before),
            # does NOT use --mute-audio (that breaks AudioContext), and does NOT
            # interfere with RTCPeerConnection or MediaRecorder in any way.
            _AUTO_MUTE_SPEAKER_SCRIPT = r"""
(function () {
    'use strict';

    function muteEl(el) {
        if (!el) return;
        el.muted  = true;
        el.volume = 0;
    }

    function muteAll() {
        document.querySelectorAll('audio,video').forEach(muteEl);
    }

    // ── 1. MutationObserver: mute instantly on DOM insert ────────────────
    var obs = new MutationObserver(function (mutations) {
        for (var i = 0; i < mutations.length; i++) {
            var added = mutations[i].addedNodes;
            for (var j = 0; j < added.length; j++) {
                var n = added[j];
                if (!n || n.nodeType !== 1) continue;
                if (n.tagName === 'AUDIO' || n.tagName === 'VIDEO') {
                    muteEl(n);
                }
                if (n.querySelectorAll) {
                    n.querySelectorAll('audio,video').forEach(muteEl);
                }
            }
        }
    });

    function startObs() {
        var root = document.body || document.documentElement;
        if (root) {
            obs.observe(root, { childList: true, subtree: true });
            muteAll();
        } else {
            document.addEventListener('DOMContentLoaded', function () {
                obs.observe(document.body || document.documentElement,
                            { childList: true, subtree: true });
                muteAll();
            }, { once: true });
        }
    }
    startObs();

    // ── 2. srcObject setter intercept: mute before stream is attached ────
    try {
        var desc = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'srcObject');
        if (desc && desc.set) {
            var _origSet = desc.set;
            Object.defineProperty(HTMLMediaElement.prototype, 'srcObject', {
                get: desc.get,
                set: function (v) {
                    this.muted  = true;
                    this.volume = 0;
                    return _origSet.call(this, v);
                },
                configurable: true,
                enumerable:   true,
            });
        }
    } catch (_) {}

    // ── 3. setInterval sweep every 2 s ───────────────────────────────────
    setInterval(muteAll, 2000);
})();
"""
            context.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3]});"
                "Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});"
                "window.chrome={runtime:{}};"
                + _SILENCE_MIC_SCRIPT           # silent fake mic → bot transmits nothing
                + _AUTO_MUTE_SPEAKER_SCRIPT     # mute every <audio>/<video> instantly → no echo
                + _WEBRTC_CAPTURE_SCRIPT        # capture incoming peer tracks for recording
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
                    self._wait_for_meeting_end(page, event.platform, duration_secs, page_closed, audio_chunks)

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

        # Clean up the temporary Chrome profile to free disk space
        try:
            shutil.rmtree(_tmp_profile, ignore_errors=True)
            logger.debug("Temp profile cleaned up: %s", _tmp_profile)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Google account sign-in (kept for reference; not called in guest mode)
    # ------------------------------------------------------------------

    def _sign_in_google(self, page: Page) -> bool:
        """
        Attempt to sign in to Google. Returns True on success, False on any failure.
        Runs directly on the calling thread — Playwright sync API must NOT be called
        from a background thread (causes greenlet.error that corrupts the context).
        Playwright's own selector timeouts cap each step internally.
        """
        email    = GOOGLE_ACCOUNT_EMAIL.strip()
        password = GOOGLE_ACCOUNT_PASSWORD.strip()
        if not email or not password:
            return False
        try:
            return self._sign_in_google_inner(page, email, password)
        except Exception as exc:
            logger.error("Google sign-in error: %s", exc)
            return False

    def _sign_in_google_inner(self, page: Page, email: str, password: str) -> bool:
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

    def _screenshot(self, page: Page, label: str) -> None:
        """Save a debug screenshot — helps diagnose what the bot actually sees."""
        try:
            from app.config import UPLOAD_DIR
            path = UPLOAD_DIR / f"debug_{label}.png"
            page.screenshot(path=str(path), full_page=False)
            logger.info("Screenshot saved → %s", path.name)
        except Exception as exc:
            logger.debug("Screenshot failed (%s): %s", label, exc)

    def _click_first(self, page: Page, selectors: list, timeout: int = 3000,
                     label: str = "") -> str | None:
        """
        Try each selector in order; return the one that worked, or None.
        Uses query_selector so it only waits per-selector, not globally.
        """
        for sel in selectors:
            try:
                el = page.wait_for_selector(sel, state="visible", timeout=timeout)
                if el:
                    el.click()
                    if label:
                        logger.info("%s via: %s", label, sel)
                    return sel
            except PWTimeout:
                pass
            except Exception as exc:
                logger.debug("Selector '%s' error: %s", sel, exc)
        return None

    def _join_google_meet(self, page: Page, url: str, page_closed: list,
                          organizer: bool = False) -> None:
        # ── Step 1: Optional Google sign-in ──────────────────────────────
        # IMPORTANT: sign-in is attempted on a SEPARATE page so that any
        # navigation failure or Playwright error cannot corrupt the `page`
        # object used for the actual meeting.  Browser cookies/session are
        # stored at the context level, so a successful sign-in on a helper
        # page is immediately visible when `page` later loads meet.google.com.
        signed_in = False
        _has_creds = (
            GOOGLE_ACCOUNT_EMAIL
            and GOOGLE_ACCOUNT_PASSWORD
            and GOOGLE_ACCOUNT_EMAIL not in ("your-email@gmail.com", "")
            and GOOGLE_ACCOUNT_PASSWORD not in ("your-password", "")
        )
        if _has_creds:
            logger.info("Signing into Google on a helper page...")
            signin_page = None
            try:
                signin_page = page.context.new_page()
                signed_in = self._sign_in_google(signin_page)
            except Exception as exc:
                logger.warning("Sign-in helper page error: %s", exc)
                signed_in = False
            finally:
                if signin_page:
                    try:
                        signin_page.close()
                    except Exception:
                        pass
            if signed_in:
                logger.info("Signed in as %s", GOOGLE_ACCOUNT_EMAIL)
            else:
                logger.warning("Sign-in failed — falling back to guest mode")
                try:
                    page.context.clear_cookies()
                except Exception:
                    pass
        else:
            logger.info("No credentials set — joining as guest")

        # ── Step 2: Navigate to the Meet URL ─────────────────────────────
        logger.info("Navigating to Google Meet: %s", url)
        try:
            page.goto(url, timeout=PAGE_TIMEOUT_MS)
        except PWTimeout:
            logger.warning("Page load timed out — continuing anyway")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20_000)
        except PWTimeout:
            pass
        time.sleep(3)

        if page_closed[0]:
            logger.warning("Meet page closed immediately after navigation")
            return

        self._screenshot(page, "01_meet_loaded")
        logger.info("Page URL after navigation: %s", page.url)

        # ── Step 3: Dismiss any first-run popups / banners ────────────────
        for sel in [
            "button:has-text('Got it')", "button:has-text('Dismiss')",
            "button:has-text('Learn More')", "[aria-label='Close dialog']",
        ]:
            try:
                page.click(sel, timeout=1000)
                logger.info("Dismissed banner: %s", sel)
            except PWTimeout:
                pass

        # ── Step 4: Hard-block check ──────────────────────────────────────
        try:
            content = page.content().lower()
            if "you can't join this video call" in content or \
               "returning to home screen" in content:
                logger.error("Meet blocked join — link invalid/expired or guest access disabled")
                self._screenshot(page, "02_blocked")
                return
        except Exception:
            pass

        # ── Step 5: Guest / unauthenticated path ──────────────────────────
        # When not signed in, Meet shows an interstitial:
        #   "To join, sign in or continue as a guest"
        # The button text has varied over Meet versions — try ALL known variants.
        if not signed_in:
            # BUG FIX: prior code had 'Continue as guest' (missing " a ").
            # Current Meet (2024-2025) says "Continue as a guest" (with "a").
            guest_selectors = [
                # ── Current Meet UI (2024-2025) ──
                "button:has-text('Continue as a guest')",
                "a:has-text('Continue as a guest')",
                # ── Older/regional variants ──
                "button:has-text('Continue as guest')",
                "a:has-text('Continue as guest')",
                "button:has-text('Continue without signing in')",
                "button:has-text('Join as a guest')",
                "a:has-text('Join as a guest')",
                "button:has-text('Use without an account')",
                # ── Loose catch-all (matches any button with 'guest') ──
                "button:has-text('guest')",
                "a:has-text('guest')",
                # ── Data-attribute fallback ──
                "[data-idom-class*='guest']",
            ]
            guest_hit = self._click_first(page, guest_selectors,
                                          timeout=2000, label="Clicked guest entry")
            if guest_hit:
                # Wait for the lobby / name-input screen to load
                time.sleep(3)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=10_000)
                except PWTimeout:
                    pass
            else:
                logger.warning(
                    "No 'Continue as a guest' button found — Meet may already "
                    "show the lobby (URL: %s)", page.url
                )
                self._screenshot(page, "03_no_guest_btn")

            # ── Enter display name ────────────────────────────────────────
            # Strategy: click → fill → verify via input_value().
            # Fallback 1: keyboard.type() (triggers real key events for React).
            # Fallback 2: JS injection using React's native setter so synthetic
            #             events fire and Meet's state machine picks up the name.
            # Fallback 3: check each iframe (Meet can embed the lobby in a frame).
            time.sleep(2)   # let the lobby DOM fully settle
            self._screenshot(page, "03b_before_name_entry")

            name_selectors = [
                "input[placeholder='Your name']",       # most reliable — visible placeholder
                "input[aria-label='Your name']",
                "input[aria-label*='name' i]",
                "input[placeholder*='name' i]",
                "input[jsname='YPqjbf']",               # Meet internal jsname
                "input[type='text']",                   # last-resort
            ]

            def _try_fill_name(ctx, sel: str) -> bool:
                """
                Try to fill `sel` inside Playwright Frame/Page `ctx`.
                Returns True if the value was verified in the element.
                Note: keyboard operations always go through `page` (the outer
                Page object) because Frame objects do not have a .keyboard attr.
                """
                try:
                    ctx.wait_for_selector(sel, state="visible", timeout=3000)
                    # 1) Click to focus
                    ctx.click(sel)
                    time.sleep(0.3)
                    # 2) Select-all + delete, then fill
                    ctx.fill(sel, "")
                    ctx.fill(sel, BOT_NAME)
                    time.sleep(0.3)
                    # 3) Verify
                    val = ctx.input_value(sel)
                    if BOT_NAME.lower() in val.lower():
                        ctx.press(sel, "Tab")
                        logger.info("Name filled (fill verified) '%s' via: %s", val, sel)
                        return True
                    # 4) fill() didn't take — try keyboard.type() via page (Page only)
                    logger.warning("fill() unverified for '%s' (got '%s') — trying keyboard.type()",
                                   sel, val)
                    ctx.click(sel)
                    page.keyboard.press("Control+a")   # page.keyboard always available
                    page.keyboard.press("Delete")
                    page.keyboard.type(BOT_NAME, delay=50)
                    time.sleep(0.3)
                    val2 = ctx.input_value(sel)
                    if BOT_NAME.lower() in val2.lower():
                        ctx.press(sel, "Tab")
                        logger.info("Name filled (keyboard.type verified) '%s' via: %s", val2, sel)
                        return True
                    logger.warning("keyboard.type() also unverified for '%s' (got '%s')", sel, val2)
                except PWTimeout:
                    logger.info("Name selector not visible (timeout): %s", sel)
                except Exception as exc:
                    logger.info("Name selector '%s' error: %s", sel, exc)
                return False

            name_entered = False

            # Pass 1: main page
            for sel in name_selectors:
                if _try_fill_name(page, sel):
                    name_entered = True
                    break

            # Pass 2: iframes (Meet sometimes embeds the lobby in a sub-frame)
            if not name_entered:
                frames = [f for f in page.frames if f is not page.main_frame]
                logger.info("Trying name input inside %d sub-frame(s)...", len(frames))
                for iframe in frames:
                    for sel in name_selectors:
                        if _try_fill_name(iframe, sel):
                            name_entered = True
                            break
                    if name_entered:
                        break

            # Pass 3: JavaScript injection — React-compatible native setter
            if not name_entered:
                logger.info("Trying JS injection for name input (React-compatible)...")
                try:
                    js_result = page.evaluate(
                        """(name) => {
                            const sels = [
                                "input[placeholder='Your name']",
                                "input[aria-label='Your name']",
                                "input[jsname='YPqjbf']",
                                "input[aria-label*='name' i]",
                                "input[type='text']"
                            ];
                            for (const sel of sels) {
                                const el = document.querySelector(sel);
                                if (el) {
                                    el.focus();
                                    const setter = Object.getOwnPropertyDescriptor(
                                        window.HTMLInputElement.prototype, 'value').set;
                                    setter.call(el, name);
                                    el.dispatchEvent(new Event('input',  {bubbles:true}));
                                    el.dispatchEvent(new Event('change', {bubbles:true}));
                                    el.dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
                                    return 'filled:' + sel + ':' + el.value;
                                }
                            }
                            return 'not_found';
                        }""",
                        BOT_NAME,
                    )
                    logger.info("JS name injection result: %s", js_result)
                    if js_result and js_result.startswith("filled:"):
                        name_entered = True
                except Exception as exc:
                    logger.warning("JS name injection failed: %s", exc)

            if not name_entered:
                logger.warning("All name-entry methods failed — bot joining without setting name")
                self._screenshot(page, "04_no_name_input")

        # ── Step 6: Mute mic & camera before joining ──────────────────────
        self._screenshot(page, "05_pre_join")
        time.sleep(2)

        # Microphone — try button selectors, then keyboard shortcut.
        # Only click if the mic is CURRENTLY ON (aria-label says "Turn off …").
        # If it's already off the selectors below won't match, which is fine.
        muted_mic = self._click_first(page, [
            "[aria-label='Turn off microphone (ctrl + d)']",
            "[aria-label='Turn off microphone']",
            "[aria-label='Mute microphone']",
            "[data-is-muted='false'][aria-label*='microphone' i]",
            "[jsname='BOHk6d']",
            "button[aria-label*='Turn off mic' i]",
            "button[aria-label*='microphone' i][aria-pressed='false']",
        ], timeout=3000, label="Mic muted")
        if not muted_mic:
            try:
                page.keyboard.press("Control+d")
                logger.info("Mic mute attempted via Ctrl+D")
            except Exception:
                pass

        # Camera — try button selectors, then keyboard shortcut.
        # Only click if camera is CURRENTLY ON (aria-label says "Turn off …").
        muted_cam = self._click_first(page, [
            "[aria-label='Turn off camera (ctrl + e)']",
            "[aria-label='Turn off camera']",
            "[aria-label='Disable camera']",
            "[data-is-muted='false'][aria-label*='camera' i]",
            "[jsname='R3R6if']",
            "button[aria-label*='Turn off cam' i]",
            "button[aria-label*='camera' i][aria-pressed='false']",
        ], timeout=3000, label="Camera muted")
        if not muted_cam:
            try:
                page.keyboard.press("Control+e")
                logger.info("Camera mute attempted via Ctrl+E")
            except Exception:
                pass

        time.sleep(1)

        # ── Step 7: Click the join / ask-to-join button ───────────────────
        join_selectors = [
            "button:has-text('Ask to join')",    # guest in a room owned by someone else
            "button:has-text('Join now')",        # organiser or open meeting
            "button:has-text('Join')",
            "[jsname='Qx7uuf']",                 # common Meet jsname
            "[jsname='V67aGc']",
            "[data-idom-class*='join']",
            "button[aria-label*='join' i]",
        ]
        joined = self._click_first(page, join_selectors,
                                   timeout=JOIN_TIMEOUT_MS, label="Join button clicked")

        if not joined:
            self._screenshot(page, "06_no_join_btn")
            logger.error(
                "Could not click any join button. "
                "Check debug screenshots in the uploads folder. "
                "URL: %s", page.url
            )
        else:
            time.sleep(3)
            # Mute all DOM <audio>/<video> elements right after joining.
            # Safe — does NOT touch prototype chain, so Meet's WebRTC health
            # checks and track detection continue to work normally.
            try:
                page.evaluate(
                    "document.querySelectorAll('audio,video')"
                    ".forEach(function(el){el.muted=true;})"
                )
                logger.info("DOM audio/video elements muted after join")
            except Exception:
                pass
            # Force-resume AudioContext — Chrome suspends it without a user gesture.
            # Calling resume() via page.evaluate() after a real click (join button)
            # counts as an in-gesture call on some Chrome versions.
            try:
                ctx_state = page.evaluate(
                    "window._pyAudioCtx ? window._pyAudioCtx.state : "
                    "(typeof audioCtx !== 'undefined' ? audioCtx.state : 'unknown')"
                )
                logger.info("AudioContext state after join: %s", ctx_state)
            except Exception:
                pass
            self._screenshot(page, "07_joined")
            logger.info("Join clicked — now in meeting (or waiting room)")

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
    # Meeting end detection + graceful leave
    # ------------------------------------------------------------------

    def _get_meet_participant_count(self, page: Page) -> int:
        """
        Read the current participant count from Google Meet's UI.
        Returns -1 if the count cannot be determined.
        """
        # 1) Participant tiles in the main video grid
        try:
            tiles = page.query_selector_all("[data-participant-id]")
            if tiles:
                return len(tiles)
        except Exception:
            pass

        # 2) "People" panel button badge (e.g. "People (3)")
        for sel in [
            "[aria-label*='people' i]",
            "[aria-label*='participant' i]",
            "button[jsname='A5il2e']",       # Meet's people-panel button jsname
        ]:
            try:
                el = page.query_selector(sel)
                if el:
                    text = el.get_attribute("aria-label") or el.inner_text()
                    nums = re.findall(r"\d+", text)
                    if nums:
                        return int(nums[0])
            except Exception:
                pass

        # 3) Generic count badge near the grid
        try:
            el = page.query_selector("[data-count]")
            if el:
                val = el.get_attribute("data-count")
                if val and val.isdigit():
                    return int(val)
        except Exception:
            pass

        return -1   # unknown

    def _leave_meeting(self, page: Page, platform: str) -> None:
        """
        Click the platform leave/end-call button and confirm any dialog that
        appears afterwards (e.g. "Just leave" vs "End meeting for all").
        """
        if platform == "meet":
            leave_sels = [
                "[aria-label='Leave call']",
                "button:has-text('Leave call')",
                "[jsname='CQylAd']",                    # Meet toolbar leave button
                "[data-idom-class*='leave-call' i]",
                "button[aria-label*='leave' i]",
            ]
        elif platform == "zoom":
            leave_sels = [
                "button:has-text('Leave')",
                "button:has-text('Leave Meeting')",
                "[aria-label*='leave' i]",
            ]
        elif platform == "teams":
            leave_sels = [
                "button[aria-label*='leave' i]",
                "button:has-text('Leave')",
            ]
        else:
            leave_sels = [
                "button:has-text('Leave')",
                "button[aria-label*='leave' i]",
            ]

        clicked = self._click_first(page, leave_sels, timeout=5000,
                                    label="Leave-call button clicked")
        if not clicked:
            logger.warning("Leave button not found — browser will close without clicking Leave")
            return

        time.sleep(1)
        self._screenshot(page, "08_after_leave_click")

        # Confirm any secondary dialog ("Just leave" / "Leave meeting")
        confirm_sels = [
            "button:has-text('Just leave')",
            "button:has-text('Leave meeting')",
            "button:has-text('Leave')",
            "button:has-text('Confirm')",
        ]
        for sel in confirm_sels:
            try:
                page.click(sel, timeout=3000)
                logger.info("Leave dialog confirmed via: %s", sel)
                break
            except PWTimeout:
                pass

        time.sleep(2)
        logger.info("Left the meeting cleanly")

    def _wait_for_meeting_end(self, page: Page, platform: str,
                               max_secs: int, page_closed: list,
                               audio_chunks: list = None) -> None:
        end_signals = {
            "meet": ["you've left the call", "the call has ended", "return to home screen"],
            "zoom": ["meeting is over", "this meeting has ended", "thank you for joining"],
            "teams": ["the meeting has ended", "you left the meeting"],
        }
        signals = end_signals.get(platform, [])
        poll_interval = 15
        elapsed = 0

        # Auto-leave when bot is alone for this many seconds
        alone_grace_secs = int(os.getenv("BOT_GRACE_SECONDS", "60"))
        alone_max_polls  = max(1, alone_grace_secs // poll_interval)
        alone_streak     = 0   # consecutive polls where bot appears alone

        while elapsed < max_secs:
            time.sleep(poll_interval)
            elapsed += poll_interval

            if page_closed[0]:
                logger.info("Page closed — meeting ended")
                return

            # ── Re-mute DOM audio/video elements every poll cycle ──────────
            try:
                page.evaluate(
                    "document.querySelectorAll('audio,video')"
                    ".forEach(function(el){el.muted=true;})"
                )
            except Exception:
                pass

            # ── Force-resume AudioContext + log capture status ─────────────
            try:
                status = page.evaluate("""
                    (function(){
                        var info = {ctx:'none', tracks:0, recording:false};
                        if (typeof audioCtx !== 'undefined' && audioCtx) {
                            info.ctx = audioCtx.state;
                            if (audioCtx.state !== 'running') audioCtx.resume();
                        }
                        if (typeof connectedIds !== 'undefined')
                            info.tracks = Object.keys(connectedIds).length;
                        if (typeof recorder !== 'undefined' && recorder)
                            info.recording = recorder.state === 'recording';
                        return JSON.stringify(info);
                    })()
                """)
                logger.info("AudioCapture status: %s  chunks_so_far=%d",
                            status, len(audio_chunks) if audio_chunks else 0)
            except Exception:
                pass

            # ── Check for page-level meeting-end signals ───────────────────
            try:
                content = page.content().lower()
                for signal in signals:
                    if signal in content:
                        logger.info("Meeting end detected: '%s'", signal)
                        return
            except Exception as exc:
                # Do NOT exit here — a transient page error is not a meeting end.
                # Log and keep polling so we don't produce a 0-byte recording.
                logger.debug("page.content() error (will retry): %s", exc)

            # ── Check participant count (Google Meet) ──────────────────────
            if platform == "meet":
                try:
                    count = self._get_meet_participant_count(page)
                    if count == -1:
                        # Could not read count; don't advance alone streak
                        pass
                    elif count <= 1:   # 0 or 1 (only the bot)
                        alone_streak += 1
                        remaining_grace = (alone_max_polls - alone_streak) * poll_interval
                        logger.info(
                            "Bot appears alone (count=%d) — grace %d/%d polls (%ds left)",
                            count, alone_streak, alone_max_polls, max(0, remaining_grace),
                        )
                        if alone_streak >= alone_max_polls:
                            logger.info(
                                "Alone for %ds — leaving call automatically", alone_grace_secs
                            )
                            self._leave_meeting(page, platform)
                            return
                    else:
                        if alone_streak > 0:
                            logger.info(
                                "Participants rejoined (count=%d) — resetting alone-streak", count
                            )
                        alone_streak = 0
                except Exception as exc:
                    logger.debug("Participant count check failed: %s", exc)

            remaining = max_secs - elapsed
            if elapsed % 300 < poll_interval:
                logger.info("Still in meeting — %ds remaining", remaining)

        logger.info("Max recording duration reached (%ds) — leaving call", max_secs)
        self._leave_meeting(page, platform)
