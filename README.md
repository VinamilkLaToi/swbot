# sw-bot

Auto farm Summoners War qua LDPlayer + ADB + OpenCV template matching.

## Mục tiêu

- Farm hầm chỉ định (Faimon Hell, Mt. Siz, ...) — loop replay
- Farm DB10 — loop battle, sau mỗi 30 trận tự sell rune (sell exclusion đã setup trong game)
- Humanize: random delay + jitter pixel → giảm risk ban
- 24/7 trên máy Windows + Telegram alert khi crash / unknown state

## Stack

- Python 3.11
- `adbutils` — control LDPlayer qua ADB
- `opencv-python` — template matching
- `numpy`, `pillow` — image utils
- `requests` — Telegram alert
- `python-dotenv` — config

## Cấu trúc

```
src/
  adb_client.py      # connect LDPlayer, screencap, tap with jitter
  vision.py          # template match wrapper
  state_machine.py   # main loop logic
  telegram_notify.py # alert qua bot @advswbot
  config.py          # load .env
  main.py            # entry: python -m src.main --task scenario|db10
templates/
  anchors/   # các nút common (replay, victory, defeat, network_retry, ...)
  scenario/  # template riêng cho hầm chỉ định
  db10/      # template riêng cho DB10 + sell flow
debug/       # screenshot khi unknown state (auto save)
logs/        # rotating log
```

## Setup máy Windows

Xem `SETUP_WINDOWS.md`.

## Run

```
python -m src.main --task scenario --max-runs 100
python -m src.main --task db10 --sell-every 30
```
