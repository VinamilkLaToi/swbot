"""Debug: tap Sell Selected once, screencap rapidly to catch any transient
state (selection mode might be brief)."""
import time
import cv2
from src.adb_client import AdbClient
from src import config

OUT = config.DEBUG_DIR / "walk"
OUT.mkdir(parents=True, exist_ok=True)

c = AdbClient()
c.connect()

f0 = c.screencap()
cv2.imwrite(str(OUT / "dbg_before.png"), f0)
print(f"before saved ({f0.shape[1]}x{f0.shape[0]})")

print("tap (900, 505)")
c.tap(900, 505)

for i in range(8):
    time.sleep(0.25)
    f = c.screencap()
    out = OUT / f"dbg_after_{i:02d}.png"
    cv2.imwrite(str(out), f)
    print(f"  +{(i+1)*0.25:.2f}s -> {out.name}")

print("done")
