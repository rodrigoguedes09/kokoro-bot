"""Small helper utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    """Create the directory (and parents) if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Any, path: Path) -> Path:
    """Serialise *data* as pretty-printed JSON and write to *path*."""
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    """Clamp *value* between *low* and *high*."""
    return max(low, min(high, value))


def sentiment_emoji(score: float) -> str:
    """Return an emoji that matches the sentiment score."""
    if score >= 0.3:
        return "😊"
    if score >= 0.0:
        return "😐"
    if score >= -0.3:
        return "😟"
    return "😠"


def format_score(score: float) -> str:
    """Format a sentiment score as a signed string with 2 decimals."""
    return f"{score:+.2f}"
