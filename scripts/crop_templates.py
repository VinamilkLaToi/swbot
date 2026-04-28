# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python", "numpy"]
# ///
"""Crop button templates from state_30done.png and verify by re-matching."""
import cv2
import numpy as np
from pathlib import Path

SRC = "/tmp/swbot-tg/snapshots/state_30done.png"
OUT_DIR = Path("/Users/toiladung/alfred/skills/games/sw-bot/templates/scenario")
OUT_DIR.mkdir(parents=True, exist_ok=True)

img = cv2.imread(SRC)
H, W = img.shape[:2]
print(f"image: {W}x{H}")

crops = {
    "repeat_results_title": (320, 95, 640, 125),
    "replay_btn":           (412, 482, 605, 528),
    "sell_selected_btn":    (845, 482, 955, 528),
    "energy_label":         (715, 56, 815, 85),
}

for name, (x1, y1, x2, y2) in crops.items():
    crop = img[y1:y2, x1:x2]
    out = OUT_DIR / f"{name}.png"
    cv2.imwrite(str(out), crop)
    print(f"saved: {out.name}  size={crop.shape[1]}x{crop.shape[0]}")

print("\n--- match verification ---")
for name in crops:
    tpl = cv2.imread(str(OUT_DIR / f"{name}.png"))
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    h, w = tpl.shape[:2]
    cx, cy = max_loc[0] + w // 2, max_loc[1] + h // 2
    print(f"{name:30s} conf={max_val:.4f}  center=({cx},{cy})")

viz = img.copy()
for name, (x1, y1, x2, y2) in crops.items():
    cv2.rectangle(viz, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(viz, name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
cv2.imwrite("/tmp/swbot-tg/snapshots/state_30done_annotated.png", viz)
print("\nannotated: /tmp/swbot-tg/snapshots/state_30done_annotated.png")
