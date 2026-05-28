param(
  [string]$EnvPath = "",
  [string]$OutputPath = "",
  [int]$PageLimit = 200
)

$ErrorActionPreference = "Stop"

function Invoke-UnifiGet {
  param(
    [Parameter(Mandatory = $true)][string]$BaseUrl,
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$ApiKey
  )

  $url = "$BaseUrl$Path"
  $raw = & curl.exe -k -sS -H "X-API-Key: $ApiKey" $url
  if ($LASTEXITCODE -ne 0) {
    throw "curl failed for $url"
  }

  try {
    return ($raw | ConvertFrom-Json)
  } catch {
    throw "Failed to parse JSON from $url"
  }
}

function Get-PagedItems {
  param(
    [Parameter(Mandatory = $true)][string]$BaseUrl,
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$ApiKey,
    [int]$Limit = 200
  )

  $offset = 0
  $all = @()

  while ($true) {
    $separator = if ($Path.Contains('?')) { '&' } else { '?' }
    $pagedPath = "$Path${separator}limit=$Limit&offset=$offset"
    $resp = Invoke-UnifiGet -BaseUrl $BaseUrl -Path $pagedPath -ApiKey $ApiKey

    $chunk = @($resp.data)
    if ($chunk.Count -gt 0) {
      $all += $chunk
    }

    $total = 0
    if ($null -ne $resp.totalCount) {
      $total = [int]$resp.totalCount
    } elseif ($null -ne $resp.count) {
      $total = [int]$resp.count
    } else {
      $total = $all.Count
    }

    if ($all.Count -ge $total -or $chunk.Count -eq 0) {
      break
    }

    $offset += $Limit
  }

  return @($all)
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$secretModule = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $secretModule -Force

if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot '.env'
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $OutputPath = Join-Path $repoRoot 'automation\unifi\data\unifi-inventory-latest.json'
}

$envMap = Get-LabEnvMap -Path $EnvPath
$apiKey = Resolve-LabSecret -Key 'UDM_PRO_API_KEY' -EnvMap $envMap

$udmHost = $envMap['UDM_PRO_HOST']
if ([string]::IsNullOrWhiteSpace($udmHost)) {
  $udmHost = '192.168.1.1'
}

$baseUrl = "https://$udmHost"

$sitesResp = Invoke-UnifiGet -BaseUrl $baseUrl -Path '/proxy/network/integration/v1/sites' -ApiKey $apiKey
$sites = @($sitesResp.data)

$resultSites = @()
foreach ($site in $sites) {
  $siteId = $site.id
  $devices = Get-PagedItems -BaseUrl $baseUrl -Path "/proxy/network/integration/v1/sites/$siteId/devices" -ApiKey $apiKey -Limit $PageLimit
  $clients = Get-PagedItems -BaseUrl $baseUrl -Path "/proxy/network/integration/v1/sites/$siteId/clients" -ApiKey $apiKey -Limit $PageLimit
  $networks = Get-PagedItems -BaseUrl $baseUrl -Path "/proxy/network/integration/v1/sites/$siteId/networks" -ApiKey $apiKey -Limit $PageLimit

  $resultSites += [pscustomobject]@{
    id = $site.id
    name = $site.name
    internal_reference = $site.internal_reference
    devices = $devices
    clients = $clients
    networks = $networks
  }
}

$payload = [pscustomobject]@{
  generatedAt = (Get-Date).ToString('o')
  host = $udmHost
  sites = $resultSites
}

$parentDir = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $parentDir)) {
  New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
}

($payload | ConvertTo-Json -Depth 20) | Set-Content -LiteralPath $OutputPath -Encoding UTF8

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$archivePath = Join-Path $parentDir ("unifi-inventory-$stamp.json")
Copy-Item -LiteralPath $OutputPath -Destination $archivePath -Force

$deviceCount = ($resultSites | ForEach-Object { @($_.devices).Count } | Measure-Object -Sum).Sum
$clientCount = ($resultSites | ForEach-Object { @($_.clients).Count } | Measure-Object -Sum).Sum
$networkCount = ($resultSites | ForEach-Object { @($_.networks).Count } | Measure-Object -Sum).Sum

Write-Host ("UniFi inventory fetched. sites={0} devices={1} clients={2} networks={3}" -f $resultSites.Count, $deviceCount, $clientCount, $networkCount)
Write-Host ("Latest: {0}" -f $OutputPath)
Write-Host ("Archive: {0}" -f $archivePath)
