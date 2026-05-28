param(
  [string]$EnvPath = "",
  [string]$OpenBaoPath = "lab/runtime/openbrain"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}

Import-Module (Join-Path $repoRoot "automation\common\SecretResolver.psm1") -Force
$envMap = Get-LabEnvMap -Path $EnvPath
$cfg = Get-OpenBaoConfig -EnvMap $envMap

$token = $envMap['LAB_SECRETS01_OPENBAO_ROOT_TOKEN']
if ([string]::IsNullOrWhiteSpace($token)) {
  $token = $cfg.Token
}

$secret = Get-OpenBaoKvV2Secret -Address $cfg.Address -Token $token -Mount $cfg.Mount -Path $OpenBaoPath
if ($null -eq $secret -or [string]::IsNullOrWhiteSpace([string]$secret.mcp_access_key)) {
  throw "OpenBrain MCP key not found at secret/$OpenBaoPath"
}

$payloadFile = Join-Path $env:TEMP "openbrain-tools-list.json"
'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | Set-Content -NoNewline -Path $payloadFile

$response = curl.exe -ksS https://openbrain.192.168.1.80.sslip.io/ `
  -H ("x-brain-key: " + [string]$secret.mcp_access_key) `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  --data-binary ("@" + $payloadFile)

Remove-Item -Force $payloadFile -ErrorAction SilentlyContinue

if ($response -match "search_thoughts" -and $response -match "capture_thought") {
  Write-Host "OpenBrain endpoint check: PASS"
} else {
  Write-Host "OpenBrain endpoint check: FAIL"
  Write-Output $response
  exit 1
}
