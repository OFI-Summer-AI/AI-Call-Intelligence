"""Pure helpers for PDF chart generation (no Streamlit)."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

import pandas as pd


def parse_ts(ts: str) -> float:
    try:
        parts = str(ts).strip().split(":")
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        if len(parts) == 2:
            m, s = int(parts[0]), float(parts[1])
            return m * 60 + s
    except (ValueError, TypeError):
        pass
    return 0.0


_POS = frozenset(
    "great good excellent yes interested love excited happy valuable strong clear win success progress agree opportunity".split()
)
_NEG = frozenset(
    "bad concern risk worried delay problem difficult expensive issue uncertain hesitate budget tight challenge wrong".split()
)


def sentiment_curve(transcript: list[dict[str, Any]], n_bins: int = 14) -> pd.DataFrame:
    if not transcript:
        return pd.DataFrame({"minute": [], "tone": []})
    max_end = max(parse_ts(s.get("end", "0")) for s in transcript) or 1.0
    texts: list[list[str]] = [[] for _ in range(n_bins)]
    for s in transcript:
        mid = (parse_ts(s.get("start", "0")) + parse_ts(s.get("end", "0"))) / 2.0
        b = min(int(mid / max_end * n_bins), n_bins - 1)
        words = re.findall(r"[a-zA-Z]+", str(s.get("text", "")).lower())
        texts[b].extend(words)
    scores = []
    for words in texts:
        if not words:
            scores.append(0.0)
            continue
        p = sum(1 for w in words if w in _POS)
        n = sum(1 for w in words if w in _NEG)
        denom = max(len(words), 1)
        scores.append((p - n) / denom * 3.0)
    minutes = [max_end * (i + 0.5) / n_bins / 60.0 for i in range(n_bins)]
    s = pd.Series(scores)
    if len(s) > 3:
        s = s.rolling(3, center=True, min_periods=1).mean()
    return pd.DataFrame({"minute": minutes, "tone": s.values})


def distinct_speakers(transcript: list[dict[str, Any]]) -> int:
    labels: set[str] = set()
    for s in transcript:
        r = s.get("role") or s.get("speaker")
        if r:
            labels.add(str(r).strip())
    return len(labels)
