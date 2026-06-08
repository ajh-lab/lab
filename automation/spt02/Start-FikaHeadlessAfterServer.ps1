$ErrorActionPreference = "Continue"

$LogPath = "C:\SPT\Logs\start-fika-headless-after-server.log"
$ReadyUrl = "https://127.0.0.1:6969/fika/headless/get"

function Write-Log {
  param([string]$Message)

  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Add-Content -LiteralPath $LogPath -Value "$stamp $Message"
}

Write-Log "Starting delayed Fika headless launcher"

$ready = $false
for ($i = 1; $i -le 180; $i++) {
  try {
    $code = & curl.exe -k -sS -o NUL -w "%{http_code}" $ReadyUrl -H "responsecompressed: 0" 2>$null
    if ($code -match "^(2|3|4)") {
      $ready = $true
      Write-Log "SPT/Fika server ready after attempt $($i) with HTTP $code"
      break
    }
    Write-Log "SPT/Fika server not ready on attempt $($i): HTTP $code"
  } catch {
    Write-Log "SPT/Fika server not ready on attempt $($i): $($_.Exception.Message)"
  }
  Start-Sleep -Seconds 5
}

if (-not $ready) {
  Write-Log "SPT/Fika server did not become ready; not starting FikaHeadlessManager"
  exit 1
}

$existing = Get-Process -Name "FikaHeadlessManager" -ErrorAction SilentlyContinue
if ($existing) {
  Write-Log "FikaHeadlessManager already running: $($existing.Id -join ',')"
  exit 0
}

Start-Process -FilePath "C:\SPT\FikaHeadlessManager.exe" -WorkingDirectory "C:\SPT"
Write-Log "Started FikaHeadlessManager"
