param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("Start", "Stop", "Restart", "Status")]
  [string]$Action
)

$ErrorActionPreference = "Continue"

$ServerTaskName = "SPT02-SPT-Server"
$HeadlessTaskName = "SPT02-Fika-Headless"
$ServerUrl = "https://127.0.0.1:6969/fika/headless/get"
$HeadlessUrl = "https://127.0.0.1:6969/fika/headless/get"
$LogPath = "C:\SPT\Logs\SPT02-fika-action.log"

function Write-Log {
  param([string]$Message)
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Add-Content -LiteralPath $LogPath -Value "$stamp $Message" -ErrorAction SilentlyContinue
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

function Get-FikaStatus {
  $spt = Get-Process -Name "SPT.Server" -ErrorAction SilentlyContinue
  $manager = Get-Process -Name "FikaHeadlessManager" -ErrorAction SilentlyContinue
  $tarkov = Get-Process -Name "EscapeFromTarkov" -ErrorAction SilentlyContinue
  $listener = Get-NetTCPConnection -LocalPort 6969 -State Listen -ErrorAction SilentlyContinue

  [pscustomobject]@{
    computerName = $env:COMPUTERNAME
    sptServerRunning = [bool]$spt
    sptServerPids = @($spt | ForEach-Object { $_.Id })
    fikaHeadlessManagerRunning = [bool]$manager
    fikaHeadlessManagerPids = @($manager | ForEach-Object { $_.Id })
    escapeFromTarkovRunning = [bool]$tarkov
    escapeFromTarkovPids = @($tarkov | ForEach-Object { $_.Id })
    port6969Listening = [bool]$listener
    backendReady = Test-SptReady
    headlessEndpoint = Get-HeadlessJson
    timestamp = (Get-Date).ToString("s")
  }
}

function Stop-FikaSetup {
  Write-Log "Stop requested"
  foreach ($task in @($HeadlessTaskName, $ServerTaskName)) {
    Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
  }
  Get-Process -Name "FikaHeadlessManager", "EscapeFromTarkov", "SPT.Server", "Fika-Installer" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 3
  Write-Log "Stop completed"
}

function Start-FikaSetup {
  Write-Log "Start requested"
  if (-not (Get-Process -Name "SPT.Server" -ErrorAction SilentlyContinue)) {
    Start-ScheduledTask -TaskName $ServerTaskName
  }

  $ready = $false
  for ($i = 1; $i -le 180; $i++) {
    if (Test-SptReady) {
      $ready = $true
      break
    }
    Start-Sleep -Seconds 5
  }

  if (-not $ready) {
    Write-Log "Start failed: backend did not become ready"
    throw "SPT backend did not become ready in time."
  }

  if (-not (Get-Process -Name "FikaHeadlessManager" -ErrorAction SilentlyContinue)) {
    Start-ScheduledTask -TaskName $HeadlessTaskName
  }
  Start-Sleep -Seconds 8
  Write-Log "Start completed"
}

switch ($Action) {
  "Start" { Start-FikaSetup }
  "Stop" { Stop-FikaSetup }
  "Restart" {
    Write-Log "Restart requested"
    Stop-FikaSetup
    Start-Sleep -Seconds 5
    Start-FikaSetup
  }
  "Status" { }
}

Get-FikaStatus | ConvertTo-Json -Depth 5
