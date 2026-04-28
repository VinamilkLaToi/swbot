# sw-bot Windows setup script
# Run from PowerShell (admin recommended for winget):
#   iwr -useb https://raw.githubusercontent.com/VinamilkLaToi/swbot/main/setup.ps1 | iex

$ErrorActionPreference = "Stop"

function Info($msg)  { Write-Host "[setup] $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "[ ok ] $msg"  -ForegroundColor Green }
function Warn($msg)  { Write-Host "[warn] $msg"  -ForegroundColor Yellow }
function Fail($msg)  { Write-Host "[fail] $msg"  -ForegroundColor Red; throw $msg }

# --- 1. winget check ---
Info "Checking winget..."
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Fail "winget not found. Update Windows or install App Installer from Microsoft Store."
}
Ok "winget available"

# --- 2. Python 3.11 ---
Info "Installing Python 3.11 (skip if already installed)..."
$pythonOk = $false
try {
    $ver = & python --version 2>&1
    if ($ver -match "Python 3\.(11|12)") {
        Ok "Python found: $ver"
        $pythonOk = $true
    }
} catch {}
if (-not $pythonOk) {
    winget install -e --id Python.Python.3.11 --source winget --silent --accept-source-agreements --accept-package-agreements
    Ok "Python installed (you may need to restart PowerShell for PATH)"
}

# --- 3. Git ---
Info "Installing Git (skip if already installed)..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    winget install -e --id Git.Git --source winget --silent --accept-source-agreements --accept-package-agreements
    Ok "Git installed"
} else {
    Ok "Git found: $(git --version)"
}

# Refresh PATH for current session from registry
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Locate executables explicitly in case PATH didn't propagate yet
function Find-Exe($name, $candidates) {
    if (Get-Command $name -ErrorAction SilentlyContinue) {
        return (Get-Command $name).Source
    }
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$gitExe = Find-Exe "git" @(
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files (x86)\Git\cmd\git.exe"
)
if (-not $gitExe) { Fail "Git not found after install. Restart PowerShell and re-run." }
Ok "git: $gitExe"

$pythonExe = Find-Exe "python" @(
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python312\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Program Files\Python312\python.exe"
)
if (-not $pythonExe) { Fail "Python not found after install. Restart PowerShell and re-run." }
Ok "python: $pythonExe"

# --- 4. Clone repo ---
$REPO_DIR = "C:\swbot"
Info "Setting up repo at $REPO_DIR..."
if (Test-Path "$REPO_DIR\.git") {
    Info "Repo exists — pulling latest"
    Push-Location $REPO_DIR
    & $gitExe pull
    Pop-Location
} else {
    & $gitExe clone https://github.com/VinamilkLaToi/swbot.git $REPO_DIR
}
Ok "Repo ready"

# --- 5. venv + deps ---
Push-Location $REPO_DIR
Info "Creating venv..."
if (-not (Test-Path ".venv")) {
    & $pythonExe -m venv .venv
}
Ok "venv ready"

Info "Installing Python dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
Ok "Dependencies installed"

# --- 6. .env scaffold ---
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    # Pre-fill chat_id (token user must add manually for security)
    (Get-Content .env) -replace "TELEGRAM_CHAT_ID=", "TELEGRAM_CHAT_ID=7680654700" | Set-Content .env
    Warn ".env created — open it and fill TELEGRAM_BOT_TOKEN:  notepad .env"
} else {
    Ok ".env already exists (not overwritten)"
}

Pop-Location

# --- 7. Final guide ---
Write-Host ""
Write-Host "================ NEXT STEPS ================" -ForegroundColor Cyan
Write-Host "1. Install LDPlayer 9 manually: https://www.ldplayer.net/" -ForegroundColor White
Write-Host "2. In LDPlayer: Settings -> Other -> ADB debugging -> Local connection -> Save -> restart" -ForegroundColor White
Write-Host "3. Open Summoners War in LDPlayer, login phụ acc" -ForegroundColor White
Write-Host "4. Fill TELEGRAM_BOT_TOKEN in $REPO_DIR\.env  (notepad $REPO_DIR\.env)" -ForegroundColor White
Write-Host "5. Smoke test:" -ForegroundColor White
Write-Host "   cd $REPO_DIR" -ForegroundColor Yellow
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "   python -m src.main smoke" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
