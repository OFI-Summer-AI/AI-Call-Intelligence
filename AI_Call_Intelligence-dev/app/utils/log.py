from __future__ import annotations

import logging
import sys
from typing import Any, Dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_stage(
    log: logging.Logger,
    *,
    stage: str,
    duration_ms: int,
    step: int,
    total: int,
    detail: Dict[str, Any] | None = None,
) -> None:
    detail_str = ""
    if detail:
        detail_str = " | " + " | ".join(f"{k}={v}" for k, v in detail.items())
    log.info(
        "flow | stage=%-22s | step=%d/%d | %dms%s",
        stage, step, total, duration_ms, detail_str,
    )
