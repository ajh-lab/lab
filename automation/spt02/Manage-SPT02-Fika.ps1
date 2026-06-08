$ErrorActionPreference = "Continue"

$ServerTaskName = "SPT02-SPT-Server"
$HeadlessTaskName = "SPT02-Fika-Headless"
$ServerUrl = "https://127.0.0.1:6969/fika/headless/get"
$HeadlessUrl = "https://127.0.0.1:6969/fika/headless/get"
$LogPath = "C:\SPT\Logs\SPT02-fika-manager.log"

function Write-Log {
  param([string]$Message)

  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$stamp $Message"
  Add-Content -LiteralPath $LogPath -Value $line -ErrorAction SilentlyContinue
}
function Write-Header {
  Clear-Host
  Write-Host "SPT02 Fika Server Manager" -ForegroundColor Cyan
  Write-Host "==========================" -ForegroundColor Cyan
  Write-Host ""
  Write-Host "This tool starts, stops, or restarts the SPT/Fika server setup on this host."
  Write-Host "It controls:"
  Write-Host "  - SPT.Server.exe backend on https://192.168.1.86:6969"
  Write-Host "  - FikaHeadlessManager.exe after the SPT backend is ready"
  Write-Host ""
}
function Test-SptReady {
  try {
    $code = & curl.exe -k -sS -o NUL -w "%{http_code}" $ServerUrl 2>$null
    return ($code -match "^(2|3|4)")
  } catch {
    return $false
  }
}

function Get-HeadlessJson {
  try {
    return (& curl.exe -k -sS $HeadlessUrl -H "responsecompressed: 0" 2>$null)
  } catch {
    return ""
  }
}

function Show-Status {
  $spt = Get-Process -Name "SPT.Server" -ErrorAction SilentlyContinue
  $manager = Get-Process -Name "FikaHeadlessManager" -ErrorAction SilentlyContinue
  $tarkov = Get-Process -Name "EscapeFromTarkov" -ErrorAction SilentlyContinue
  $listener = Get-NetTCPConnection -LocalPort 6969 -State Listen -ErrorAction SilentlyContinue
  $headless = Get-HeadlessJson

  Write-Host "Current status:" -ForegroundColor Yellow
  Write-Host ("  SPT.Server process:        {0}" -f ($(if ($spt) { "Running (PID $($spt.Id -join ', '))" } else { "Stopped" })))
  Write-Host ("  FikaHeadlessManager:       {0}" -f ($(if ($manager) { "Running (PID $($manager.Id -join ', '))" } else { "Stopped" })))
  Write-Host ("  EscapeFromTarkov headless: {0}" -f ($(if ($tarkov) { "Running (PID $($tarkov.Id -join ', '))" } else { "Stopped" })))
  Write-Host ("  TCP 6969 listener:         {0}" -f ($(if ($listener) { "Listening" } else { "Not listening" })))
  Write-Host ("  Backend health check:      {0}" -f ($(if (Test-SptReady) { "OK" } else { "Not ready" })))
  if (-not [string]::IsNullOrWhiteSpace($headless)) {
    Write-Host ("  Fika headless endpoint:    {0}" -f $headless)
  }
  Write-Host ""
}

function Stop-FikaSetup {
  Write-Host "Stopping Fika/SPT tasks and processes..." -ForegroundColor Yellow
  Write-Log "Stop requested"

  foreach ($task in @($HeadlessTaskName, $ServerTaskName)) {
    Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
  }

  Get-Process -Name "FikaHeadlessManager", "EscapeFromTarkov", "SPT.Server", "Fika-Installer" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

  Start-Sleep -Seconds 3
  Write-Log "Stop completed"
  Show-Status
}

function Start-FikaSetup {
  Write-Host "Starting SPT backend..." -ForegroundColor Yellow
  Write-Log "Start requested"

  if (-not (Get-Process -Name "SPT.Server" -ErrorAction SilentlyContinue)) {
    Start-ScheduledTask -TaskName $ServerTaskName
  } else {
    Write-Host "SPT.Server is already running."
  }

  Write-Host "Waiting for SPT backend to become ready on port 6969..."
  $ready = $false
  for ($i = 1; $i -le 180; $i++) {
    if (Test-SptReady) {
      $ready = $true
      break
    }
    Start-Sleep -Seconds 5
  }

  if (-not $ready) {
    Write-Host "SPT backend did not become ready in time. Headless manager was not started." -ForegroundColor Red
    Write-Log "Start failed: backend did not become ready"
    Show-Status
    return
  }

  Write-Host "SPT backend is ready. Starting Fika headless manager..." -ForegroundColor Green
  if (-not (Get-Process -Name "FikaHeadlessManager" -ErrorAction SilentlyContinue)) {
    Start-ScheduledTask -TaskName $HeadlessTaskName
  } else {
    Write-Host "FikaHeadlessManager is already running."
  }

  Start-Sleep -Seconds 8
  Write-Log "Start completed"
  Show-Status
}

function Restart-FikaSetup {
  Write-Host "Restarting SPT/Fika setup..." -ForegroundColor Yellow
  Write-Log "Restart requested"
  Stop-FikaSetup
  Start-Sleep -Seconds 5
  Start-FikaSetup
}

while ($true) {
  Write-Header
  Show-Status
  Write-Host "Choose an action:"
  Write-Host "  1. Start server setup"
  Write-Host "  2. Stop server setup"
  Write-Host "  3. Restart server setup"
  Write-Host "  4. Refresh status"
  Write-Host "  5. Exit"
  Write-Host ""

  $choice = Read-Host "Enter 1, 2, 3, 4, or 5"
  Write-Host ""

  switch ($choice) {
    "1" { Start-FikaSetup; Read-Host "Press Enter to continue" | Out-Null }
    "2" { Stop-FikaSetup; Read-Host "Press Enter to continue" | Out-Null }
    "3" { Restart-FikaSetup; Read-Host "Press Enter to continue" | Out-Null }
    "4" { Show-Status; Read-Host "Press Enter to continue" | Out-Null }
    "5" { Write-Host "Exiting."; break }
    default { Write-Host "Invalid choice." -ForegroundColor Red; Start-Sleep -Seconds 2 }
  }
}
