import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_dir: Path | None = None) -> None:
    """Configure root logger — call once at startup."""
    target_dir = log_dir or Path("/tmp/app_data/logs")
    target_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)-35s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    root.setLevel(log_level)

    console = logging.StreamHandler(sys.stdout)
    console.stream = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1, closefd=False)
    console.setFormatter(formatter)
    root.addHandler(console)

    log_file = target_dir / "pipeline.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
