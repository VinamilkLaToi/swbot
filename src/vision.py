"""Template matching wrapper using OpenCV."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from . import config


@dataclass
class Match:
    name: str
    confidence: float
    x: int  # center x
    y: int  # center y
    w: int
    h: int

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)


@lru_cache(maxsize=128)
def _load_template(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Template not found or invalid: {path}")
    return img


def find(
    frame: np.ndarray,
    template_name: str,
    category: str = "anchors",
    threshold: float = config.MATCH_THRESHOLD,
) -> Match | None:
    """
    Find single best match for template_name in frame.
    template_name: filename without .png (e.g. "replay_btn")
    category: subfolder in templates/ (anchors, scenario, db10)
    """
    path = config.TEMPLATES_DIR / category / f"{template_name}.png"
    template = _load_template(str(path))
    h, w = template.shape[:2]

    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return Match(name=template_name, confidence=float(max_val), x=cx, y=cy, w=w, h=h)


def find_first(
    frame: np.ndarray,
    candidates: list[tuple[str, str]],  # [(name, category), ...]
    threshold: float = config.MATCH_THRESHOLD,
) -> Match | None:
    """Try templates in order, return first match above threshold."""
    for name, category in candidates:
        m = find(frame, name, category, threshold)
        if m:
            return m
    return None
