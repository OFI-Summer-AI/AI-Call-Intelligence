"""
Streamlit UI for AI Call Intelligence - Live Transcription

Run with:
    streamlit run app/streamlit_app.py

Make sure the FastAPI WebSocket server is running:
    python -m app.realtime_server
"""

import streamlit as st
import requests
import json
import time

# --- Page Config ---
st.set_page_config(
    page_title="AI Call Intelligence - Live Transcription",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .transcript-container {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.5rem;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #313244;
    }
    .transcript-entry {
        padding: 0.6rem 1rem;
        margin: 0.4rem 0;
        border-radius: 8px;
        background: #313244;
        border-left: 3px solid #667eea;
    }
    .transcript-time {
        font-size: 0.75rem;
        color: #89b4fa;
        font-weight: 600;
    }
    .transcript-text {
        font-size: 0.95rem;
        color: #cdd6f4;
        margin-top: 0.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-active {
        background: #a6e3a1;
        color: #1e1e2e;
    }
    .status-idle {
        background: #f9e2af;
        color: #1e1e2e;
    }
    .mic-button {
        display: flex;
        justify-content: center;
        margin: 1rem 0;
    }
    .stats-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #313244;
        text-align: center;
    }
    .stats-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .stats-label {
        font-size: 0.85rem;
        color: #6b7280;
    }
    iframe {
        border: none;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration ---
FASTAPI_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/transcribe"

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Settings")
    st.markdown("---")
    
    server_url = st.text_input("Server URL", value=FASTAPI_URL, help="FastAPI backend URL")
    chunk_interval = st.slider("Chunk Interval (seconds)", 1, 5, 2, help="Audio chunk duration sent to server")
    
    st.markdown("---")
    st.markdown("### How It Works")
    st.markdown("""
    1. **Click Start** to begin recording
    2. Browser captures mic audio
    3. Audio chunks sent via WebSocket
    4. Whisper transcribes in real-time
    5. Live transcript appears below
    """)
    
    st.markdown("---")
    st.markdown("### Server Status")
    
    try:
        resp = requests.get(f"{server_url}/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"Connected — Model: `{data.get('model', 'unknown')}`")
        else:
            st.error("Server returned error")
    except Exception:
        st.error("Server not reachable. Start the FastAPI server first.")

# --- Main Content ---
st.markdown('<div class="main-header">AI Call Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time live transcription powered by Whisper</div>', unsafe_allow_html=True)

# --- Stats Row ---
col1, col2, col3 = st.columns(3)

# Fetch current transcripts
try:
    transcripts_resp = requests.get(f"{server_url}/api/transcripts", timeout=2)
    all_transcripts = transcripts_resp.json() if transcripts_resp.status_code == 200 else {}
except Exception:
    all_transcripts = {}

total_sessions = len(all_transcripts)
total_segments = sum(len(v) for v in all_transcripts.values())
total_words = sum(
    len(entry.get("text", "").split())
    for entries in all_transcripts.values()
    for entry in entries
)

with col1:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_sessions}</div>
        <div class="stats-label">Sessions</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_segments}</div>
        <div class="stats-label">Segments</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_words}</div>
        <div class="stats-label">Words</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Live Recording Section ---
tab1, tab2, tab3 = st.tabs(["Live Recording", "Screen Capture", "Session History"])

