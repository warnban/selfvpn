# Sync Compose UI from daddyvpn-app into amnezia-client fork (merged APK).
param(
    [string]$Source = "$PSScriptRoot\..\daddyvpn-app\app\src\main\java\site\daddyvpn\app",
    [string]$Target = "$PSScriptRoot\..\amnezia-client\client\android\src\org\amnezia\vpn"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Target)) {
    Write-Error "amnezia-client not found. Clone: git clone --depth 1 https://github.com/amnezia-vpn/amnezia-client.git android/amnezia-client"
}

# Files safe to auto-sync (package rename only).
# MainViewModel / DaddyVpnActivity / VpnBridge — fork-specific, edit in amnezia-client.
$map = @{
    "ui\theme\Color.kt"      = "ui\theme\Color.kt"
    "ui\theme\Theme.kt"      = "ui\theme\Theme.kt"
    "ui\screens\HomeScreen.kt" = "ui\screens\HomeScreen.kt"
    "ui\screens\KeySheet.kt" = "ui\screens\KeySheet.kt"
    "data\KeyStore.kt"       = "data\KeyStore.kt"
}

function Transform-Content([string]$content) {
    $content `
        -replace 'package site\.daddyvpn\.app', 'package org.amnezia.vpn' `
        -replace 'site\.daddyvpn\.app', 'org.amnezia.vpn'
}

foreach ($rel in $map.Keys) {
    $srcFile = Join-Path $Source $rel
    $dstFile = Join-Path $Target $map[$rel]
    if (-not (Test-Path $srcFile)) {
        Write-Warning "Skip missing: $srcFile"
        continue
    }
    $content = Transform-Content (Get-Content $srcFile -Raw)
    $dir = Split-Path $dstFile -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content $dstFile $content -NoNewline
    Write-Host "Synced $rel"
}

Write-Host "Done. Fork-specific: DaddyVpnActivity, MainViewModel, VpnBridge, AndroidManifest."
