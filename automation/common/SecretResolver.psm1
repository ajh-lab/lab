Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-LabEnvMap {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Env file not found: $Path"
  }

  $map = @{}
  Get-Content -LiteralPath $Path | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    if ($_ -match '^\s*([^=]+)=(.*)$') {
      $key = $matches[1].Trim()
      $val = $matches[2].Trim()
      $map[$key] = $val
    }
  }
  return $map
}

function Get-OpenBaoConfig {
  param([hashtable]$EnvMap)

  $addr = $null
  if ($EnvMap.ContainsKey('LAB_SECRETS01_OPENBAO_ADDR')) {
    $addr = $EnvMap['LAB_SECRETS01_OPENBAO_ADDR']
  } elseif ($EnvMap.ContainsKey('OPENBAO_ADDR')) {
    $addr = $EnvMap['OPENBAO_ADDR']
  }

  $token = $null
  foreach ($k in @(
      'LAB_SECRETS01_OPENBAO_CONTEXT_TOKEN',
      'LAB_SECRETS01_OPENBAO_DEPLOY_TOKEN',
      'LAB_SECRETS01_OPENBAO_ROOT_TOKEN',
      'OPENBAO_ROOT_TOKEN'
    )) {
    if ($EnvMap.ContainsKey($k) -and -not [string]::IsNullOrWhiteSpace($EnvMap[$k])) {
      $token = $EnvMap[$k]
      break
    }
  }

  $mount = 'secret'
  if ($EnvMap.ContainsKey('LAB_OPENBAO_KV_MOUNT') -and -not [string]::IsNullOrWhiteSpace($EnvMap['LAB_OPENBAO_KV_MOUNT'])) {
    $mount = $EnvMap['LAB_OPENBAO_KV_MOUNT']
  }

  $envPath = 'homelab/bootstrap/env'
  if ($EnvMap.ContainsKey('LAB_OPENBAO_ENV_SECRET_PATH') -and -not [string]::IsNullOrWhiteSpace($EnvMap['LAB_OPENBAO_ENV_SECRET_PATH'])) {
    $envPath = $EnvMap['LAB_OPENBAO_ENV_SECRET_PATH']
  }

  [pscustomobject]@{
    Address = $addr
    Token = $token
    Mount = $mount
    EnvSecretPath = $envPath
  }
}

function Join-OpenBaoDataUri {
  param(
    [Parameter(Mandatory = $true)][string]$Address,
    [Parameter(Mandatory = $true)][string]$Mount,
    [Parameter(Mandatory = $true)][string]$Path
  )

  $base = $Address.TrimEnd('/')
  $mountEsc = [uri]::EscapeDataString($Mount.Trim('/'))
  $pathSegments = $Path.Trim('/') -split '/'
  $pathEsc = ($pathSegments | ForEach-Object { [uri]::EscapeDataString($_) }) -join '/'
  return "$base/v1/$mountEsc/data/$pathEsc"
}

function Invoke-OpenBaoWriteKvV2 {
  param(
    [Parameter(Mandatory = $true)][string]$Address,
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$Mount,
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][hashtable]$Data
  )

  $uri = Join-OpenBaoDataUri -Address $Address -Mount $Mount -Path $Path
  $headers = @{ 'X-Vault-Token' = $Token }
  $body = @{ data = $Data } | ConvertTo-Json -Depth 20
  return Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -ContentType 'application/json' -Body $body
}

function Get-OpenBaoKvV2Secret {
  param(
    [Parameter(Mandatory = $true)][string]$Address,
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$Mount,
    [Parameter(Mandatory = $true)][string]$Path
  )

  $uri = Join-OpenBaoDataUri -Address $Address -Mount $Mount -Path $Path
  $headers = @{ 'X-Vault-Token' = $Token }
  try {
    $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
  } catch {
    return $null
  }

  if ($null -eq $resp -or $null -eq $resp.data -or $null -eq $resp.data.data) {
    return $null
  }
  return $resp.data.data
}

