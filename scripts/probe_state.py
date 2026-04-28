"""Probe current LDPlayer state: screencap once, match scenario templates,
report confidences, save annotated screenshot to debug/ + send to Telegram.

Usage (from repo root):
    .\\.venv\\Scripts\\python.exe -m scripts.probe_state
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2

from src import config
from src.adb_client import AdbClient
from src.telegram_notify import send_photo
from src.vision import find


TEMPLATES = [
    "replay_btn",
    "sell_selected_btn",
    "repeat_results_title",
    "energy_label",
]


def main() -> int:
    print("[probe] connecting ADB...")
    client = AdbClient()
    client.connect()
    print(f"[probe] device: {client.device.serial if client.device else '?'}")

    print("[probe] screencap...")
    frame = client.screencap()
    h, w = frame.shape[:2]
    print(f"[probe] frame: {w}x{h}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw = config.DEBUG_DIR / f"probe_{ts}.png"
    cv2.imwrite(str(raw), frame)
    print(f"[probe] saved raw: {raw}")

    viz = frame.copy()
    summary_lines = [f"probe {ts}  {w}x{h}"]
    for name in TEMPLATES:
        m = find(frame, name, category="scenario")
        if m:
            line = f"  {name:25s} OK conf={m.confidence:.3f} @({m.x},{m.y})"
            cv2.drawMarker(viz, (m.x, m.y), (0, 255, 0),
                           markerType=cv2.MARKER_CROSS, markerSize=24, thickness=2)
            cv2.putText(viz, f"{name} {m.confidence:.2f}", (m.x + 12, m.y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        else:
            line = f"  {name:25s} MISS (below threshold)"
        print(line)
        summary_lines.append(line)

    annotated = config.DEBUG_DIR / f"probe_{ts}_annotated.png"
    cv2.imwrite(str(annotated), viz)
    print(f"[probe] saved annotated: {annotated}")

    caption = "\n".join(summary_lines)
    ok = send_photo(annotated, caption=caption)
    print(f"[probe] telegram: {'OK' if ok else 'FAIL'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
