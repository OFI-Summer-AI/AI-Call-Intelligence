"""
Stage 5: Metrics Computation & Report Generation
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

from app.requirements.embedding import CorpusIndex
from app.requirements.extraction import Requirement
from app.requirements.ingestion import TranscriptData

console = Console()

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "requirements"


def _tier_emoji(tier: str) -> str:
    return {"verified": "✓", "ambiguous": "⚠", "unverified": "✗"}.get(tier, "?")


def generate_report(transcript: TranscriptData, requirements: list[Requirement], corpus: CorpusIndex) -> dict:
    n = len(requirements)
    overall_accuracy = round(float(np.mean([r.best_score for r in requirements])), 4) if n else 0.0
    tier_counts = Counter(r.confidence_tier for r in requirements)
    return {
        "meta": {
            "meeting_id": transcript.meeting_id,
            "title": transcript.title,
            "date": transcript.date,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "total_turns": len(transcript.turns),
            "total_requirements": n,
        },
        "metrics": {
            "overall_accuracy": overall_accuracy,
            "verified_count": tier_counts.get("verified", 0),
            "ambiguous_count": tier_counts.get("ambiguous", 0),
            "unverified_count": tier_counts.get("unverified", 0),
            "by_type": dict(Counter(r.type for r in requirements)),
            "by_priority": dict(Counter(r.priority for r in requirements)),
            "customer_ratio": round(sum(1 for r in requirements if r.raised_by == "customer") / n, 4) if n else 0.0,
        },
        "requirements": [r.to_dict() for r in requirements],
        "chunks_used": corpus.size,
    }


def save_report(report: dict, output_dir: Path | None = None) -> Path:
    target = output_dir or OUTPUT_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"report_{report['meta']['meeting_id']}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"[green]✓[/green] Report saved → [bold]{path}[/bold]")
    return path


def print_summary(report: dict) -> None:
    meta = report["meta"]
    metrics = report["metrics"]
    reqs = report["requirements"]

    console.rule(f"[bold cyan]{meta['title']}[/bold cyan]")
    acc = metrics["overall_accuracy"]
    badge = (
        "[bold green]● HIGH CONFIDENCE[/bold green]" if acc >= 0.85
        else "[bold yellow]● REVIEW NEEDED[/bold yellow]" if acc >= 0.60
        else "[bold red]● LOW CONFIDENCE[/bold red]"
    )
    console.print(f"Overall Accuracy: [bold]{acc:.1%}[/bold]  {badge}\n")

    table = Table(title="Requirements Summary", show_lines=True)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title", min_width=30)
    table.add_column("Type", width=16)
    table.add_column("Priority", width=14)
    table.add_column("Score", width=7, justify="right")
    table.add_column("Tier", width=12)

    tier_styles = {"verified": "green", "ambiguous": "yellow", "unverified": "red"}
    for req in reqs:
        tier = req["confidence_tier"]
        style = tier_styles.get(tier, "white")
        table.add_row(
            req["id"], req["title"], req["type"], req["priority"],
            f"{req['best_score']:.3f}",
            f"[{style}]{_tier_emoji(tier)} {tier}[/{style}]",
        )
    console.print(table)

    n = meta["total_requirements"]
    v, a, u = metrics["verified_count"], metrics["ambiguous_count"], metrics["unverified_count"]
    if n:
        console.print(
            f"\n[green]Verified: {v}/{n} ({v/n:.0%})[/green]  "
            f"[yellow]Ambiguous: {a}/{n} ({a/n:.0%})[/yellow]  "
            f"[red]Unverified: {u}/{n} ({u/n:.0%})[/red]"
        )
