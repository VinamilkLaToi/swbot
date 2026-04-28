"""Debug: try different tap methods to find one that works on LDPlayer.

Targets the close-X button at top-right of Repeat Battle dialog (~885, 50)
which should obviously change state if tap registers.
"""
import time
import cv2
from src.adb_client import AdbClient
from src import config

OUT = config.DEBUG_DIR / "walk"
OUT.mkdir(parents=True, exist_ok=True)

c = AdbClient()
c.connect()
d = c.device

X, Y = 885, 50

print(f"target: close X at ({X},{Y})")

# Snap before
cv2.imwrite(str(OUT / "tap_before.png"), c.screencap())

# Method 1: input tap
print("[m1] input tap")
d.shell(f"input tap {X} {Y}")
time.sleep(1.5)
cv2.imwrite(str(OUT / "tap_m1_input_tap.png"), c.screencap())

# Method 2: input touchscreen tap
print("[m2] input touchscreen tap")
d.shell(f"input touchscreen tap {X} {Y}")
time.sleep(1.5)
cv2.imwrite(str(OUT / "tap_m2_touchscreen.png"), c.screencap())

# Method 3: swipe with same start/end (long tap-like)
print("[m3] input swipe (same point, 100ms)")
d.shell(f"input swipe {X} {Y} {X} {Y} 100")
time.sleep(1.5)
cv2.imwrite(str(OUT / "tap_m3_swipe.png"), c.screencap())

# Method 4: cmd input tap (newer android)
print("[m4] cmd input tap")
d.shell(f"cmd input tap {X} {Y}")
time.sleep(1.5)
cv2.imwrite(str(OUT / "tap_m4_cmd_input.png"), c.screencap())

# Method 5: adb getevent device + sendevent? skip — too low-level

print("done")
