"""State machine for Cairos Dungeon scenario farming (Necropolis Abyss Hard etc.).

Core loop:
  - Detect "Repeat Battle Results" screen (replay btn + sell btn visible)
  - Tap Sell Selected -> handle confirm popup
  - Tap Replay -> next batch starts
  - Otherwise: wait (likely in-battle or transition)

Edge cases handled later:
  - Energy depleted popup
  - Network retry
  - Daily mission popup
  - Level up popup
"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from pathlib import Path

from . import config
from .adb_client import AdbClient
from .telegram_notify import send_text, send_photo
from .vision import find

log = logging.getLogger("sw-bot.scenario")


def _setup_logging() -> None:
    log_file = config.LOGS_DIR / f"scenario_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def _save_unknown(client: AdbClient, frame, tag: str = "unknown") -> Path:
    """Save the current frame for debugging unknown states."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = config.DEBUG_DIR / f"{tag}_{ts}.png"
    import cv2
    cv2.imwrite(str(path), frame)
    return path


def run(max_runs: int = 0, sell: bool = True) -> int:
    """
    Run the scenario farming loop.

    max_runs: 0 = infinite (until energy out / break / Ctrl+C)
    sell:    True = tap Sell Selected before Replay each batch
    """
    _setup_logging()
    log.info("=== scenario start === max_runs=%d sell=%s", max_runs, sell)
    send_text(f"sw-bot scenario started (max={max_runs}, sell={sell})")

    client = AdbClient()
    client.connect()
    log.info("ADB connected: %s", client.device.serial if client.device else "?")

    runs = 0
    consecutive_unknown = 0
    UNKNOWN_LIMIT = 30  # ~30 * 1s = 30s of nothing matched

    try:
        while True:
            frame = client.screencap()

            # --- State: results screen (both buttons visible) ---
            replay = find(frame, "replay_btn", category="scenario")
            sell_btn = find(frame, "sell_selected_btn", category="scenario")

            if replay and sell_btn:
                consecutive_unknown = 0
                runs += 1
                log.info("[run %d] results screen detected", runs)

                if sell:
                    log.info("  tap Sell Selected at (%d,%d) conf=%.3f",
                             sell_btn.x, sell_btn.y, sell_btn.confidence)
                    client.tap(sell_btn.x, sell_btn.y)
                    AdbClient.humanize_delay(800, 1500)

                    # TODO: handle "Sell N runes?" confirm popup
                    # For now wait for it to settle
                    AdbClient.humanize_delay(1000, 1800)

                log.info("  tap Replay at (%d,%d) conf=%.3f",
                         replay.x, replay.y, replay.confidence)
                client.tap(replay.x, replay.y)
                AdbClient.humanize_delay(2000, 3500)

                if max_runs and runs >= max_runs:
                    log.info("max_runs %d reached, stopping", max_runs)
                    send_text(f"sw-bot scenario done: {runs} batches")
                    return 0

                # Periodic break
                if runs % config.BREAK_AFTER_RUNS == 0:
                    nap = random.uniform(
                        config.BREAK_DURATION_MIN * 60,
                        config.BREAK_DURATION_MAX * 60,
                    )
                    log.info("break for %.1fs after %d runs", nap, runs)
                    send_text(f"sw-bot break {int(nap)}s after {runs} runs")
                    time.sleep(nap)
                continue

            # --- Unknown state: maybe in-battle, transition, or popup ---
            consecutive_unknown += 1
            if consecutive_unknown >= UNKNOWN_LIMIT:
                path = _save_unknown(client, frame, tag="unknown")
                log.warning("stuck on unknown state, saved %s", path)
                send_photo(path, caption=f"sw-bot stuck (run {runs}). Inspect.")
                consecutive_unknown = 0  # reset so we keep saving snapshots periodically

            time.sleep(1.0)

    except KeyboardInterrupt:
        log.info("interrupted by user after %d runs", runs)
        send_text(f"sw-bot scenario interrupted: {runs} batches done")
        return 130
    except Exception as e:
        log.exception("crash: %s", e)
        send_text(f"sw-bot scenario CRASHED: {e}")
        return 1