with tab1:
    st.markdown("#### Start Recording")
    st.markdown("Click the button below to start capturing audio from your microphone and transcribing in real-time.")
    
    # Embed the browser audio capture page via an iframe
    audio_capture_html = f"""
    <div id="app-container" style="background: #1e1e2e; border-radius: 12px; padding: 2rem; border: 1px solid #313244;">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
            <button id="startBtn" onclick="startRecording()" style="
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white; border: none; padding: 0.8rem 2rem;
                border-radius: 8px; font-size: 1rem; font-weight: 600;
                cursor: pointer; transition: all 0.3s;">
                Start Recording
            </button>
            <button id="stopBtn" onclick="stopRecording()" disabled style="
                background: #ef4444; color: white; border: none;
                padding: 0.8rem 2rem; border-radius: 8px;
                font-size: 1rem; font-weight: 600; cursor: pointer;
                opacity: 0.5; transition: all 0.3s;">
                Stop
            </button>
            <span id="status" style="color: #6b7280; font-size: 0.9rem;">Ready</span>
        </div>
        <div id="waveform" style="height: 4px; background: #313244; border-radius: 2px; margin-bottom: 1.5rem; overflow: hidden;">
            <div id="waveform-bar" style="height: 100%; width: 0%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s;"></div>
        </div>
        <div id="transcript-box" style="
            background: #11111b; border-radius: 8px; padding: 1rem;
            max-height: 400px; overflow-y: auto; min-height: 200px;
            border: 1px solid #313244;">
            <p style="color: #6b7280; font-style: italic;">Transcription will appear here...</p>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let ws;
        let isRecording = false;
        let micChunks = [];
        const CHUNK_INTERVAL = {chunk_interval * 1000};

        function startRecording() {{
            micChunks = [];
            navigator.mediaDevices.getUserMedia({{ audio: true }})
                .then(stream => {{
                    // Connect WebSocket
                    ws = new WebSocket("{WS_URL}");
                    
                    ws.onopen = () => {{
                        document.getElementById('status').innerHTML = 
                            '<span style="color: #a6e3a1;">Recording & Transcribing</span>';
                        document.getElementById('startBtn').disabled = true;
                        document.getElementById('startBtn').style.opacity = '0.5';
                        document.getElementById('stopBtn').disabled = false;
                        document.getElementById('stopBtn').style.opacity = '1';
                    }};

                    ws.onmessage = (event) => {{
                        const data = JSON.parse(event.data);
                        if (data.type === 'transcription') {{
                            addTranscriptEntry(data.time, data.text);
                        }}
                    }};

                    ws.onerror = (err) => {{
                        document.getElementById('status').innerHTML = 
                            '<span style="color: #ef4444;">Connection Error</span>';
                    }};

                    ws.onclose = () => {{
                        stopRecording();
                    }};

                    // Setup MediaRecorder
                    mediaRecorder = new MediaRecorder(stream, {{
                        mimeType: 'audio/webm;codecs=opus'
                    }});

                    mediaRecorder.ondataavailable = (event) => {{
                        if (event.data.size > 0) {{
                            micChunks.push(event.data);
                            if (ws && ws.readyState === WebSocket.OPEN) {{
                                ws.send(event.data);
                            }}
                            // Animate waveform
                            const bar = document.getElementById('waveform-bar');
                            bar.style.width = Math.random() * 60 + 40 + '%';
                            setTimeout(() => bar.style.width = '0%', 300);
                        }}
                    }};

                    mediaRecorder.start(CHUNK_INTERVAL);
                    isRecording = true;
                }})
                .catch(err => {{
                    document.getElementById('status').innerHTML = 
                        '<span style="color: #ef4444;">Mic access denied</span>';
                }});
        }}

        function stopRecording() {{
            isRecording = false;
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            if (ws) {{
                ws.close();
            }}
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').style.opacity = '1';
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('stopBtn').style.opacity = '0.5';
            document.getElementById('waveform-bar').style.width = '0%';

            // Auto-save mic recording to server
            if (micChunks.length > 0) {{
                const blob = new Blob(micChunks, {{ type: 'audio/webm' }});
                const filename = 'mic_recording_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.webm';
                const formData = new FormData();
                formData.append('file', blob, filename);
                document.getElementById('status').innerHTML =
                    '<span style="color: #89b4fa;">Saving recording...</span>';
                fetch('{server_url}/api/upload-recording', {{
                    method: 'POST',
                    body: formData
                }})
                .then(resp => resp.json())
                .then(data => {{
                    document.getElementById('status').innerHTML =
                        '<span style="color: #a6e3a1;">Saved: ' + data.filename + '</span>';
                }})
                .catch(err => {{
                    document.getElementById('status').innerHTML =
                        '<span style="color: #f9e2af;">Stopped (server save failed)</span>';
                }});
            }} else {{
                document.getElementById('status').innerHTML = 
                    '<span style="color: #f9e2af;">Stopped</span>';
            }}
        }}

        function addTranscriptEntry(time, text) {{
            const box = document.getElementById('transcript-box');
            // Remove placeholder
            if (box.querySelector('p[style*="italic"]')) {{
                box.innerHTML = '';
            }}
            const entry = document.createElement('div');
            entry.style.cssText = 'padding: 0.6rem 1rem; margin: 0.4rem 0; border-radius: 8px; background: #313244; border-left: 3px solid #667eea;';
            entry.innerHTML = `
                <div style="font-size: 0.75rem; color: #89b4fa; font-weight: 600;">${{time}}</div>
                <div style="font-size: 0.95rem; color: #cdd6f4; margin-top: 0.2rem;">${{text}}</div>
            `;
            box.appendChild(entry);
            box.scrollTop = box.scrollHeight;
        }}
    </script>
    """
    
    st.components.v1.html(audio_capture_html, height=550)

