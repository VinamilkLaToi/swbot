"""Walk through the scenario flow step-by-step, saving screencaps at every
state for template extraction.

Each step:  before-screencap -> tap (or noop) -> wait -> after-screencap.

Steps controlled by env STEP=1..N so we can pause + inspect between phases.

Outputs to debug/walk/state_<NN>_<label>.png and prints findings.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

from src import config
from src.adb_client import AdbClient
from src.vision import find


WALK_DIR = config.DEBUG_DIR / "walk"
WALK_DIR.mkdir(parents=True, exist_ok=True)


def snap(client: AdbClient, label: str):
    frame = client.screencap()
    out = WALK_DIR / f"{label}.png"
    cv2.imwrite(str(out), frame)
    print(f"  saved: {out}  ({frame.shape[1]}x{frame.shape[0]})")
    return frame, out


def report(frame, names):
    for n in names:
        m = find(frame, n, category="scenario")
        tag = f"OK conf={m.confidence:.3f} @({m.x},{m.y})" if m else "MISS"
        print(f"    {n:25s} {tag}")


def main() -> int:
    step = int(os.environ.get("STEP", "1"))
    print(f"=== walker step {step} ===")
    client = AdbClient()
    client.connect()

    if step == 1:
        # Expect: Results screen
        print("[1] snap initial state")
        frame, _ = snap(client, "01_initial")
        report(frame, ["replay_btn", "sell_selected_btn", "repeat_results_title"])

        sb = find(frame, "sell_selected_btn", category="scenario")
        if not sb:
            print("ERROR: not at results screen — abort")
            return 1
        print(f"[1] tap Sell Selected at ({sb.x},{sb.y})")
        client.tap(sb.x, sb.y)
        time.sleep(2.0)

        print("[1] snap after first Sell Selected tap")
        frame2, _ = snap(client, "02_after_sell1")
        report(frame2, ["replay_btn", "sell_selected_btn", "repeat_results_title"])
        return 0

    if step == 2:
        # Expect: Selection mode. Sell Selected has moved.
        print("[2] snap selection mode (no tap yet)")
        frame, _ = snap(client, "03_selection_mode")
        report(frame, ["replay_btn", "sell_selected_btn", "repeat_results_title"])

        sb = find(frame, "sell_selected_btn", category="scenario")
        if not sb:
            print("ERROR: cannot find Sell Selected in selection mode — abort")
            return 1
        print(f"[2] tap Sell Selected #2 at ({sb.x},{sb.y})")
        client.tap(sb.x, sb.y)
        time.sleep(2.0)

        print("[2] snap modal (could be confirm-sell or nothing-to-sell)")
        frame2, _ = snap(client, "04_modal")
        return 0

    if step == 3:
        # Modal is on screen. We need to tap Yes / OK. Use hardcoded coord
        # guess based on Telegram refs scaled to 960x540:
        #   confirm_sell.Yes  ~ (400, 315)  on 960x540
        #   nothing_to_sell.OK ~ (480, 270) on 960x540
        # Both modals overlap that center region. Tap (480, 290) to be safe.
        print("[3] snap modal before tapping")
        frame, _ = snap(client, "05_modal_before_tap")

        tap_x, tap_y = 480, 290
        print(f"[3] tap modal-confirm at ({tap_x},{tap_y})")
        client.tap(tap_x, tap_y)
        time.sleep(2.0)

        print("[3] snap after modal-confirm")
        frame2, _ = snap(client, "06_after_modal")
        report(frame2, ["replay_btn", "sell_selected_btn", "repeat_results_title"])
        return 0

    if step == 4:
        # Expect back at Results screen, Sell Selected at original (900,505).
        # Tap Replay to go to squad screen.
        print("[4] snap pre-replay")
        frame, _ = snap(client, "07_pre_replay")
        report(frame, ["replay_btn", "sell_selected_btn", "repeat_results_title"])

        rp = find(frame, "replay_btn", category="scenario")
        if not rp:
            print("ERROR: cannot find Replay — abort")
            return 1
        print(f"[4] tap Replay at ({rp.x},{rp.y})")
        client.tap(rp.x, rp.y)
        time.sleep(3.0)

        print("[4] snap squad screen")
        frame2, _ = snap(client, "08_squad_screen")
        return 0

    print(f"unknown step {step}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
