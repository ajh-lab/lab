param(
  [string]$EnvPath = "",
  [string]$ContentPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}
if ([string]::IsNullOrWhiteSpace($ContentPath)) {
  $ContentPath = Join-Path $repoRoot "docs\spt-fika-runbook.md"
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
  throw "Missing env file: $EnvPath"
}
if (-not (Test-Path -LiteralPath $ContentPath)) {
  throw "Missing content file: $ContentPath"
}

Import-Module (Join-Path $repoRoot "automation\common\SecretResolver.psm1") -Force

$envMap = Get-LabEnvMap -Path $EnvPath
$apiKey = Resolve-LabSecret -Key "WIKIJS_ADMIN_API_KEY" -EnvMap $envMap
if ([string]::IsNullOrWhiteSpace($apiKey)) {
  throw "WIKIJS_ADMIN_API_KEY could not be resolved"
}

$uri = "https://wikijs.192.168.1.80.sslip.io/graphql"
$locale = "en"
$tags = @("services", "gaming", "spt", "fika", "windows", "physical-host", "vpn")

[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

function Invoke-WikiGql {
  param(
    [Parameter(Mandatory = $true)][string]$Query,
    [hashtable]$Variables = @{},
    [int]$TimeoutSec = 120
  )

  $body = @{ query = $Query; variables = $Variables } | ConvertTo-Json -Depth 30
  try {
    $resp = Invoke-RestMethod -Method POST -Uri $uri -Headers @{ Authorization = "Bearer $apiKey" } -ContentType "application/json" -Body $body -TimeoutSec $TimeoutSec
  } catch {
    if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream()) {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $raw = $reader.ReadToEnd()
      throw "Wiki GraphQL HTTP error. Payload: $raw"
    }
    throw
  }
  if ($resp.errors) {
    throw ($resp.errors | ConvertTo-Json -Depth 30)
  }
  return $resp.data
}

function Get-WikiPageByPath {
  param([Parameter(Mandatory = $true)][string]$Path)

  $query = @'
query {
  pages {
    list(orderBy: UPDATED, orderByDirection: DESC) {
      id
      path
      title
    }
  }
}
'@

  $result = Invoke-WikiGql -Query $query
  return @($result.pages.list) | Where-Object { $_.path -eq $Path } | Select-Object -First 1
}

function Set-WikiPage {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Title,
    [Parameter(Mandatory = $true)][string]$Description,
    [Parameter(Mandatory = $true)][string]$Content
  )

  $existing = Get-WikiPageByPath -Path $Path
  if ($null -ne $existing -and $existing.id) {
    $updateQuery = @'
mutation ($id: Int!, $content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    update(id: $id, content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded errorCode message slug }
      page { id path title }
    }
  }
}
'@

    $result = Invoke-WikiGql -Query $updateQuery -Variables @{
      id = [int]$existing.id
      content = $Content
      description = $Description
      editor = "markdown"
      isPublished = $true
      isPrivate = $false
      locale = $locale
      path = $Path
      tags = $tags
      title = $Title
    }

    if (-not $result.pages.update.responseResult.succeeded) {
      throw "Wiki update failed for /en/$Path`: $($result.pages.update.responseResult.message)"
    }
    Write-Host ("wiki_action=updated path=/en/{0}" -f $result.pages.update.page.path)
    return
  }

  $createQuery = @'
mutation ($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded errorCode message slug }
      page { id path title }
    }
  }
}
'@

  $result = Invoke-WikiGql -Query $createQuery -Variables @{
    content = $Content
    description = $Description
    editor = "markdown"
    isPublished = $true
    isPrivate = $false
    locale = $locale
    path = $Path
    tags = $tags
    title = $Title
  }

  if (-not $result.pages.create.responseResult.succeeded) {
    throw "Wiki create failed for /en/$Path`: $($result.pages.create.responseResult.message)"
  }
  Write-Host ("wiki_action=created path=/en/{0}" -f $result.pages.create.page.path)
}

$fullContent = Get-Content -LiteralPath $ContentPath -Raw
$marker = "## Current Mod State"
$markerIndex = $fullContent.IndexOf($marker)
if ($markerIndex -lt 0) {
  throw "Unable to split Wiki content because marker was not found: $marker"
}

$mainContent = $fullContent.Substring(0, $markerIndex).TrimEnd()
$mainContent = @(
  $mainContent
  ""
  "## Related Operations"
  ""
  "Mod state, remote management, Hermes/Discord operations, and troubleshooting are documented in [SPT/Fika Mods And Operations](/en/runbooks/spt-fika-server-operations)."
) -join "`r`n"

$operationsContent = @(
  "# SPT/Fika Mods And Operations"
  ""
  "Back to [SPT/Fika Server Runbook](/en/runbooks/spt-fika-server)."
  ""
  $fullContent.Substring($markerIndex).TrimStart()
) -join "`r`n"

$serviceIndex = @'
# SPT/Fika Server (spt02)

spt02 is the Windows 10 physical host that hosts the lab SPT/Fika Escape From Tarkov co-op backend and optional Fika headless raid host.

- Main runbook: [SPT/Fika Server Runbook](/en/runbooks/spt-fika-server)
- Mods and operations: [SPT/Fika Mods And Operations](/en/runbooks/spt-fika-server-operations)
- Service host: `spt02`
- IP address: `192.168.1.86`
- SPT backend URL: `https://192.168.1.86:6969`
- VPN server: UDM Pro WireGuard server `SPT-Fika-WireGuard`
- VPN subnet: `192.168.86.0/24`

Do not store spt02 passwords, VPN private keys, Discord webhook URLs, or API tokens in Wiki.js.
'@

Set-WikiPage -Path "runbooks/spt-fika-server" -Title "SPT/Fika Server Runbook" -Description "Architecture, VPN, player setup, hosting modes, and baseline SPT/Fika configuration" -Content $mainContent
Set-WikiPage -Path "runbooks/spt-fika-server-operations" -Title "SPT/Fika Mods And Operations" -Description "SPT/Fika mod state, remote management, Hermes operations, and troubleshooting" -Content $operationsContent
Set-WikiPage -Path "services/spt02" -Title "SPT/Fika Server (spt02)" -Description "Windows 10 physical host for hosting SPT/Fika Escape From Tarkov co-op service" -Content $serviceIndex
