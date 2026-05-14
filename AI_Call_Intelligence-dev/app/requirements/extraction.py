"""
Stage 3A: LLM Requirement Extraction
- Calls LLM via litellm (model swappable via LLM_MODEL env var)
- Extracts structured requirements from full transcript text
- Retries once with stricter prompt on JSON parse failure
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import litellm
from rich.console import Console

from app.requirements.ingestion import TranscriptData

console = Console()

SYSTEM_PROMPT = """You are a business analyst. Read this meeting transcript and extract ALL \
requirements discussed. Return ONLY a valid JSON array. Each item must have:
{
  "id": "REQ-001",
  "type": "functional | non_functional | constraint | assumption",
  "title": "short title max 8 words",
  "description": "full requirement in one clear sentence",
  "priority": "must_have | should_have | nice_to_have",
  "raised_by": "customer | team | both",
  "keywords": ["array", "of", "3-5", "key", "terms"]
}
Extract EVERY requirement, no matter how minor. Do not infer anything not explicitly stated. \
Return raw JSON only, no markdown."""

STRICT_SYSTEM_PROMPT = """You are a business analyst. Your previous response was not valid JSON.
Read the transcript and extract requirements.
Return ONLY a raw JSON array — no markdown fences, no explanations, nothing else.
Start your response with [ and end with ].
Each element must have exactly these keys: id, type, title, description, priority, raised_by, keywords."""

VALID_TYPES = {"functional", "non_functional", "constraint", "assumption"}
VALID_PRIORITIES = {"must_have", "should_have", "nice_to_have"}
VALID_RAISED_BY = {"customer", "team", "both"}


@dataclass
class Requirement:
    id: str
    type: str
    title: str
    description: str
    priority: str
    raised_by: str
    keywords: list[str] = field(default_factory=list)

    best_score: float = 0.0
    best_chunk: str = ""
    best_timestamp: float = 0.0
    top3_chunks: list[dict] = field(default_factory=list)
    confidence_tier: str = "unverified"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "raised_by": self.raised_by,
            "keywords": self.keywords,
            "best_score": round(self.best_score, 4),
            "best_chunk": self.best_chunk,
            "best_timestamp": self.best_timestamp,
            "top3_chunks": self.top3_chunks,
            "confidence_tier": self.confidence_tier,
        }


def _strip_markdown(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _normalise_requirement(raw: dict, idx: int) -> dict:
    req_type = raw.get("type", "functional").lower().replace(" ", "_")
    priority = raw.get("priority", "should_have").lower().replace(" ", "_")
    raised_by = raw.get("raised_by", "team").lower()
    keywords = raw.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = [str(keywords)]
    return {
        "id": raw.get("id") or f"REQ-{idx + 1:03d}",
        "type": req_type if req_type in VALID_TYPES else "functional",
        "title": str(raw.get("title", "Untitled requirement"))[:80],
        "description": str(raw.get("description", "")),
        "priority": priority if priority in VALID_PRIORITIES else "should_have",
        "raised_by": raised_by if raised_by in VALID_RAISED_BY else "team",
        "keywords": [str(k) for k in keywords[:5]],
    }


def extract_requirements(transcript: TranscriptData, model: str) -> list[Requirement]:
    full_text = transcript.full_dialogue
    console.print(f"[cyan]→[/cyan] Stage 3A: Extracting requirements via [bold]{model}[/bold] …")

    for attempt in range(2):
        system = SYSTEM_PROMPT if attempt == 0 else STRICT_SYSTEM_PROMPT
        try:
            response = litellm.completion(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": full_text},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            content = response.choices[0].message.content or ""
            content = _strip_markdown(content)
            raw_list = json.loads(content)
            if not isinstance(raw_list, list):
                raise ValueError("LLM returned non-list JSON")
            requirements = [
                Requirement(**_normalise_requirement(r, i))
                for i, r in enumerate(raw_list)
                if isinstance(r, dict)
            ]
            console.print(f"[green]✓[/green] Extracted [bold]{len(requirements)}[/bold] requirements")
            return requirements

        except (json.JSONDecodeError, ValueError) as exc:
            if attempt == 0:
                console.print(f"[yellow]⚠[/yellow] JSON parse failed ({exc}), retrying …")
                continue
            console.print(f"[red]✗[/red] Extraction failed: {exc}")
            return []
        except Exception as exc:
            console.print(f"[red]✗[/red] LLM call failed: {exc}")
            raise

    return []
