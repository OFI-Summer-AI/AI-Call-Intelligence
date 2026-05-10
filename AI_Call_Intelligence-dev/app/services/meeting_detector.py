"""
Detects active meeting windows on Windows.
Supports: Microsoft Teams, Zoom, Google Meet, Webex, Slack Huddle.
"""

import ctypes
import ctypes.wintypes
import re

# Window-title patterns that indicate an active call/meeting
_MEETING_PATTERNS = [
    # Microsoft Teams (new & classic)
    re.compile(r"Microsoft Teams.*(?:Meeting|Call)", re.IGNORECASE),
    re.compile(r"Meeting with", re.IGNORECASE),
    re.compile(r"Teams.*\|.*(?:Meeting|Call)", re.IGNORECASE),
    # Zoom
    re.compile(r"Zoom Meeting", re.IGNORECASE),
    re.compile(r"Zoom Webinar", re.IGNORECASE),
    # Google Meet (browser tab title)
    re.compile(r"Meet\s*[-–—]\s*\w", re.IGNORECASE),
    re.compile(r"meet\.google\.com", re.IGNORECASE),
    # Webex
    re.compile(r"Webex\s+Meeting", re.IGNORECASE),
    re.compile(r"Cisco Webex", re.IGNORECASE),
    # Slack Huddle
    re.compile(r"Slack.*Huddle", re.IGNORECASE),
    # Generic "in a call" indicators
    re.compile(r"Screen sharing", re.IGNORECASE),
]

# Process names whose mere presence hints at a meeting
_MEETING_PROCESSES = {
    "zoom.exe",
    "ciscocollabhost.exe",  # Webex
}


def _enum_window_titles() -> list[str]:
    """Return titles of all visible windows using Win32 API."""
    titles = []
    EnumWindows = ctypes.windll.user32.EnumWindows
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    GetWindowTextW = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HWND,
        ctypes.wintypes.LPARAM,
    )

    def callback(hwnd, _):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                titles.append(buf.value)
        return True

    EnumWindows(WNDENUMPROC(callback), 0)
    return titles


def is_meeting_active() -> tuple[bool, str | None]:
    """
    Check if any visible window matches a known meeting pattern.
    Returns (True, matched_title) or (False, None).
    """
    titles = _enum_window_titles()
    for title in titles:
        for pattern in _MEETING_PATTERNS:
            if pattern.search(title):
                return True, title
    return False, None
