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
$modelId = 'qwen3.8-flash-next'
$modelContextWindow = 131072
$modelMaxTokens = 16384
$modelTimeoutMs = 5400000

function Get-OpenBaoKvV2SecretWithTokenCandidates {
  param(
    [Parameter(Mandatory = $true)][string]$Address,
    [Parameter(Mandatory = $true)][string]$Mount,
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][hashtable]$EnvMap,
    [string]$PreferredToken
  )

  $tokens = @()
  if (-not [string]::IsNullOrWhiteSpace($PreferredToken)) {
    $tokens += $PreferredToken
  }

  foreach ($tokenKey in @(
      'LAB_SECRETS01_OPENBAO_CONTEXT_TOKEN',
      'LAB_SECRETS01_OPENBAO_DEPLOY_TOKEN',
      'LAB_SECRETS01_OPENBAO_ROOT_TOKEN',
      'OPENBAO_ROOT_TOKEN'
    )) {
    if ($EnvMap.ContainsKey($tokenKey) -and -not [string]::IsNullOrWhiteSpace($EnvMap[$tokenKey])) {
      $tokens += $EnvMap[$tokenKey]
    }
  }

  $seen = @{}
  foreach ($token in $tokens) {
    if ($seen.ContainsKey($token)) { continue }
    $seen[$token] = $true
    $secret = Get-OpenBaoKvV2Secret -Address $Address -Token $token -Mount $Mount -Path $Path
    if ($null -ne $secret) {
      return $secret
    }
  }

  return $null
}

function Sync-IQ4XSPatch {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$PatchTemplate
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
      New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -LiteralPath $Path -Value $PatchTemplate -Encoding UTF8
    return
  }

  $existing = Get-Content -LiteralPath $Path -Raw
  $updated = $existing
  if ($updated -match 'ai-workstation-litellm') {
    $updated = $updated -replace 'Qwen3\.8 Flash-Next Uncensored OrcaRouter IQ4_XS', $modelId
    $updated = [regex]::Replace(
      $updated,
      '(?m)^(\s{8}defaultMaxTokens:\s*\d+)\s+timeoutMs:\s*\d+\s*$',
      { param($line) $line.Groups[1].Value + [Environment]::NewLine + "        timeoutMs: $modelTimeoutMs" }
    )
    $updated = $updated -replace '(defaultContextWindow:\s*)\d+', "`${1}$modelContextWindow"
    $updated = $updated -replace '(contextWindow:\s*)\d+', "`${1}$modelContextWindow"
    $updated = $updated -replace '(defaultMaxTokens:\s*)\d+', "`${1}$modelMaxTokens"
    $updated = $updated -replace '(maxTokens:\s*)\d+', "`${1}$modelMaxTokens"
    $updated = [regex]::Replace(
      $updated,
      '(?ms)(ai-workstation-litellm:\s*.*?)(?=^- id: llm-deepseek|\z)',
      {
        param($match)
        $block = $match.Groups[1].Value
        if ($block -match '(?m)^\s{8}timeoutMs:\s*\d+\s*$') {
          return [regex]::Replace($block, '(?m)^(\s{8}timeoutMs:\s*)\d+\s*$', "`${1}$modelTimeoutMs")
        }

        return [regex]::Replace(
          $block,
          '(?m)^(\s{8}defaultMaxTokens:\s*\d+)[^\S\r\n]*$',
          {
            param($line)
            $line.Groups[1].Value + [Environment]::NewLine + "        timeoutMs: $modelTimeoutMs"
          },
          1
        )
      },
      1
    )
  } elseif ($updated.Trim() -eq '[]') {
    $updated = $PatchTemplate
  } else {
    $updated = $updated.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + $PatchTemplate
  }

  if ($updated -ne $existing) {
    Set-Content -LiteralPath $Path -Value $updated -Encoding UTF8
  }
}

function Sync-DshSettingsMaxTokens {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path -LiteralPath $Path)) {
    return
  }

  $existing = Get-Content -LiteralPath $Path -Raw
  $updated = $existing -replace '(maxTokens:\s*)\d+', "`${1}$modelMaxTokens"
  $updated = $updated -replace 'Qwen3\.8 Flash-Next Uncensored OrcaRouter IQ4_XS', $modelId

  if ($updated -ne $existing) {
    Set-Content -LiteralPath $Path -Value $updated -Encoding UTF8
  }
}

Import-Module $resolverPath -Force
$envMap = Get-LabEnvMap -Path $envPath
$cfg = Get-OpenBaoConfig -EnvMap $envMap

if ([string]::IsNullOrWhiteSpace($cfg.Address) -or [string]::IsNullOrWhiteSpace($cfg.Token)) {
  throw 'OpenBao address/token is unavailable from the lab .env bootstrap.'
}

$apiKey = $null
$litellmSecret = Get-OpenBaoKvV2SecretWithTokenCandidates -Address $cfg.Address -Mount $cfg.Mount -Path 'homelab/providers/litellm' -EnvMap $envMap -PreferredToken $cfg.Token
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
$patchTemplate = Get-Content -LiteralPath $patchTemplatePath -Raw
Sync-IQ4XSPatch -Path (Join-Path $DshHome 'cordis.patch.yml') -PatchTemplate $patchTemplate

$webPatchPath = Join-Path $DshHome 'profiles\web\cordis.patch.yml'
if (Test-Path -LiteralPath (Split-Path -Parent $webPatchPath)) {
  Sync-IQ4XSPatch -Path $webPatchPath -PatchTemplate $patchTemplate
}

Sync-DshSettingsMaxTokens -Path (Join-Path $DshHome 'settings.yaml')

$env:DSH_HOME = $DshHome
$env:LITELLM_API_KEY = $apiKey
$env:DSH_TELEMETRY_MODE = 'DISABLED'

$bundledNodeBin = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin'
if (Test-Path -LiteralPath (Join-Path $bundledNodeBin 'node.exe')) {
  $env:PATH = "$bundledNodeBin;$env:PATH"
}

Set-Location -LiteralPath $Workspace

$args = @('--yes', '@deepseek-ai/dsh@0.1.6-alpha.2', 'web', '--port', "$Port")
if ($NoOpen) {
  $args += '--no-open'
}

Write-Host "Starting DeepSeek Harness for IQ4_XS at http://127.0.0.1:$Port/"
Write-Host "DSH_HOME=$DshHome"
npx @args
