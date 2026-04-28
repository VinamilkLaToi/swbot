"""Entry point — smoke test for now."""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

import cv2

from . import config
from .adb_client import AdbClient
from .telegram_notify import send_text


def cmd_smoke() -> int:
    """Verify ADB connect + screencap + Telegram works."""
    print("[smoke] Connecting ADB...")
    client = AdbClient()
    dev = client.connect()
    print(f"[smoke] Device: {dev.serial}")

    print("[smoke] Capturing screen...")
    frame = client.screencap()
    h, w = frame.shape[:2]
    print(f"[smoke] Frame size: {w}x{h}")

    out = config.DEBUG_DIR / f"smoke_{datetime.now():%Y%m%d_%H%M%S}.png"
    cv2.imwrite(str(out), frame)
    print(f"[smoke] Saved: {out}")

    print("[smoke] Sending Telegram alert...")
    ok = send_text(f"sw-bot smoke test OK\nDevice: {dev.serial}\nFrame: {w}x{h}")
    print(f"[smoke] Telegram: {'OK' if ok else 'FAIL (check TELEGRAM_CHAT_ID)'}")

    print("[smoke] All good. Skeleton ready.")
    return 0


def cmd_scenario(args: argparse.Namespace) -> int:
    from .state_machine import run as run_scenario
    return run_scenario(max_runs=args.max_runs, sell=not args.no_sell)


def cmd_db10(args: argparse.Namespace) -> int:
    print("[db10] Not implemented yet — Phase 4.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="sw-bot")
    sub = p.add_subparsers(dest="task", required=True)

    sub.add_parser("smoke", help="Smoke test ADB + screencap + Telegram")

    sc = sub.add_parser("scenario", help="Farm hầm chỉ định (Cairos Dungeon)")
    sc.add_argument("--max-runs", type=int, default=0, help="0 = infinite")
    sc.add_argument("--no-sell", action="store_true", help="Skip Sell Selected step")

    db = sub.add_parser("db10", help="Farm DB10 with auto sell")
    db.add_argument("--sell-every", type=int, default=30)
    db.add_argument("--max-runs", type=int, default=0, help="0 = infinite")

    args = p.parse_args()

    if args.task == "smoke":
        return cmd_smoke()
    if args.task == "scenario":
        return cmd_scenario(args)
    if args.task == "db10":
        return cmd_db10(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
