"""Cairos Dungeon scenario farming — proper FSM.

Observable states (via screen):
  RESULTS               → tap Sell Selected → SELECTION
  SELECTION             → tap Sell Selected (new pos) → MODAL_*
  MODAL_CONFIRM_SELL    → tap Yes → RESULTS (post-sell)
  MODAL_NOTHING_TO_SELL → tap OK → SELECTION → tap Cancel → RESULTS
  RESULTS (post-sell)   → tap Replay → SQUAD
  SQUAD                 → tap "Repeat Battle 9x30" → BATTLE/loading
  BATTLE/UNKNOWN        → wait, poll until RESULTS

Templates we have: replay_btn, sell_selected_btn, repeat_results_title, energy_label.
For Yes/No/OK/RepeatBattle/Cancel we use a yellow-button pixel heuristic at
estimated coords (refined after first real run).
"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from . import config
from .adb_client import AdbClient
from .telegram_notify import send_text, send_photo
from .vision import find

log = logging.getLogger("sw-bot.scenario")


class State(Enum):
    UNKNOWN = "unknown"
    RESULTS = "results"
    SELECTION = "selection"
    MODAL_CONFIRM_SELL = "modal_confirm_sell"
    MODAL_NOTHING_TO_SELL = "modal_nothing_to_sell"
    SQUAD = "squad"


# Estimated coords on 960x540 ADB native — refine after first capture.
COORDS = {
    "yes_btn": (401, 315),               # confirm sell modal: Yes
    "no_btn": (566, 315),                # confirm sell modal: No
    "ok_btn": (503, 351),                # nothing-to-sell modal: OK
    "repeat_battle_btn": (839, 406),     # squad screen: 9x30 Repeat Battle
    "cancel_btn": (905, 505),            # selection mode: Cancel (right-most)
}

# Sell Selected x-position discriminates Results vs Selection mode.
# Results: ~900. Selection: ~770 (Sell shifts left when Cancel appears).
SELL_X_RESULTS_MIN = 850
SELL_X_SELECTION_MAX = 820


def _is_yellow_button_at(frame: np.ndarray, cx: int, cy: int, radius: int = 18) -> bool:
    """Heuristic: gold/yellow button present near (cx, cy)?

    Game's gold buttons are roughly BGR(40-130, 130-230, 180-255).
    """
    h, w = frame.shape[:2]
    x0, x1 = max(0, cx - radius), min(w, cx + radius)
    y0, y1 = max(0, cy - radius), min(h, cy + radius)
    patch = frame[y0:y1, x0:x1]
    if patch.size == 0:
        return False
    b, g, r = patch[..., 0], patch[..., 1], patch[..., 2]
    mask = (b > 30) & (b < 140) & (g > 120) & (g < 235) & (r > 170) & (r < 255)
    return (mask.sum() / mask.size) > 0.25


def _setup_logging() -> None:
    log_file = config.LOGS_DIR / f"scenario_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def _save_debug(frame: np.ndarray, tag: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = config.DEBUG_DIR / f"{tag}_{ts}.png"
    cv2.imwrite(str(path), frame)
    return path


def detect_state(frame: np.ndarray) -> tuple[State, dict]:
    """Return (State, ctx) where ctx may carry positions for downstream actions."""
    ctx: dict = {}

    yes_here = _is_yellow_button_at(frame, *COORDS["yes_btn"])
    no_here = _is_yellow_button_at(frame, *COORDS["no_btn"])
    ok_here = _is_yellow_button_at(frame, *COORDS["ok_btn"])
    rb_here = _is_yellow_button_at(frame, *COORDS["repeat_battle_btn"])

    # 1) Modal — overlays everything
    if yes_here and no_here:
        return State.MODAL_CONFIRM_SELL, ctx
    if ok_here and not yes_here:
        return State.MODAL_NOTHING_TO_SELL, ctx

    replay = find(frame, "replay_btn", category="scenario")

    # 2) Squad screen — Repeat Battle button on right, no replay_btn template match
    if rb_here and replay is None:
        return State.SQUAD, ctx

    # 3) Results vs Selection
    sell = find(frame, "sell_selected_btn", category="scenario")
    if replay and sell:
        ctx["sell"] = sell
        ctx["replay"] = replay
        if sell.x <= SELL_X_SELECTION_MAX:
            return State.SELECTION, ctx
        if sell.x >= SELL_X_RESULTS_MIN:
            return State.RESULTS, ctx
        # Ambiguous middle — bias toward RESULTS (safer)
        return State.RESULTS, ctx

    return State.UNKNOWN, ctx


def run(max_runs: int = 0, sell: bool = True) -> int:
    _setup_logging()
    log.info("=== scenario start === max_runs=%d sell=%s", max_runs, sell)
    send_text(f"sw-bot scenario started (max={max_runs}, sell={sell})")

    client = AdbClient()
    client.connect()
    log.info("ADB: %s", client.device.serial if client.device else "?")

    runs = 0
    last_state: State | None = None
    same_state_count = 0
    STUCK_LIMIT = 30           # ~30 polls in same state → save + alert
    sold_this_cycle = False

    try:
        while True:
            frame = client.screencap()
            state, ctx = detect_state(frame)

            if state == last_state:
                same_state_count += 1
            else:
                log.info("state: %s -> %s",
                         last_state.value if last_state else "init", state.value)
                same_state_count = 0
                last_state = state

            if same_state_count >= STUCK_LIMIT:
                path = _save_debug(frame, f"stuck_{state.value}")
                log.warning("stuck in %s for %d polls — saved %s",
                            state.value, same_state_count, path)
                send_photo(path, caption=f"sw-bot stuck in {state.value} (run {runs})")
                same_state_count = 0

            # ---- Action per state ----
            if state == State.RESULTS:
                if sell and not sold_this_cycle:
                    sb = ctx["sell"]
                    log.info("  RESULTS → tap Sell Selected (%d,%d) conf=%.3f",
                             sb.x, sb.y, sb.confidence)
                    client.tap(sb.x, sb.y)
                    AdbClient.humanize_delay(1200, 1800)
                else:
                    rp = ctx["replay"]
                    log.info("  RESULTS → tap Replay (%d,%d) conf=%.3f",
                             rp.x, rp.y, rp.confidence)
                    client.tap(rp.x, rp.y)
                    AdbClient.humanize_delay(2500, 3500)
                    runs += 1
                    sold_this_cycle = False
                    log.info("  --- run %d / %s ---", runs, max_runs or "inf")
                    if max_runs and runs >= max_runs:
                        log.info("max_runs reached, stopping")
                        send_text(f"sw-bot scenario done: {runs} batches")
                        return 0
                    if runs % config.BREAK_AFTER_RUNS == 0:
                        nap = random.uniform(
                            config.BREAK_DURATION_MIN * 60,
                            config.BREAK_DURATION_MAX * 60,
                        )
                        log.info("  break %.1fs after %d runs", nap, runs)
                        send_text(f"sw-bot break {int(nap)}s after {runs} runs")
                        time.sleep(nap)

            elif state == State.SELECTION:
                sb = ctx["sell"]
                log.info("  SELECTION → tap Sell Selected #2 (%d,%d) conf=%.3f",
                         sb.x, sb.y, sb.confidence)
                client.tap(sb.x, sb.y)
                AdbClient.humanize_delay(1500, 2200)

            elif state == State.MODAL_CONFIRM_SELL:
                x, y = COORDS["yes_btn"]
                log.info("  MODAL_CONFIRM_SELL → tap Yes (%d,%d)", x, y)
                client.tap(x, y)
                AdbClient.humanize_delay(1500, 2000)
                sold_this_cycle = True

            elif state == State.MODAL_NOTHING_TO_SELL:
                x, y = COORDS["ok_btn"]
                log.info("  MODAL_NOTHING_TO_SELL → tap OK (%d,%d)", x, y)
                client.tap(x, y)
                AdbClient.humanize_delay(1000, 1500)
                cx, cy = COORDS["cancel_btn"]
                log.info("  MODAL_NOTHING_TO_SELL → tap Cancel (%d,%d) to exit selection",
                         cx, cy)
                client.tap(cx, cy)
                AdbClient.humanize_delay(1500, 2000)
                sold_this_cycle = True  # nothing to sell counts as done

            elif state == State.SQUAD:
                x, y = COORDS["repeat_battle_btn"]
                log.info("  SQUAD → tap Repeat Battle 9x30 (%d,%d)", x, y)
                client.tap(x, y)
                AdbClient.humanize_delay(3000, 4500)

            else:  # UNKNOWN — likely in-battle / loading
                time.sleep(1.0)

    except KeyboardInterrupt:
        log.info("interrupted by user after %d runs", runs)
        send_text(f"sw-bot scenario interrupted: {runs} batches")
        return 130
    except Exception as e:
        log.exception("crash: %s", e)
        send_text(f"sw-bot scenario CRASHED: {e}")
        return 1
