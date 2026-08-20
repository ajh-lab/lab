param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
  [string]$WikiGraphqlUri = 'https://wikijs.192.168.1.80.sslip.io/graphql'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

Import-Module (Join-Path $RepoRoot 'automation/common/SecretResolver.psm1') -Force

$envPath = Join-Path $RepoRoot '.env'
$envMap = Get-LabEnvMap -Path $envPath

function Resolve-WikiApiKey {
  if ($envMap.ContainsKey('WIKIJS_ADMIN_API_KEY') -and -not [string]::IsNullOrWhiteSpace($envMap['WIKIJS_ADMIN_API_KEY'])) {
    return [string]$envMap['WIKIJS_ADMIN_API_KEY']
  }

  return Resolve-LabSecret -Key 'WIKIJS_ADMIN_API_KEY' -EnvMap $envMap
}

$apiKey = Resolve-WikiApiKey
$headers = @{
  Authorization = "Bearer $apiKey"
  'Content-Type' = 'application/json'
}

function Invoke-WikiGql {
  param(
    [Parameter(Mandatory = $true)][string]$Query,
    [hashtable]$Variables = @{}
  )

  $body = @{ query = $Query; variables = $Variables } | ConvertTo-Json -Depth 30
  $response = Invoke-RestMethod -Method Post -Uri $WikiGraphqlUri -Headers $headers -Body $body -TimeoutSec 120
  if ($response.PSObject.Properties.Name -contains 'errors' -and $response.errors) {
    throw "Wiki GraphQL error: $($response.errors | ConvertTo-Json -Depth 10)"
  }
  return $response.data
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
  if ($existing -and $existing.id) {
    $query = @'
mutation ($id: Int!, $content: String!, $description: String!, $title: String!) {
  pages {
    update(id: $id, content: $content, description: $description, title: $title, editor: "markdown", isPublished: true, isPrivate: false, locale: "en", tags: ["droneops", "bs01", "longhorn"]) {
      responseResult {
        succeeded
        message
      }
      page {
        path
      }
    }
  }
}
'@
    $result = Invoke-WikiGql -Query $query -Variables @{
      id = [int]$existing.id
      title = $Title
      description = $Description
      content = $Content
    }
    if (-not $result.pages.update.responseResult.succeeded) {
      throw "Wiki update failed for /en/$Path`: $($result.pages.update.responseResult.message)"
    }
    Write-Host ("wiki_action=updated path=/en/{0}" -f $result.pages.update.page.path)
    return
  }

  $query = @'
mutation ($content: String!, $description: String!, $path: String!, $title: String!) {
  pages {
    create(content: $content, description: $description, editor: "markdown", isPublished: true, isPrivate: false, locale: "en", path: $path, tags: ["droneops", "bs01", "longhorn"], title: $title) {
      responseResult {
        succeeded
        message
      }
      page {
        path
      }
    }
  }
}
'@
  $result = Invoke-WikiGql -Query $query -Variables @{
    title = $Title
    description = $Description
    path = $Path
    content = $Content
  }
  if (-not $result.pages.create.responseResult.succeeded) {
    throw "Wiki create failed for /en/$Path`: $($result.pages.create.responseResult.message)"
  }
  Write-Host ("wiki_action=created path=/en/{0}" -f $result.pages.create.page.path)
}

$runbook = Get-Content -Raw -Path (Join-Path $RepoRoot 'docs/bs01-longhorn-runbook.md')
$fieldRack = Get-Content -Raw -Path (Join-Path $RepoRoot 'docs/bs01-field-rack.md')

$content = @"
# BS01 Longhorn Storage

This page is generated from the lab repo. Do not add secrets here.

Source files:

- `docs/bs01-longhorn-runbook.md`
- `docs/bs01-field-rack.md`
- `k8s/field/bs01/argocd/longhorn-application.yaml`

## Runbook

$runbook

## Field Rack Summary

$fieldRack
"@

Set-WikiPage -Path 'runbooks/bs01-longhorn-storage' -Title 'BS01 Longhorn Storage' -Description 'Longhorn storage setup, verification, and operations notes for the BS01 field k3s cluster' -Content $content
