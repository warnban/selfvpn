# Apply DaddyVPN branding to amnezia-client fork
param(
    [string]$AmneziaRoot = "$PSScriptRoot\..\amnezia-client"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $AmneziaRoot)) {
    Write-Error "amnezia-client not found at $AmneziaRoot. Run: git clone --depth 1 https://github.com/amnezia-vpn/amnezia-client.git android/amnezia-client"
}

$buildGradle = Join-Path $AmneziaRoot "client\android\build.gradle.kts"
$content = Get-Content $buildGradle -Raw
$content = $content -replace 'applicationId = "org\.amnezia\.vpn"', 'applicationId = "site.daddyvpn.app"'
Set-Content $buildGradle $content -NoNewline

$stringsEn = Join-Path $AmneziaRoot "client\android\res\values\strings.xml"
if (Test-Path $stringsEn) {
    (Get-Content $stringsEn -Raw) `
        -replace 'AmneziaVPN', 'DaddyVPN' `
        -replace 'Amnezia VPN', 'Дядя Саня VPN' |
        Set-Content $stringsEn -NoNewline
}

Write-Host "Branding applied. applicationId=site.daddyvpn.app"
Write-Host "Next: build amnezia-client with Qt/Android SDK, merge daddyvpn-app Compose launcher."