with tab2:
    st.markdown("#### Screen / Meeting Capture")
    st.markdown("Capture system audio from any meeting app (Teams, Zoom, Google Meet) and transcribe in real-time. You can also download the full recording.")
    
    screen_capture_html = f"""
    <div style="background: #1e1e2e; border-radius: 12px; padding: 2rem; border: 1px solid #313244;">
        <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; flex-wrap: wrap;">
            <button id="scStartBtn" onclick="startScreenCapture()" style="
                background: linear-gradient(135deg, #f97316, #ef4444);
                color: white; border: none; padding: 0.8rem 1.6rem;
                border-radius: 8px; font-size: 0.95rem; font-weight: 600;
                cursor: pointer; transition: all 0.3s;">
                Capture Screen Audio
            </button>
            <button id="scStopBtn" onclick="stopScreenCapture()" disabled style="
                background: #ef4444; color: white; border: none;
                padding: 0.8rem 1.6rem; border-radius: 8px;
                font-size: 0.95rem; font-weight: 600; cursor: pointer;
                opacity: 0.5; transition: all 0.3s;">
                Stop
            </button>
            <button id="scDownloadBtn" onclick="downloadRecording()" disabled style="
                background: #22c55e; color: white; border: none;
                padding: 0.8rem 1.6rem; border-radius: 8px;
                font-size: 0.95rem; font-weight: 600; cursor: pointer;
                opacity: 0.5; transition: all 0.3s;">
                Download Recording
            </button>
            <span id="scStatus" style="color: #6b7280; font-size: 0.9rem;">Ready</span>
        </div>
        <div style="display: flex; gap: 0.6rem; margin-bottom: 1rem; flex-wrap: wrap;">
            <label style="color: #a6adc8; font-size: 0.85rem; display: flex; align-items: center; gap: 0.3rem;">
                <input type="checkbox" id="scIncludeMic" style="accent-color: #667eea;"> Mix microphone audio
            </label>
            <span id="scTimer" style="color: #89b4fa; font-size: 0.85rem; font-weight: 600; margin-left: auto;">00:00:00</span>
        </div>
        <div style="height: 4px; background: #313244; border-radius: 2px; margin-bottom: 1rem; overflow: hidden;">
            <div id="sc-waveform-bar" style="height: 100%; width: 0%; background: linear-gradient(90deg, #f97316, #ef4444); transition: width 0.3s;"></div>
        </div>
        <div id="sc-transcript-box" style="
            background: #11111b; border-radius: 8px; padding: 1rem;
            max-height: 350px; overflow-y: auto; min-height: 180px;
            border: 1px solid #313244;">
            <p style="color: #6b7280; font-style: italic;">Select a screen or window to capture its audio. Make sure to check "Share audio" when prompted.</p>
        </div>
    </div>

    <script>
        let scMediaRecorder, scWs, scFullRecorder;
        let scIsRecording = false;
        let scChunks = [];
        let scTimerInterval, scSeconds = 0;
        const SC_CHUNK_INTERVAL = {chunk_interval * 1000};

        function formatTime(s) {{
            const h = String(Math.floor(s / 3600)).padStart(2, '0');
            const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
            const sec = String(s % 60).padStart(2, '0');
            return h + ':' + m + ':' + sec;
        }}

        async function startScreenCapture() {{
            try {{
                // Capture screen with system audio
                const displayStream = await navigator.mediaDevices.getDisplayMedia({{
                    video: true,
                    audio: true
                }});

                // Check if audio track is available
                const audioTracks = displayStream.getAudioTracks();
                if (audioTracks.length === 0) {{
                    document.getElementById('scStatus').innerHTML =
                        '<span style="color: #ef4444;">No audio track - check "Share audio" when sharing</span>';
                    displayStream.getTracks().forEach(t => t.stop());
                    return;
                }}

                // Build audio-only stream for transcription
                const audioCtx = new AudioContext();
                const displaySource = audioCtx.createMediaStreamSource(new MediaStream(audioTracks));
                const destination = audioCtx.createMediaStreamDestination();
                displaySource.connect(destination);

                // Optionally mix microphone
                const includeMic = document.getElementById('scIncludeMic').checked;
                let micStream = null;
                if (includeMic) {{
                    try {{
                        micStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        const micSource = audioCtx.createMediaStreamSource(micStream);
                        micSource.connect(destination);
                    }} catch(e) {{
                        console.warn('Mic not available, proceeding without');
                    }}
                }}

                // WebSocket for live transcription
                scWs = new WebSocket("{WS_URL}");
                scWs.onopen = () => {{
                    document.getElementById('scStatus').innerHTML =
                        '<span style="color: #a6e3a1;">Capturing & Transcribing</span>';
                    document.getElementById('scStartBtn').disabled = true;
                    document.getElementById('scStartBtn').style.opacity = '0.5';
                    document.getElementById('scStopBtn').disabled = false;
                    document.getElementById('scStopBtn').style.opacity = '1';
                }};
                scWs.onmessage = (event) => {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'transcription') {{
                        scAddEntry(data.time, data.text);
                    }}
                }};
                scWs.onerror = () => {{
                    document.getElementById('scStatus').innerHTML =
                        '<span style="color: #ef4444;">WebSocket error</span>';
                }};
                scWs.onclose = () => {{
                    if (scIsRecording) stopScreenCapture();
                }};

                // Transcription recorder (audio chunks to WS)
                scMediaRecorder = new MediaRecorder(destination.stream, {{
                    mimeType: 'audio/webm;codecs=opus'
                }});
                scMediaRecorder.ondataavailable = (event) => {{
                    if (event.data.size > 0 && scWs && scWs.readyState === WebSocket.OPEN) {{
                        scWs.send(event.data);
                        const bar = document.getElementById('sc-waveform-bar');
                        bar.style.width = Math.random() * 60 + 40 + '%';
                        setTimeout(() => bar.style.width = '0%', 300);
                    }}
                }};
                scMediaRecorder.start(SC_CHUNK_INTERVAL);

                // Full recording (video + audio for download)
                scChunks = [];
                scFullRecorder = new MediaRecorder(displayStream, {{
                    mimeType: 'video/webm;codecs=vp9,opus'
                }});
                scFullRecorder.ondataavailable = (event) => {{
                    if (event.data.size > 0) scChunks.push(event.data);
                }};
                scFullRecorder.start(1000);

                // Timer
                scSeconds = 0;
                document.getElementById('scTimer').textContent = '00:00:00';
                scTimerInterval = setInterval(() => {{
                    scSeconds++;
                    document.getElementById('scTimer').textContent = formatTime(scSeconds);
                }}, 1000);

                // Stop when user ends screen share
                displayStream.getVideoTracks()[0].onended = () => {{
                    stopScreenCapture();
                }};

                scIsRecording = true;

            }} catch(err) {{
                document.getElementById('scStatus').innerHTML =
                    '<span style="color: #ef4444;">Screen capture denied or not supported</span>';
                console.error('Screen capture error:', err);
            }}
        }}

        function stopScreenCapture() {{
            scIsRecording = false;
            clearInterval(scTimerInterval);
            if (scMediaRecorder && scMediaRecorder.state !== 'inactive') scMediaRecorder.stop();
            if (scFullRecorder && scFullRecorder.state !== 'inactive') scFullRecorder.stop();
            if (scWs) scWs.close();

            // Stop all tracks
            if (scMediaRecorder && scMediaRecorder.stream) {{
                scMediaRecorder.stream.getTracks().forEach(t => t.stop());
            }}
            if (scFullRecorder && scFullRecorder.stream) {{
                scFullRecorder.stream.getTracks().forEach(t => t.stop());
            }}

            document.getElementById('scStatus').innerHTML =
                '<span style="color: #f9e2af;">Stopped - ' + formatTime(scSeconds) + ' recorded</span>';
            document.getElementById('scStartBtn').disabled = false;
            document.getElementById('scStartBtn').style.opacity = '1';
            document.getElementById('scStopBtn').disabled = true;
            document.getElementById('scStopBtn').style.opacity = '0.5';
            document.getElementById('sc-waveform-bar').style.width = '0%';

            if (scChunks.length > 0) {{
                document.getElementById('scDownloadBtn').disabled = false;
                document.getElementById('scDownloadBtn').style.opacity = '1';
                // Auto-save to server
                saveRecordingToServer();
            }}
        }}

        function saveRecordingToServer() {{
            if (scChunks.length === 0) return;
            const blob = new Blob(scChunks, {{ type: 'video/webm' }});
            const filename = 'meeting_recording_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.webm';
            const formData = new FormData();
            formData.append('file', blob, filename);

            document.getElementById('scStatus').innerHTML =
                '<span style="color: #89b4fa;">Saving recording to server...</span>';

            fetch('{server_url}/api/upload-recording', {{
                method: 'POST',
                body: formData
            }})
            .then(resp => resp.json())
            .then(data => {{
                document.getElementById('scStatus').innerHTML =
                    '<span style="color: #a6e3a1;">Saved: ' + data.filename + ' (' + formatTime(scSeconds) + ')</span>';
            }})
            .catch(err => {{
                document.getElementById('scStatus').innerHTML =
                    '<span style="color: #f9e2af;">Stopped - ' + formatTime(scSeconds) + ' (server save failed)</span>';
                console.error('Upload error:', err);
            }});
        }}

        function downloadRecording() {{
            if (scChunks.length === 0) return;
            const blob = new Blob(scChunks, {{ type: 'video/webm' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'meeting_recording_' + new Date().toISOString().slice(0,19).replace(/:/g,'-') + '.webm';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}

        function scAddEntry(time, text) {{
            const box = document.getElementById('sc-transcript-box');
            if (box.querySelector('p[style*="italic"]')) box.innerHTML = '';
            const entry = document.createElement('div');
            entry.style.cssText = 'padding: 0.6rem 1rem; margin: 0.4rem 0; border-radius: 8px; background: #313244; border-left: 3px solid #f97316;';
            entry.innerHTML = '<div style="font-size: 0.75rem; color: #89b4fa; font-weight: 600;">' + time + '</div>' +
                '<div style="font-size: 0.95rem; color: #cdd6f4; margin-top: 0.2rem;">' + text + '</div>';
            box.appendChild(entry);
            box.scrollTop = box.scrollHeight;
        }}
    </script>
    """

    st.components.v1.html(screen_capture_html, height=580)

with tab3:
    st.markdown("#### Session History")
    
    if all_transcripts:
        for session_id, entries in sorted(all_transcripts.items(), reverse=True):
            with st.expander(f"Session: {session_id} ({len(entries)} segments)", expanded=False):
                for entry in entries:
                    st.markdown(f"""
                    <div class="transcript-entry">
                        <div class="transcript-time">{entry.get('time', '')}</div>
                        <div class="transcript-text">{entry.get('text', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No sessions recorded yet. Start a recording to see transcripts here.")

# --- Auto-refresh ---
st.markdown("---")
col_refresh, col_info = st.columns([1, 3])
with col_refresh:
    if st.button("Refresh Transcripts"):
        st.rerun()
with col_info:
    st.caption("Transcripts update automatically when you refresh. The live view in the recording tab updates in real-time via WebSocket.")
