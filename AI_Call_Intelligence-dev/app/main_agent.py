"""
AI Call Intelligence — Meeting Bot Agent

Usage:
    python -m app.main_agent

Environment variables (set in .env):
    # Google Calendar
    ENABLE_GOOGLE_CALENDAR=true
    GOOGLE_CREDENTIALS_FILE=credentials.json      # OAuth client_secret from Google Cloud
    GOOGLE_TOKEN_FILE=google_token.json           # auto-created after first auth

    # Microsoft Outlook
    ENABLE_OUTLOOK_CALENDAR=false
    MICROSOFT_CLIENT_ID=<azure-app-client-id>
    MICROSOFT_TENANT_ID=common

    # Bot behaviour
    BOT_NAME=AI Notetaker
    JOIN_EARLY_SECONDS=120        # join 2 min before meeting start
    CALENDAR_POLL_INTERVAL=5      # poll calendar every 5 min

    # Whisper
    WHISPER_MODEL_SIZE=base
"""

import signal
import time

from app.logger import setup_logging, get_logger
from app.agent.scheduler import MeetingAgentScheduler

setup_logging()
logger = get_logger(__name__)


def main():
    logger.info("AI Call Intelligence Meeting Agent starting")
    scheduler = MeetingAgentScheduler()
    scheduler.start()

    # Keep alive until Ctrl+C
    stop_event = [False]

    def _shutdown(sig, frame):
        logger.info("Shutdown signal received")
        stop_event[0] = True

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop_event[0]:
            time.sleep(1)
    finally:
        scheduler.stop()
        logger.info("Meeting agent stopped")


if __name__ == "__main__":
    main()
