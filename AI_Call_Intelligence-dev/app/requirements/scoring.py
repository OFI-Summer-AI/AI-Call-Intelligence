"""
Stage 4: Semantic Scoring
- Embeds each requirement description with SBERT
- Computes cosine similarity against transcript chunks
- Assigns confidence_tier: verified / ambiguous / unverified
"""

from __future__ import annotations

import numpy as np
from rich.console import Console
from rich.progress import track

from app.requirements.embedding import CorpusIndex, embed_texts
from app.requirements.extraction import Requirement

console = Console()

VERIFIED_THRESHOLD = 0.85
AMBIGUOUS_THRESHOLD = 0.60


def _cosine_similarities(query: np.ndarray, corpus: np.ndarray) -> np.ndarray:
    q_norm = query / (np.linalg.norm(query) + 1e-10)
    c_norms = np.linalg.norm(corpus, axis=1, keepdims=True) + 1e-10
    return (corpus / c_norms @ q_norm).astype(float)


def _assign_tier(score: float) -> str:
    if score >= VERIFIED_THRESHOLD:
        return "verified"
    if score >= AMBIGUOUS_THRESHOLD:
        return "ambiguous"
    return "unverified"


def score_requirements(requirements: list[Requirement], corpus: CorpusIndex) -> list[Requirement]:
    if not requirements:
        return []

    console.print(
        f"[cyan]→[/cyan] Stage 4: Scoring [bold]{len(requirements)}[/bold] requirements "
        f"against [bold]{corpus.size}[/bold] chunks …"
    )

    req_embeddings = embed_texts([r.description for r in requirements])
    scored: list[Requirement] = []

    for req, req_emb in track(list(zip(requirements, req_embeddings)), description="Scoring…", console=console):
        sims = _cosine_similarities(req_emb, corpus.embeddings)
        top_indices = np.argsort(sims)[::-1][:3]
        best_idx = int(top_indices[0])
        best_score = float(sims[best_idx])

        req.best_score = round(best_score, 4)
        req.best_chunk = corpus.chunks[best_idx].text[:400]
        req.best_timestamp = corpus.chunks[best_idx].start_time
        req.top3_chunks = [
            {
                "rank": rank + 1,
                "score": round(float(sims[idx]), 4),
                "text": corpus.chunks[idx].text[:300],
                "start_time": corpus.chunks[idx].start_time,
            }
            for rank, idx in enumerate(top_indices)
        ]
        req.confidence_tier = _assign_tier(best_score)
        scored.append(req)

    verified = sum(1 for r in scored if r.confidence_tier == "verified")
    ambiguous = sum(1 for r in scored if r.confidence_tier == "ambiguous")
    unverified = sum(1 for r in scored if r.confidence_tier == "unverified")
    console.print(
        f"[green]✓[/green] Scoring complete — "
        f"[green]verified={verified}[/green]  "
        f"[yellow]ambiguous={ambiguous}[/yellow]  "
        f"[red]unverified={unverified}[/red]"
    )
    return scored
