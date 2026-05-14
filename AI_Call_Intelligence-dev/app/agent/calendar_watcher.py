"""
Calendar watchers for Google Calendar and Microsoft Outlook.

Google Calendar setup:
  1. Go to console.cloud.google.com → create a project
  2. Enable "Google Calendar API"
  3. Create OAuth 2.0 credentials (Desktop app) → download as credentials.json
  4. Set GOOGLE_CREDENTIALS_FILE=path/to/credentials.json in .env
  First run will open a browser for OAuth consent; token saved to GOOGLE_TOKEN_FILE.

Microsoft Outlook setup:
  1. Go to portal.azure.com → App registrations → New registration
  2. Set redirect URI: https://login.microsoftonline.com/common/oauth2/nativeclient
  3. Add API permissions: Calendars.Read (Microsoft Graph, delegated)
  4. Set MICROSOFT_CLIENT_ID and MICROSOFT_TENANT_ID in .env
  First run uses device-code flow (prints a URL + code to authenticate).
"""

import os
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.agent.link_extractor import extract_meeting_url
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MeetingEvent:
    event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    join_url: str
    platform: str  # 'zoom' | 'meet' | 'teams'
    source: str    # 'google' | 'outlook'


def _search_for_link(fields: list[str]) -> tuple[str, str] | None:
    """Try each field string for a meeting URL."""
    for text in fields:
        result = extract_meeting_url(text or "")
        if result:
            return result
    return None


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

class GoogleCalendarWatcher:
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self):
        self._creds_file = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))
        self._token_file = Path(os.getenv("GOOGLE_TOKEN_FILE", "google_token.json"))
        self._service = None

    def _build_service(self):
        if self._service:
            return self._service

        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        if self._token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_file), self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._creds_file.exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {self._creds_file}. "
                        "See app/agent/calendar_watcher.py for setup instructions."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self._creds_file), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            self._token_file.write_text(creds.to_json())

        self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def get_upcoming_meetings(self, hours_ahead: int = 24) -> list[MeetingEvent]:
        try:
            service = self._build_service()
        except Exception as exc:
            logger.error("Google Calendar unavailable: %s", exc)
            return []

        now = datetime.now(timezone.utc)
        time_max = now + timedelta(hours=hours_ahead)

        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        meetings = []
        for item in result.get("items", []):
            start_str = item.get("start", {}).get("dateTime")
            end_str = item.get("end", {}).get("dateTime")
            if not start_str:
                continue  # all-day event, skip

            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)

            # Look for meeting link in conference data, location, description
            conference_uri = ""
            for ep in item.get("conferenceData", {}).get("entryPoints", []):
                if ep.get("entryPointType") == "video":
                    conference_uri = ep.get("uri", "")
                    break

            found = _search_for_link([
                conference_uri,
                item.get("location", ""),
                item.get("description", ""),
            ])
            if not found:
                continue

            join_url, platform = found
            meetings.append(MeetingEvent(
                event_id=item["id"],
                title=item.get("summary", "Untitled Meeting"),
                start_time=start,
                end_time=end,
                join_url=join_url,
                platform=platform,
                source="google",
            ))
            logger.info("Google event found: '%s' at %s [%s]", item.get("summary"), start, platform)

        return meetings


# ---------------------------------------------------------------------------
# Microsoft Outlook (Graph API)
# ---------------------------------------------------------------------------

class OutlookCalendarWatcher:
    GRAPH_SCOPE = ["https://graph.microsoft.com/Calendars.Read"]
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self._client_id = os.getenv("MICROSOFT_CLIENT_ID", "")
        self._tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
        self._token_cache_file = Path(os.getenv("OUTLOOK_TOKEN_FILE", "outlook_token.json"))
        self._app = None

    def _build_app(self):
        if self._app:
            return self._app
        if not self._client_id:
            raise ValueError(
                "MICROSOFT_CLIENT_ID not set. "
                "See app/agent/calendar_watcher.py for setup instructions."
            )
        import msal

        cache = msal.SerializableTokenCache()
        if self._token_cache_file.exists():
            cache.deserialize(self._token_cache_file.read_text())

        self._app = msal.PublicClientApplication(
            self._client_id,
            authority=f"https://login.microsoftonline.com/{self._tenant_id}",
            token_cache=cache,
        )
        self._cache = cache
        return self._app

    def _get_token(self) -> str:
        app = self._build_app()
        accounts = app.get_accounts()
        result = None
        if accounts:
            result = app.acquire_token_silent(self.GRAPH_SCOPE, account=accounts[0])

        if not result:
            flow = app.initiate_device_flow(scopes=self.GRAPH_SCOPE)
            print("\n" + flow["message"])
            result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise RuntimeError(f"Outlook auth failed: {result.get('error_description')}")

        self._token_cache_file.write_text(self._cache.serialize())
        return result["access_token"]

    def get_upcoming_meetings(self, hours_ahead: int = 24) -> list[MeetingEvent]:
        try:
            token = self._get_token()
        except Exception as exc:
            logger.error("Outlook Calendar unavailable: %s", exc)
            return []

        import requests as http

        now = datetime.now(timezone.utc)
        time_max = now + timedelta(hours=hours_ahead)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        params = {
            "startDateTime": now.isoformat(),
            "endDateTime": time_max.isoformat(),
            "$select": "id,subject,start,end,location,bodyPreview,onlineMeeting",
            "$orderby": "start/dateTime",
        }
        resp = http.get(
            f"{self.GRAPH_ENDPOINT}/me/calendarView",
            headers=headers,
            params=params,
            timeout=15,
        )
        resp.raise_for_status()

        meetings = []
        for item in resp.json().get("value", []):
            start = datetime.fromisoformat(item["start"]["dateTime"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(item["end"]["dateTime"].replace("Z", "+00:00"))

            online_url = (item.get("onlineMeeting") or {}).get("joinUrl", "")
            found = _search_for_link([
                online_url,
                (item.get("location") or {}).get("displayName", ""),
                item.get("bodyPreview", ""),
            ])
            if not found:
                continue

            join_url, platform = found
            meetings.append(MeetingEvent(
                event_id=item["id"],
                title=item.get("subject", "Untitled Meeting"),
                start_time=start,
                end_time=end,
                join_url=join_url,
                platform=platform,
                source="outlook",
            ))
            logger.info("Outlook event found: '%s' at %s [%s]", item.get("subject"), start, platform)

        return meetings
