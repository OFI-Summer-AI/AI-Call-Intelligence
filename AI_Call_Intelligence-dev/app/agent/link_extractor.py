import re

_PATTERNS = {
    "zoom": re.compile(r"https://[a-z0-9.-]*zoom\.us/(?:j|wc)/\d+[^\s]*", re.I),
    "meet": re.compile(r"https://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}[^\s]*", re.I),
    "teams": re.compile(r"https://teams\.(?:microsoft|live)\.com/[^\s]+", re.I),
}


def extract_meeting_url(text: str) -> tuple[str, str] | None:
    """Return (url, platform) for the first meeting link found, or None."""
    for platform, pattern in _PATTERNS.items():
        match = pattern.search(text or "")
        if match:
            return match.group(0).rstrip(".,;)>"), platform
    return None


def zoom_web_url(url: str) -> str:
    """Convert a zoom.us/j/<id> link to the web-client URL (no app required)."""
    meeting_id = re.search(r"/j/(\d+)", url)
    if not meeting_id:
        return url
    pwd = re.search(r"[?&]pwd=([^&]+)", url)
    base = f"https://app.zoom.us/wc/{meeting_id.group(1)}/join"
    return f"{base}?pwd={pwd.group(1)}" if pwd else base
