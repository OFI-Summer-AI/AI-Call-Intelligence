FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY AI_Call_refactor/requirements.txt .

# CPU-only torch first (avoids 2GB CUDA download)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Remaining deps
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browser (for meeting bot)
RUN playwright install chromium --with-deps

COPY AI_Call_refactor/ .

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
