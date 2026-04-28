"""Load config from .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _get(key: str, default: str | None = None, required: bool = False) -> str:
    val = os.getenv(key, default)
    if required and not val:
        raise RuntimeError(f"Missing required env: {key}")
    return val  # type: ignore[return-value]


def _get_int(key: str, default: int) -> int:
    return int(_get(key, str(default)))


def _get_float(key: str, default: float) -> float:
    return float(_get(key, str(default)))


# ADB
ADB_HOST = _get("ADB_HOST", "127.0.0.1")
ADB_PORT = _get_int("ADB_PORT", 5555)

# Telegram
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID")

# Vision / behavior
MATCH_THRESHOLD = _get_float("MATCH_THRESHOLD", 0.85)
TAP_JITTER_PX = _get_int("TAP_JITTER_PX", 5)
DELAY_MIN_MS = _get_int("DELAY_MIN_MS", 250)
DELAY_MAX_MS = _get_int("DELAY_MAX_MS", 900)
BREAK_AFTER_RUNS = _get_int("BREAK_AFTER_RUNS", 40)
BREAK_DURATION_MIN = _get_int("BREAK_DURATION_MIN", 5)
BREAK_DURATION_MAX = _get_int("BREAK_DURATION_MAX", 15)

# Paths
TEMPLATES_DIR = ROOT / "templates"
DEBUG_DIR = ROOT / "debug"
LOGS_DIR = ROOT / "logs"
DEBUG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
