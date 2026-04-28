# Enable OpenSSH Server on Windows + add Claude's public key for swbot.
# Run from PowerShell admin:
#   iwr -useb https://raw.githubusercontent.com/VinamilkLaToi/swbot/main/setup-ssh-server.ps1 | iex

$ErrorActionPreference = "Stop"
$CLAUDE_PUBKEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ4/kVd0m+AzrR6wSb2D1RoMmIesccmCb9xh7fyhpgEB claude-swbot"

function Info($msg) { Write-Host "[ssh] $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "[ok ] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "[warn] $msg" -ForegroundColor Yellow }

# --- 1. Install OpenSSH Server capability ---
Info "Checking OpenSSH Server..."
$cap = Get-WindowsCapability -Online -Name OpenSSH.Server*
if ($cap.State -ne "Installed") {
    Info "Installing OpenSSH.Server..."
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
    Ok "OpenSSH Server installed"
} else {
    Ok "OpenSSH Server already installed"
}

# --- 2. Start service + auto-start on boot ---
Info "Starting sshd service..."
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
Ok "sshd running, set to auto-start"

# --- 3. Firewall rule (port 22 inbound) ---
Info "Configuring firewall..."
if (-not (Get-NetFirewallRule -Name "sshd" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name sshd -DisplayName "OpenSSH Server (sshd)" `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
    Ok "Firewall rule added"
} else {
    Ok "Firewall rule already exists"
}

# --- 4. Detect if user is admin ---
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# --- 5. Add Claude pubkey ---
# For admin users: keys go in C:\ProgramData\ssh\administrators_authorized_keys
# For standard users: keys go in $HOME\.ssh\authorized_keys
function Add-PubKey($file) {
    $dir = Split-Path $file -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    if (Test-Path $file) {
        $existing = Get-Content $file -ErrorAction SilentlyContinue
        if ($existing -match [regex]::Escape($CLAUDE_PUBKEY)) {
            Ok "Key already in $file"
            return
        }
    }
    Add-Content -Path $file -Value $CLAUDE_PUBKEY
    Ok "Key added to $file"
}

if ($isAdmin) {
    Info "User is in Administrators group — using administrators_authorized_keys"
    $adminKeys = "C:\ProgramData\ssh\administrators_authorized_keys"
    Add-PubKey $adminKeys
    # Lock down permissions (required by sshd)
    icacls $adminKeys /inheritance:r /grant "Administrators:F" /grant "SYSTEM:F" | Out-Null
    Ok "Permissions set on $adminKeys"
} else {
    Info "Standard user — using ~/.ssh/authorized_keys"
    $userKeys = "$env:USERPROFILE\.ssh\authorized_keys"
    Add-PubKey $userKeys
}

# --- 6. Default shell to PowerShell (nicer than cmd) ---
Info "Setting default ssh shell to PowerShell..."
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell `
    -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -PropertyType String -Force | Out-Null
Ok "Default shell: PowerShell"

# --- 7. Print connection info ---
Write-Host ""
Write-Host "================ CONNECTION INFO ================" -ForegroundColor Cyan
$tsExe = "C:\Program Files\Tailscale\tailscale.exe"
if (Test-Path $tsExe) {
    $tsStatus = & $tsExe status 2>$null
    Write-Host "Tailscale status:"
    Write-Host $tsStatus
}
Write-Host ""
Write-Host "Username: $env:USERNAME"
Write-Host "Hostname: $env:COMPUTERNAME"
Write-Host ""
Write-Host "From Mac:"
Write-Host "  ssh -i ~/.ssh/id_ed25519_swbot ""$env:USERNAME@<tailscale-ip>"""
Write-Host "================================================" -ForegroundColor Cyan
