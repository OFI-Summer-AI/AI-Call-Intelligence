"""
Stage 3B: Corpus Chunking & Embedding
- Chunks transcript into overlapping windows
- Embeds each chunk using sentence-transformers all-MiniLM-L6-v2
- Returns a CorpusIndex for cosine similarity lookup
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
from rich.console import Console
from sentence_transformers import SentenceTransformer

from app.requirements.ingestion import TranscriptData, Turn

console = Console()

CHUNK_SIZE_WORDS = 225
OVERLAP_WORDS = 37
SBERT_MODEL = "all-MiniLM-L6-v2"

_sbert: SentenceTransformer | None = None


def get_sbert() -> SentenceTransformer:
    global _sbert
    if _sbert is None:
        console.print(f"[cyan]→[/cyan] Loading SBERT model [bold]{SBERT_MODEL}[/bold] …")
        _sbert = SentenceTransformer(SBERT_MODEL)
        console.print("[green]✓[/green] SBERT model loaded")
    return _sbert


@dataclass
class Chunk:
    chunk_id: int
    text: str
    speakers_in_chunk: list[str]
    start_time: float
    end_time: float
    word_count: int


@dataclass
class CorpusIndex:
    chunks: list[Chunk]
    embeddings: np.ndarray
    model_name: str = SBERT_MODEL

    @property
    def size(self) -> int:
        return len(self.chunks)


def _turns_to_word_tokens(turns: list[Turn]) -> list[dict]:
    tokens: list[dict] = []
    for turn in turns:
        for word in turn.text.split():
            tokens.append({
                "word": word,
                "speaker": turn.speaker,
                "start_time": turn.start_time,
                "end_time": turn.end_time,
            })
    return tokens


def _sliding_windows(tokens: list[dict], chunk_size: int, overlap: int) -> Iterator[list[dict]]:
    step = chunk_size - overlap
    start = 0
    while start < len(tokens):
        yield tokens[start: start + chunk_size]
        start += step
        if start + chunk_size > len(tokens) and start < len(tokens):
            yield tokens[start:]
            break


def chunk_transcript(turns: list[Turn], chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS) -> list[Chunk]:
    tokens = _turns_to_word_tokens(turns)
    if not tokens:
        return []
    chunks: list[Chunk] = []
    for chunk_id, window in enumerate(_sliding_windows(tokens, chunk_size, overlap)):
        chunks.append(Chunk(
            chunk_id=chunk_id,
            text=" ".join(t["word"] for t in window),
            speakers_in_chunk=list(dict.fromkeys(t["speaker"] for t in window)),
            start_time=window[0]["start_time"],
            end_time=window[-1]["end_time"],
            word_count=len(window),
        ))
    return chunks


def embed_texts(texts: list[str]) -> np.ndarray:
    return get_sbert().encode(texts, show_progress_bar=False, convert_to_numpy=True).astype(np.float32)


def build_corpus_index(transcript: TranscriptData) -> CorpusIndex:
    console.print("[cyan]→[/cyan] Stage 3B: Chunking and embedding transcript …")
    chunks = chunk_transcript(transcript.turns)
    if not chunks:
        raise ValueError("No chunks produced — transcript may be empty")
    embeddings = embed_texts([c.text for c in chunks])
    console.print(
        f"[green]✓[/green] Built corpus index — "
        f"[bold]{len(chunks)}[/bold] chunks, dim=[bold]{embeddings.shape[1]}[/bold]"
    )
    return CorpusIndex(chunks=chunks, embeddings=embeddings)
