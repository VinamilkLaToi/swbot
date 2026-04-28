# Setup Windows — sw-bot

## 1. Cài Python 3.11

- Tải: https://www.python.org/downloads/release/python-3119/
- Chọn "Windows installer (64-bit)"
- ✅ Tick **"Add python.exe to PATH"** lúc install
- Verify: mở PowerShell mới → `python --version` → phải in `Python 3.11.x`

## 2. Cài Git for Windows

- Tải: https://git-scm.com/download/win
- Cài default settings
- Verify: `git --version`

## 3. Cài LDPlayer

- Tải LDPlayer 9: https://www.ldplayer.net/
- Cài Summoners War từ Play Store trong LDPlayer
- Login acc phụ
- **Bật ADB:** LDPlayer → Settings (icon bánh răng góc phải) → Other settings → ADB debugging → **Local connection** → Save → restart LDPlayer

## 4. Verify ADB connection

LDPlayer có sẵn `adb.exe` trong thư mục cài. Thêm vào PATH hoặc dùng full path:

```powershell
# Default LDPlayer 9 install path:
cd "C:\LDPlayer\LDPlayer9"
.\adb.exe devices
```

Kết quả mong đợi:
```
List of devices attached
emulator-5554   device
```

(Hoặc `127.0.0.1:5555` tuỳ config — note port này, sẽ dùng ở step 6.)

## 5. Clone repo + cài dependencies

```powershell
cd C:\
git clone https://github.com/dungpa91/swbot.git
cd swbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Nếu PowerShell chặn activate script:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## 6. Tạo .env

```powershell
copy .env.example .env
notepad .env
```

Sửa:
- `ADB_PORT` = port từ step 4 (5555 hoặc 5554)
- `TELEGRAM_CHAT_ID` = chat_id của anh (đã gửi)

## 7. Smoke test

LDPlayer phải đang mở, game đang chạy.

```powershell
python -m src.main smoke
```

Kết quả mong đợi:
- In ra device serial, kích thước frame
- Lưu screenshot vào `debug/smoke_*.png`
- Telegram bot @advswbot gửi tin "sw-bot smoke test OK"

Nếu fail → copy lỗi gửi tôi.