function Get-SecretHint {
  param(
    [Parameter(Mandatory = $true)][string]$Key,
    [Parameter(Mandatory = $true)][hashtable]$EnvMap
  )

  $explicitPathKey = "LAB_SECRET_PATH__{0}" -f $Key
  $explicitFieldKey = "LAB_SECRET_FIELD__{0}" -f $Key

  if ($EnvMap.ContainsKey($explicitPathKey)) {
    $field = if ($EnvMap.ContainsKey($explicitFieldKey) -and -not [string]::IsNullOrWhiteSpace($EnvMap[$explicitFieldKey])) { $EnvMap[$explicitFieldKey] } else { $Key }
    return [pscustomobject]@{
      Path = $EnvMap[$explicitPathKey]
      Field = $field
    }
  }

  switch ($Key) {
    'N8N_API_KEY' { return [pscustomobject]@{ Path = 'homelab/services/n8n'; Field = 'api_key' } }
    'NETBOX_ADMIN_API_TOKEN' { return [pscustomobject]@{ Path = 'homelab/services/netbox'; Field = 'admin_api_token' } }
    'UDM_PRO_API_KEY' { return [pscustomobject]@{ Path = 'homelab/services/unifi'; Field = 'api_key' } }
    'LAB_REGISTRY01_REGISTRY_USER' { return [pscustomobject]@{ Path = 'homelab/registry/lab-registry01'; Field = 'registry_user' } }
    'LAB_REGISTRY01_REGISTRY_PASSWORD' { return [pscustomobject]@{ Path = 'homelab/registry/lab-registry01'; Field = 'registry_password' } }
    'LAB_REGISTRY01_ENDPOINT' { return [pscustomobject]@{ Path = 'homelab/registry/lab-registry01'; Field = 'endpoint' } }
    default { return $null }
  }
}

function Resolve-LabSecret {
  param(
    [Parameter(Mandatory = $true)][string]$Key,
    [Parameter(Mandatory = $true)][hashtable]$EnvMap,
    [switch]$DisableEnvFallback
  )

  $cfg = Get-OpenBaoConfig -EnvMap $EnvMap
  $hint = Get-SecretHint -Key $Key -EnvMap $EnvMap

  if (-not [string]::IsNullOrWhiteSpace($cfg.Address) -and -not [string]::IsNullOrWhiteSpace($cfg.Token)) {
    if ($hint -ne $null) {
      $data = Get-OpenBaoKvV2Secret -Address $cfg.Address -Token $cfg.Token -Mount $cfg.Mount -Path $hint.Path
      if ($data -ne $null -and $data.PSObject.Properties.Name -contains $hint.Field) {
        $val = [string]$data.$($hint.Field)
        if (-not [string]::IsNullOrWhiteSpace($val)) {
          return $val
        }
      }
    }

    $envData = Get-OpenBaoKvV2Secret -Address $cfg.Address -Token $cfg.Token -Mount $cfg.Mount -Path $cfg.EnvSecretPath
    if ($envData -ne $null -and $envData.PSObject.Properties.Name -contains $Key) {
      $envVal = [string]$envData.$Key
      if (-not [string]::IsNullOrWhiteSpace($envVal)) {
        return $envVal
      }
    }
  }

  if (-not $DisableEnvFallback -and $EnvMap.ContainsKey($Key) -and -not [string]::IsNullOrWhiteSpace($EnvMap[$Key])) {
    return [string]$EnvMap[$Key]
  }

  throw "Secret not found for key '$Key' in OpenBAO or .env fallback."
}

Export-ModuleMember -Function @(
  'Get-LabEnvMap',
  'Get-OpenBaoConfig',
  'Get-OpenBaoKvV2Secret',
  'Invoke-OpenBaoWriteKvV2',
  'Resolve-LabSecret'
)
