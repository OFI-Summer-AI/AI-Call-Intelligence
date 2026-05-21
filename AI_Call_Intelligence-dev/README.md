# Clario — AI Call Intelligence Platform

Clario records meetings, transcribes audio, and runs an 8-stage AI pipeline to extract insights, score call quality, flag risks, and generate PDF reports. It ships as a FastAPI backend with a pre-built React frontend.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [All Python Packages](#all-python-packages)
4. [Local Setup — Mac](#local-setup--mac)
5. [Local Setup — Windows](#local-setup--windows)
6. [Google OAuth Setup (Gmail / Calendar)](#google-oauth-setup-gmail--calendar)
7. [Deploy to Railway (Backend)](#deploy-to-railway-backend)
8. [Deploy to Vercel (Frontend)](#deploy-to-vercel-frontend)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────────────────────────────┐
│  Frontend  (React — static files)        │
│  • Locally   → served by FastAPI         │
│  • Production → hosted on Vercel         │
└──────────────────┬───────────────────────┘
                   │  HTTP / WebSocket
┌──────────────────▼───────────────────────┐
│  Backend  (FastAPI + Uvicorn)            │
│  • Locally   → python run.py  (:8000)    │
│  • Production → Docker on Railway (:8080)│
│                                          │
│  Pipeline: Audio → Whisper STT →         │
│  Diarization → Merge → Polish →          │
│  Extract Fields → Risk → Assessment      │
└──────────────────────────────────────────┘
```

**Production deployment model:**
- **Railway** runs the Docker container — handles the FastAPI server, Whisper STT, and all AI processing
- **Vercel** hosts only the static React files — zero compute, just file serving
- At Vercel build time, `vercel.json` injects your Railway URL into `index.html` so the frontend knows where to call the API

---

## Prerequisites

Install these **before** any of the setup steps below. Required on every machine.

### 1. Python 3.11

- Download from https://www.python.org/downloads/
- During Windows install, tick **"Add Python to PATH"**
- Verify: `python --version` (Windows) or `python3 --version` (Mac)

### 2. FFmpeg (system binary)

The app calls `ffmpeg` directly as a subprocess — it is **not** a pip package.

**Mac:**
```bash
brew install ffmpeg
```
Verify: `ffmpeg -version`

**Windows:**
1. Download `ffmpeg-release-full.7z` from https://www.gyan.dev/ffmpeg/builds/
2. Extract to `C:\ffmpeg\`
3. Add `C:\ffmpeg\bin` to your system **PATH**:
   - Search → "Environment Variables" → System Variables → `Path` → Edit → New → `C:\ffmpeg\bin`
4. Open a new terminal and verify: `ffmpeg -version`

If you cannot add to PATH, set these in your `.env` file instead:
```
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
FFPROBE_PATH=C:\ffmpeg\bin\ffprobe.exe
```

### 3. Git

- Download from https://git-scm.com/

---

## All Python Packages

### Installed via `pip install -r requirements.txt`

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.110.0 | Web framework |
| `uvicorn` | >=0.29.0 | ASGI server to run FastAPI |
| `starlette` | >=0.36.0 | ASGI toolkit (middleware, routing) |
| `python-multipart` | >=0.0.9 | Enables file uploads (`UploadFile`) |
| `websockets` | >=12.0 | WebSocket live transcription endpoint |
| `openai` | >=1.30.0 | LLM calls (GPT-4o-mini) + OpenAI STT backend |
| `openai-whisper` | >=20231117 | Local Whisper speech-to-text |
| `numpy` | >=1.24.0 | Required internally by Whisper |
| `pyannote.audio` | >=3.1.1 | Speaker diarization (optional) |
| `python-dotenv` | >=1.0.0 | Loads `.env` file into environment |
| `pydantic` | >=2.6.0 | Request/response data validation |
| `pandas` | >=2.0.0 | Data manipulation in PDF chart helpers |
| `httpx` | >=0.27.0 | Async HTTP client (auto-leave watcher) |
| `requests` | >=2.31.0 | HTTP client (Outlook calendar watcher) |
| `fpdf2` | >=2.7.6 | PDF report generation |
| `playwright` | >=1.40.0 | Headless browser for meeting bot |
| `google-auth` | >=2.28.0 | Google API authentication |
| `google-auth-oauthlib` | >=1.2.0 | Google OAuth2 flow |
| `google-api-python-client` | >=2.120.0 | Google Calendar API client |
| `msal` | >=1.27.0 | Microsoft identity / Outlook calendar |
| `APScheduler` | >=3.10.4 | Background job scheduler for calendar watcher |
| `python-dateutil` | >=2.9.0 | Date parsing utilities |

### Installed separately (NOT in requirements.txt)

| Dependency | Install command | Why separate |
|------------|----------------|--------------|
| `torch` + `torchaudio` | `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu` | CPU vs GPU builds are very different; installing wrong one wastes 2GB+. The Dockerfile handles it explicitly. |
| `ffmpeg` (binary) | `brew install ffmpeg` / gyan.dev / `apt-get` | System binary, not a Python package. The app calls it via `subprocess`. |

### Playwright browser (post-install step)

After `pip install -r requirements.txt`, run:
```bash
playwright install chromium
```
This downloads the ~150MB Chromium browser used by the meeting bot.

---

## Local Setup — Mac

Follow every step in order.

### Step 1 — Install system dependencies

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FFmpeg
brew install ffmpeg

# Verify
ffmpeg -version
python3 --version   # should be 3.10 or 3.11
```

### Step 2 — Create a virtual environment

```bash
cd AI_Call_refactor

python3 -m venv .venv
source .venv/bin/activate
```

Your terminal prompt will show `(.venv)` when the environment is active. Run `source .venv/bin/activate` again any time you open a new terminal.

### Step 3 — Install PyTorch (CPU-only)

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

This takes 2–5 minutes. Do this **before** requirements.txt or pip may pull the wrong torch build.

### Step 4 — Install all other dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Install Playwright browser

```bash
playwright install chromium
```

### Step 6 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
OPENAI_API_KEY=sk-...
GOOGLE_ACCOUNT_EMAIL=you@gmail.com
GOOGLE_ACCOUNT_PASSWORD=your_app_password
```

See [Environment Variables Reference](#environment-variables-reference) for all options.

### Step 7 — Start the server

```bash
python run.py
```

Open http://localhost:8000 in your browser.

### Kill port 8000 if already in use

```bash
kill -9 $(lsof -ti :8000)
```

---

## Local Setup — Windows

Follow every step in order. Use **PowerShell** (not Command Prompt).

### Step 1 — Install system dependencies

1. **Python 3.11** — https://www.python.org/downloads/windows/
   - During install: tick **"Add Python 3.11 to PATH"**
   - Verify in a new PowerShell: `python --version`

2. **FFmpeg**
   - Download `ffmpeg-release-full.7z` from https://www.gyan.dev/ffmpeg/builds/
   - Extract to `C:\ffmpeg\`
   - Add `C:\ffmpeg\bin` to PATH:
     - Search → "Edit the system environment variables" → Environment Variables → under System Variables find `Path` → Edit → New → type `C:\ffmpeg\bin` → OK all dialogs
   - Open a new PowerShell and verify: `ffmpeg -version`

3. **Git** — https://git-scm.com/download/win

### Step 2 — Allow PowerShell scripts

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

You only need to do this once per machine.

### Step 3 — Create a virtual environment

```powershell
cd path\to\AI_Call_refactor

python -m venv .venv
.venv\Scripts\Activate.ps1
```

Your prompt will show `(.venv)`. Run `.venv\Scripts\Activate.ps1` again whenever you open a new PowerShell window.

### Step 4 — Install PyTorch (CPU-only)

```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

This takes 2–5 minutes. Do this **before** requirements.txt.

### Step 5 — Install all other dependencies

```powershell
pip install -r requirements.txt
```

### Step 6 — Install Playwright browser

```powershell
playwright install chromium
```

If this fails with a permissions error, run PowerShell as Administrator for this step only, then go back to normal PowerShell.

### Step 7 — Configure environment variables

```powershell
copy .env.example .env
```

Open `.env` in Notepad or VS Code and fill in at minimum:

```env
OPENAI_API_KEY=sk-...
GOOGLE_ACCOUNT_EMAIL=you@gmail.com
GOOGLE_ACCOUNT_PASSWORD=your_app_password

# Only needed if ffmpeg is NOT on your PATH:
FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
FFPROBE_PATH=C:\ffmpeg\bin\ffprobe.exe
```

### Step 8 — Start the server

```powershell
python run.py
```

Open http://localhost:8000 in your browser.

### Kill port 8000 if already in use

```powershell
# Find the PID using port 8000
netstat -ano | findstr :8000

# Kill it (replace 1234 with the actual PID from the output above)
taskkill /PID 1234 /F
```

### Windows-specific notes

- Always use `python`, not `python3`, in PowerShell
- The `data/` folder is created automatically on first run — don't create it manually
- On first Google Calendar auth, a real Chromium window will open — don't close it until you've logged in

---

## Google OAuth Setup (Gmail / Calendar)

The app needs two files to access your Google Calendar and join Google Meet meetings:

| File | What it is |
|------|-----------|
| `credentials.json` | OAuth2 client secret — identifies your Google Cloud app |
| `google_token.json` | Your personal access token — generated automatically on first run |

> **The `google_token.json` already in this repo belongs to the previous developer. Delete it — it won't work for you.**

### Step 1 — Create a Google Cloud project

1. Go to https://console.cloud.google.com
2. Click the project dropdown (top-left) → **New Project**
3. Name it anything (e.g. `clario`) → **Create**
4. Confirm the new project is selected in the dropdown

### Step 2 — Enable Google Calendar API

1. Left sidebar → **APIs & Services → Library**
2. Search **Google Calendar API** → click it → **Enable**

### Step 3 — Create OAuth credentials

1. Left sidebar → **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. If asked to configure consent screen first:
   - User type: **External** → Create
   - App name: `Clario` (or anything)
   - Support email: your Gmail
   - Click **Save and Continue** through all steps
   - On **Test users**: click **+ Add Users** → add your Gmail → Save
4. Back at Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: anything → **Create**
5. Click **Download JSON** → rename the file to `credentials.json`
6. Place `credentials.json` inside the `AI_Call_refactor/` folder (same level as `run.py`)

### Step 4 — Set .env variables

```env
ENABLE_GOOGLE_CALENDAR=true
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=google_token.json
GOOGLE_ACCOUNT_EMAIL=you@gmail.com
GOOGLE_ACCOUNT_PASSWORD=your_app_password
```

> `GOOGLE_ACCOUNT_PASSWORD` is used by Playwright to log into Google Meet in the browser. If you have 2-Step Verification enabled, create a **Google App Password** at https://myaccount.google.com/apppasswords and use that here instead of your real password.

### Step 5 — First-run browser login

Start the server (`python run.py`) with `ENABLE_GOOGLE_CALENDAR=true`. On first start it will:

1. Detect `google_token.json` is missing
2. Open a browser window → log in with Google → grant calendar read permission
3. Save the token to `google_token.json` — all future runs reuse it silently

### Protect your credentials

```bash
# Mac/Linux — add to .gitignore
echo "credentials.json" >> .gitignore
echo "google_token.json" >> .gitignore
```

```powershell
# Windows PowerShell
Add-Content .gitignore "credentials.json"
Add-Content .gitignore "google_token.json"
```

**Never commit these files to git** — they give access to your Google account.

### Sharing the app with a colleague

Each person creates their own `credentials.json` from the same Google Cloud project (just download the client secret again) and does their own first-run browser login. These files are personal and cannot be shared.

---

## Deploy to Railway (Backend)

Railway runs the full backend inside Docker — FastAPI server, Whisper STT, all processing. FFmpeg is installed automatically by the Dockerfile.

### Step 1 — Push code to GitHub

Make sure your latest code is pushed to a GitHub repository.

### Step 2 — Create a Railway project

1. Go to https://railway.app → log in
2. Click **New Project → Deploy from GitHub repo**
3. Select your repository
4. Railway will detect `railway.toml` and use the Dockerfile automatically

### Step 3 — Set environment variables

In Railway → your service → **Variables** tab, add these one by one:

```
OPENAI_API_KEY        = sk-...
LLM_MODEL             = gpt-4o-mini
STT_BACKEND           = whisper
WHISPER_MODEL_SIZE    = small
ENABLE_DIARIZATION    = false
PORT                  = 8080
ENABLE_GOOGLE_CALENDAR  = false
ENABLE_OUTLOOK_CALENDAR = false
```

> Set `ENABLE_GOOGLE_CALENDAR=false` on Railway. The meeting bot needs an interactive browser login which doesn't work in a headless container. Run the calendar watcher locally if you need it.

### Step 4 — Deploy

Click **Deploy**. The first build takes **5–15 minutes** — it downloads PyTorch CPU wheels (~800MB) and the Whisper model.

Subsequent deploys are faster because Railway caches Docker layers.

### Step 5 — Get your public URL

Go to your service → **Settings → Networking → Public Networking** → **Generate Domain**.

Your URL will look like:
```
https://your-app-name.up.railway.app
```

Save this — you need it for Vercel.

### Step 6 — Verify

```bash
curl https://your-app-name.up.railway.app/health
# Expected: {"status":"ok","whisper_model":"small"}
```

---

## Deploy to Vercel (Frontend)

Vercel hosts only the static React files. It is not running any Python — it just serves HTML/JS and injects the Railway URL into the page at build time.

### Step 1 — Import project to Vercel

1. Go to https://vercel.com → log in
2. Click **Add New → Project**
3. Click **Import** next to your GitHub repository
4. Vercel will detect `vercel.json` automatically — no build settings to change

### Step 2 — Add environment variable

Before deploying, go to **Environment Variables** in the project settings and add:

| Name | Value |
|------|-------|
| `RAILWAY_URL` | `https://your-app-name.up.railway.app` |

This is the Railway URL from the previous section.

### Step 3 — Deploy

Click **Deploy**. Vercel only copies static files, so it finishes in ~30 seconds.

### Step 4 — Verify

Open your Vercel URL (e.g. `https://your-project.vercel.app`). The React UI should load and successfully talk to the Railway backend.

### How the URL injection works

`vercel.json` runs this shell command at build time:

```bash
sed -i "s|__RAILWAY_URL__|${RAILWAY_URL}|g" AI_Call_refactor/app/static/index.html
```

It replaces the `__RAILWAY_URL__` placeholder in `index.html` with your actual Railway URL. When running locally, the React app automatically falls back to `http://localhost:8000`.

### Redeploy after changing Railway URL

If your Railway URL ever changes, update the `RAILWAY_URL` environment variable in Vercel and click **Redeploy** (Deployments tab → three-dot menu → Redeploy).

---

## Environment Variables Reference

Copy `.env.example` to `.env` and fill in the values below.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | — | OpenAI API key (`sk-...`) |
| `LLM_MODEL` | No | `gpt-4o-mini` | LLM model for extraction and assessment |
| `STT_BACKEND` | No | `whisper` | `whisper` (local) or `openai_diarize` (OpenAI API) |
| `WHISPER_MODEL_SIZE` | No | `base` | `tiny` / `base` / `small` / `medium` / `large` |
| `FFMPEG_PATH` | No | auto | Full path to `ffmpeg` binary — set on Windows if not on PATH |
| `FFPROBE_PATH` | No | auto | Full path to `ffprobe` binary — set on Windows if not on PATH |
| `ENABLE_DIARIZATION` | No | `false` | Enable speaker diarization via pyannote |
| `DIARIZATION_HF_TOKEN` | If diarization | — | Hugging Face token for pyannote model download |
| `PIPELINE_RESUME` | No | `false` | `true` = skip pipeline stages that already have output on disk |
| `PORT` | No | `8000` | HTTP port (Railway overrides this to `8080`) |
| `ENABLE_GOOGLE_CALENDAR` | No | `true` | Enable Google Calendar watcher |
| `GOOGLE_CREDENTIALS_FILE` | If Google | `credentials.json` | Path to OAuth2 client secret file |
| `GOOGLE_TOKEN_FILE` | If Google | `google_token.json` | Path to OAuth2 token file (auto-created on first run) |
| `GOOGLE_ACCOUNT_EMAIL` | If Google | — | Gmail address for meeting bot browser login |
| `GOOGLE_ACCOUNT_PASSWORD` | If Google | — | Gmail password or App Password (if 2FA enabled) |
| `ENABLE_OUTLOOK_CALENDAR` | No | `false` | Enable Microsoft Outlook / Teams calendar |
| `MICROSOFT_CLIENT_ID` | If Outlook | — | Azure app registration client ID |
| `MICROSOFT_TENANT_ID` | If Outlook | `common` | Azure tenant ID |
| `BOT_NAME` | No | `Clario` | Display name shown in meeting participants list |
| `JOIN_EARLY_SECONDS` | No | `120` | How many seconds before meeting start to join |
| `CALENDAR_POLL_INTERVAL` | No | `5` | Minutes between calendar checks |
| `BOT_POLL_INTERVAL_SEC` | No | `10` | Seconds between participant count checks |
| `BOT_GRACE_SECONDS` | No | `30` | Seconds to wait after last participant leaves before bot exits |

---

## Troubleshooting

### Port 8000 already in use

**Mac:**
```bash
kill -9 $(lsof -ti :8000)
```

**Windows:**
```powershell
netstat -ano | findstr :8000
taskkill /PID 1234 /F    # replace 1234 with the PID shown above
```

### `ffmpeg: command not found` or `ffmpeg not found`

FFmpeg is not installed or not on your PATH.

- **Mac:** `brew install ffmpeg`
- **Windows:** Add `C:\ffmpeg\bin` to PATH (see Prerequisites), or set `FFMPEG_PATH` in `.env`

### Whisper model downloads on first run

Normal — Whisper downloads model weights the first time. Sizes: `tiny` ~75MB, `small` ~460MB, `medium` ~1.5GB. Set `WHISPER_MODEL_SIZE=tiny` to speed up first-run during testing.

### `playwright install chromium` fails on Windows

Run PowerShell as Administrator for this one step:
```powershell
playwright install chromium --with-deps
```

### `torch` not found after installing requirements.txt

PyTorch must be installed **before** requirements.txt with the CPU-specific index URL. Run:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Vercel build: `RAILWAY_URL not set, skipping substitution`

The `RAILWAY_URL` environment variable was not set in Vercel before deploying. Add it in Vercel → your project → **Settings → Environment Variables**, then redeploy.

### Railway health check timeout on first deploy

The first deploy downloads PyTorch + Whisper which can take 10+ minutes. This is expected. If the health check times out, increase `healthcheckTimeout` in `railway.toml` (currently 300 seconds).

### Google Calendar: `credentials.json not found`

Place `credentials.json` in the `AI_Call_refactor/` folder (same level as `run.py`) and set `GOOGLE_CREDENTIALS_FILE=credentials.json` in `.env`. See [Google OAuth Setup](#google-oauth-setup-gmail--calendar).

### Google Calendar bot not joining meetings on Railway

The Playwright meeting bot requires an interactive browser session for Google login, which cannot run in a headless Docker container. Run the calendar watcher locally with `python main_agent.py` and point `OPENAI_API_KEY` + API calls at your Railway backend URL.
