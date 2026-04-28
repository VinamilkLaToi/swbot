"""Send alert/screenshot to Telegram via bot @advswbot."""
from __future__ import annotations

from pathlib import Path

import requests

from . import config

API_BASE = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def send_text(text: str) -> bool:
    if not config.TELEGRAM_CHAT_ID:
        return False
    try:
        r = requests.post(
            f"{API_BASE}/sendMessage",
            data={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        return r.ok
    except Exception:
        return False


def send_photo(image_path: str | Path, caption: str = "") -> bool:
    if not config.TELEGRAM_CHAT_ID:
        return False
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                f"{API_BASE}/sendPhoto",
                data={"chat_id": config.TELEGRAM_CHAT_ID, "caption": caption},
                files={"photo": f},
                timeout=30,
            )
        return r.ok
    except Exception:
        return False
