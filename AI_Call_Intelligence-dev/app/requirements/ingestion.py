"""
Stage 1-2: Ingestion & Validation
- Parse and validate transcript JSON
- Infer speaker_role from participant list if missing
- Produce clean flat turn list
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()

REQUIRED_TOP_FIELDS = {"meeting_id", "title", "date", "turns"}
REQUIRED_TURN_FIELDS = {"speaker", "text"}


@dataclass
class Turn:
    speaker: str
    role: str
    start_time: float
    end_time: float
    text: str

    def formatted(self) -> str:
        mins = int(self.start_time // 60)
        secs = int(self.start_time % 60)
        return f"[{mins:02d}:{secs:02d}] {self.speaker}: {self.text}"


@dataclass
class TranscriptData:
    meeting_id: str
    title: str
    date: str
    participants: list[dict]
    turns: list[Turn]
    _role_map: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def full_dialogue(self) -> str:
        return "\n".join(t.formatted() for t in self.turns)

    @property
    def customer_only(self) -> str:
        lines = [t.formatted() for t in self.turns if t.role == "customer"]
        return "\n".join(lines) if lines else "(no customer turns found)"

    @property
    def full_text_plain(self) -> str:
        return " ".join(t.text for t in self.turns)

    @property
    def total_duration(self) -> float:
        return self.turns[-1].end_time if self.turns else 0.0


def _build_role_map(participants: list[dict]) -> dict[str, str]:
    return {
        p.get("name", "").strip().lower(): p.get("role", "unknown").lower()
        for p in participants
        if p.get("name", "").strip()
    }


def _infer_role(speaker: str, role_map: dict[str, str], raw_role: str | None) -> str:
    if raw_role and raw_role.lower() in ("customer", "team"):
        return raw_role.lower()
    return role_map.get(speaker.lower(), "team")


def load_and_validate(source: str | Path | dict) -> TranscriptData:
    if isinstance(source, (str, Path)) and Path(source).exists():
        raw = json.loads(Path(source).read_text(encoding="utf-8"))
    elif isinstance(source, str):
        raw = json.loads(source)
    elif isinstance(source, dict):
        raw = source
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    missing = REQUIRED_TOP_FIELDS - raw.keys()
    if missing:
        raise ValueError(f"Transcript missing required fields: {sorted(missing)}")
    if not isinstance(raw["turns"], list) or len(raw["turns"]) == 0:
        raise ValueError("'turns' must be a non-empty list")

    participants = raw.get("participants", [])
    role_map = _build_role_map(participants)

    turns: list[Turn] = []
    for i, t in enumerate(raw["turns"]):
        missing_t = REQUIRED_TURN_FIELDS - t.keys()
        if missing_t:
            raise ValueError(f"Turn {i} missing fields: {sorted(missing_t)}")
        speaker = str(t["speaker"]).strip()
        text = str(t["text"]).strip()
        if not text:
            continue
        turns.append(Turn(
            speaker=speaker,
            role=_infer_role(speaker, role_map, t.get("speaker_role")),
            start_time=float(t.get("start_time", i * 30.0)),
            end_time=float(t.get("end_time", (i + 1) * 30.0)),
            text=text,
        ))

    if not turns:
        raise ValueError("No valid turns found after parsing")

    console.print(
        f"[green]✓[/green] Ingested [bold]{raw['title']}[/bold] — "
        f"{len(turns)} turns, {len(participants)} participants"
    )
    return TranscriptData(
        meeting_id=str(raw["meeting_id"]),
        title=str(raw["title"]),
        date=str(raw["date"]),
        participants=participants,
        turns=turns,
        _role_map=role_map,
    )
