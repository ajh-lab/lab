param(
  [int]$Port = 3080,
  [string]$DshHome = "$env:USERPROFILE\.dsh-lab-iq4xs",
  [string]$Workspace = "$env:USERPROFILE\SourceControl\lab",
  [string]$AiWorkstationSsh = 'helios@192.168.1.123',
  [switch]$NoOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')
$envPath = Join-Path $repoRoot '.env'
$resolverPath = Join-Path $repoRoot 'automation\common\SecretResolver.psm1'
$patchTemplatePath = Join-Path $repoRoot 'automation\deepseek-harness\config\iq4xs.cordis.patch.yml'

Import-Module $resolverPath -Force
$envMap = Get-LabEnvMap -Path $envPath
$cfg = Get-OpenBaoConfig -EnvMap $envMap

if ([string]::IsNullOrWhiteSpace($cfg.Address) -or [string]::IsNullOrWhiteSpace($cfg.Token)) {
  throw 'OpenBao address/token is unavailable from the lab .env bootstrap.'
}

$apiKey = $null
$litellmSecret = Get-OpenBaoKvV2Secret -Address $cfg.Address -Token $cfg.Token -Mount $cfg.Mount -Path 'homelab/providers/litellm'
if ($null -ne $litellmSecret -and ($litellmSecret.PSObject.Properties.Name -contains 'lan_api_key')) {
  $apiKey = [string]$litellmSecret.lan_api_key
} elseif ($null -ne $litellmSecret -and ($litellmSecret.PSObject.Properties.Name -contains 'api_key')) {
  $apiKey = [string]$litellmSecret.api_key
}

if ([string]::IsNullOrWhiteSpace($apiKey)) {
  $remoteCommand = 'set -euo pipefail; f="$HOME/.config/litellm/litellm-lan-api-key.env"; [ -f "$f" ]; . "$f"; printf %s "$LITELLM_LAN_API_KEY"'
  $apiKey = [string](& ssh $AiWorkstationSsh $remoteCommand)
}

if ([string]::IsNullOrWhiteSpace($apiKey)) {
  throw 'LiteLLM LAN API key could not be resolved from OpenBao or the AI workstation runtime file.'
}

New-Item -ItemType Directory -Force -Path $DshHome | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $DshHome 'cordis.patch.yml'))) {
  Copy-Item -LiteralPath $patchTemplatePath -Destination (Join-Path $DshHome 'cordis.patch.yml')
}

$env:DSH_HOME = $DshHome
$env:DEEPSEEK_API_KEY = $apiKey
$env:DEEPSEEK_BASE_URL = 'http://192.168.1.123:4000/v1'
$env:DSH_TELEMETRY_MODE = 'DISABLED'

Set-Location -LiteralPath $Workspace

$args = @('--yes', '@deepseek-ai/dsh@0.1.2-rc.1', 'web', '--port', "$Port")
if ($NoOpen) {
  $args += '--no-open'
}

Write-Host "Starting DeepSeek Harness for IQ4_XS at http://127.0.0.1:$Port/"
Write-Host "DSH_HOME=$DshHome"
npx @args
