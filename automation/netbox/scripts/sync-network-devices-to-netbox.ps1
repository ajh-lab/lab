param(
  [string]$CsvPath = "",
  [string]$EnvPath = "",
  [string]$NetBoxBaseUrl = "http://192.168.1.80:32081",
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Invoke-NetBox {
  param(
    [Parameter(Mandatory = $true)][ValidateSet('GET','POST','PATCH')][string]$Method,
    [Parameter(Mandatory = $true)][string]$Uri,
    [hashtable]$Headers,
    [object]$Body
  )

  if ($null -ne $Body) {
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 20)
  }
  return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers
}

function Ensure-TagId {
  param(
    [string]$BaseUrl,
    [hashtable]$Headers,
    [string]$Name,
    [string]$Slug,
    [string]$Color
  )

  $existing = Invoke-NetBox -Method GET -Uri "$BaseUrl/api/extras/tags/?slug=$Slug" -Headers $Headers
  if ($existing.count -gt 0) {
    return $existing.results[0].id
  }

  $body = @{
    name = $Name
    slug = $Slug
    color = $Color
    description = "Imported from network_devices.csv sync"
  }
  $created = Invoke-NetBox -Method POST -Uri "$BaseUrl/api/extras/tags/" -Headers $Headers -Body $body
  return $created.id
}

function Ensure-Prefix {
  param(
    [string]$BaseUrl,
    [hashtable]$Headers,
    [string]$Prefix
  )

  $existing = Invoke-NetBox -Method GET -Uri "$BaseUrl/api/ipam/prefixes/?prefix=$Prefix" -Headers $Headers
  if ($existing.count -gt 0) {
    return
  }

  $body = @{
    prefix = $Prefix
    status = "active"
    description = "Discovered network segment from network_devices.csv"
  }
  [void](Invoke-NetBox -Method POST -Uri "$BaseUrl/api/ipam/prefixes/" -Headers $Headers -Body $body)
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$secretModule = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $secretModule -Force

if ([string]::IsNullOrWhiteSpace($CsvPath)) {
  $CsvPath = Join-Path $repoRoot 'network_devices.csv'
}
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot '.env'
}

if (-not (Test-Path -LiteralPath $CsvPath)) {
  throw "CSV not found: $CsvPath"
}

$envMap = Get-LabEnvMap -Path $EnvPath
$token = Resolve-LabSecret -Key 'NETBOX_ADMIN_API_TOKEN' -EnvMap $envMap

$headers = @{ Authorization = "Token $token" }

# Validate API auth early
try {
  [void](Invoke-NetBox -Method GET -Uri "$NetBoxBaseUrl/api/ipam/ip-addresses/?limit=1" -Headers $headers)
} catch {
  throw "NetBox API authentication failed. Verify NETBOX_ADMIN_API_TOKEN. Details: $($_.Exception.Message)"
}

$rows = Import-Csv -LiteralPath $CsvPath | Where-Object { $_.UsableHost -eq 'TRUE' -and -not [string]::IsNullOrWhiteSpace($_.IPAddress) }

$segments = $rows |
  ForEach-Object {
    $ipParts = $_.IPAddress.Split('.')
    if ($ipParts.Count -eq 4) {
      "{0}.{1}.{2}.0/24" -f $ipParts[0], $ipParts[1], $ipParts[2]
    }
  } |
  Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
  Sort-Object -Unique

$tagId = $null
if (-not $WhatIf) {
  $tagId = Ensure-TagId -BaseUrl $NetBoxBaseUrl -Headers $headers -Name 'network-csv-import' -Slug 'network-csv-import' -Color '607d8b'
  foreach ($segment in $segments) {
    Ensure-Prefix -BaseUrl $NetBoxBaseUrl -Headers $headers -Prefix $segment
  }
}

$created = 0
$updated = 0
$skipped = 0
$failed = 0
$errors = New-Object System.Collections.Generic.List[string]

foreach ($row in $rows) {
  try {
    $ip = $row.IPAddress.Trim()
    if (-not [System.Net.IPAddress]::TryParse($ip, [ref]([System.Net.IPAddress]$null))) {
      $skipped++
      continue
    }

    $address = if ($ip.Contains(':')) { "$ip/128" } else { "$ip/32" }

    $dnsName = ""
    if (-not [string]::IsNullOrWhiteSpace($row.Hostname)) {
      $dnsName = $row.Hostname.Trim()
    }

    $descParts = @()
    if (-not [string]::IsNullOrWhiteSpace($row.Name)) { $descParts += $row.Name.Trim() }
    if (-not [string]::IsNullOrWhiteSpace($row.Description)) { $descParts += $row.Description.Trim() }
    $description = ($descParts -join ' | ')

    $commentsLines = @(
      "Source: network_devices.csv",
      "Reachable: $($row.Reachable)",
      "MgmtReachable: $($row.MgmtReachable)",
      "LatencyMs: $($row.LatencyMs)",
      "CheckedAt: $($row.CheckedAt)",
      "LastUpdated: $($row.LastUpdated)"
    )
    if (-not [string]::IsNullOrWhiteSpace($row.Notes)) {
      $commentsLines += "Notes: $($row.Notes.Trim())"
    }
    if (-not [string]::IsNullOrWhiteSpace($row.CredentialRef)) {
      $commentsLines += "CredentialRef: $($row.CredentialRef.Trim())"
    }
    $comments = ($commentsLines -join "`n")

    $payload = @{
      address = $address
      status = "active"
      description = $description
      comments = $comments
    }

    if (-not [string]::IsNullOrWhiteSpace($dnsName)) {
      $payload.dns_name = $dnsName
    }

    if ($null -ne $tagId) {
      $payload.tags = @($tagId)
    }

    if ($WhatIf) {
      Write-Host "[WhatIf] Would upsert $address"
      continue
    }

    $existing = Invoke-NetBox -Method GET -Uri "$NetBoxBaseUrl/api/ipam/ip-addresses/?address=$address" -Headers $headers
    if ($existing.count -gt 0) {
      $id = $existing.results[0].id
      [void](Invoke-NetBox -Method PATCH -Uri "$NetBoxBaseUrl/api/ipam/ip-addresses/$id/" -Headers $headers -Body $payload)
      $updated++
    } else {
      [void](Invoke-NetBox -Method POST -Uri "$NetBoxBaseUrl/api/ipam/ip-addresses/" -Headers $headers -Body $payload)
      $created++
    }
  }
  catch {
    $failed++
    $errors.Add("$($row.IPAddress): $($_.Exception.Message)")
  }
}

Write-Host "Sync complete. created=$created updated=$updated skipped=$skipped failed=$failed total=$($rows.Count)"
if ($errors.Count -gt 0) {
  Write-Host "Failures:"
  $errors | Select-Object -First 20 | ForEach-Object { Write-Host " - $_" }
}
