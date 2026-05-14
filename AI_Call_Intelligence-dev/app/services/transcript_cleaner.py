from typing import List, Dict
from app.logger import get_logger

logger = get_logger(__name__)


def clean_segments(segments: List[Dict]) -> List[Dict]:
    """
    Light cleanup:
    - trim spaces
    - remove empty segments
    """
    cleaned = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        cleaned.append(
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": " ".join(text.split()),
            }
        )
    dropped = len(segments) - len(cleaned)
    logger.debug("Cleaned segments: %d in, %d out, %d dropped", len(segments), len(cleaned), dropped)
    return cleaned