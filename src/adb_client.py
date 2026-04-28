"""ADB client wrapper: screencap + tap with humanize jitter/delay."""
from __future__ import annotations

import io
import random
import time
from dataclasses import dataclass

import numpy as np
from adbutils import adb, AdbDevice
from PIL import Image

from . import config


@dataclass
class Tap:
    x: int
    y: int


class AdbClient:
    def __init__(self, host: str = config.ADB_HOST, port: int = config.ADB_PORT):
        self.host = host
        self.port = port
        self.device: AdbDevice | None = None

    def connect(self) -> AdbDevice:
        adb.connect(f"{self.host}:{self.port}")
        devices = adb.device_list()
        if not devices:
            raise RuntimeError(
                f"No ADB device found at {self.host}:{self.port}. "
                "Is LDPlayer running with ADB enabled?"
            )
        # Prefer matching host:port if multiple devices
        for d in devices:
            if f"{self.host}:{self.port}" in d.serial:
                self.device = d
                break
        else:
            self.device = devices[0]
        return self.device

    def _ensure(self) -> AdbDevice:
        if self.device is None:
            self.connect()
        assert self.device is not None
        return self.device

    def screencap(self) -> np.ndarray:
        """Return BGR ndarray of current screen."""
        d = self._ensure()
        png_bytes = d.shell("screencap -p", encoding=None)
        # Some devices add CRLF — strip if needed (legacy)
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        rgb = np.array(img)
        bgr = rgb[:, :, ::-1].copy()  # RGB → BGR for cv2
        return bgr

    def tap(self, x: int, y: int, jitter: int = config.TAP_JITTER_PX) -> Tap:
        """Tap with random jitter ± jitter px."""
        jx = x + random.randint(-jitter, jitter)
        jy = y + random.randint(-jitter, jitter)
        d = self._ensure()
        d.shell(f"input tap {jx} {jy}")
        return Tap(jx, jy)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        d = self._ensure()
        d.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    @staticmethod
    def humanize_delay(
        min_ms: int = config.DELAY_MIN_MS, max_ms: int = config.DELAY_MAX_MS
    ) -> None:
        time.sleep(random.uniform(min_ms, max_ms) / 1000.0)
