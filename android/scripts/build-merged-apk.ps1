# Build DaddyVPN merged APK via WSL Ubuntu (Compose UI + Amnezia VPN in one package).
param(
    [string]$Distro = "Ubuntu",
    [string]$Abi = "arm64-v8a"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if ($RepoRoot -match '^([A-Za-z]):(.*)$') {
    $WslRepo = "/mnt/$($Matches[1].ToLower())" + ($Matches[2] -replace '\\', '/')
} else {
    $WslRepo = $RepoRoot -replace '\\', '/'
}

Write-Host "=== DaddyVPN merged APK (WSL: $Distro) ===" -ForegroundColor Cyan
Write-Host "Repo (WSL): $WslRepo"

& "$PSScriptRoot\apply-branding.ps1"

$bashCmd = "set -e; cd '$WslRepo'; chmod +x android/scripts/build-merged-apk.sh; ABI='$Abi' bash android/scripts/build-merged-apk.sh"
wsl -d $Distro -e bash -lc $bashCmd

if ($LASTEXITCODE -eq 0) {
    $Apk = Join-Path $RepoRoot "android\daddyvpn-merged-debug.apk"
    if (Test-Path $Apk) {
        Write-Host ""
        Write-Host "APK ready: $Apk" -ForegroundColor Green
        Write-Host "Install on phone: adb install -r `"$Apk`""
    }
}
