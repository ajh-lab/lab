param(
  [string]$EnvPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
  throw "Missing env file: $EnvPath"
}

$envMap = @{}
Get-Content -LiteralPath $EnvPath | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k, $v = $_ -split '=', 2
  $envMap[$k.Trim()] = $v.Trim().Trim('"')
}

$apiKey = $envMap["WIKIJS_ADMIN_API_KEY"]
if ([string]::IsNullOrWhiteSpace($apiKey)) {
  throw "WIKIJS_ADMIN_API_KEY missing in .env"
}

$uri = "https://wikijs.192.168.1.80.sslip.io/graphql"
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

function Invoke-WikiGql {
  param(
    [Parameter(Mandatory = $true)][string]$Query,
    [hashtable]$Variables
  )

  $body = @{ query = $Query; variables = $Variables } | ConvertTo-Json -Depth 20
  try {
    $resp = Invoke-RestMethod -Method POST -Uri $uri -Headers @{ Authorization = "Bearer $apiKey" } -ContentType "application/json" -Body $body
  } catch {
    if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream()) {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $raw = $reader.ReadToEnd()
      throw "Wiki GraphQL HTTP error. Payload: $raw"
    }
    throw
  }
  if ($resp.errors) {
    throw ($resp.errors | ConvertTo-Json -Depth 20)
  }
  return $resp.data
}

$path = "services/container-registry"
$locale = "en"
$tags = @("services", "infrastructure", "registry", "containers")
$title = "Container Registry (lab-registry01)"
$description = "Internal Docker registry service (lab-registry01)"
$content = @'
# Container Registry (lab-registry01)

## Overview
- Hostname: `lab-registry01`
- Role: Internal container image registry (Docker Registry v2)
- VM IP: `192.168.1.15`
- Endpoint: `http://192.168.1.15:5000`

## Authentication
- Auth mode: `htpasswd` (basic auth)
- Credential source: OpenBao path `secret/homelab/registry/lab-registry01`
- Required fields: `endpoint`, `registry_user`, `registry_password`

## Operations
- Registry compose path on host: `/opt/registry/docker-compose.yml`
- Registry data path on host: `/opt/registry/data`
- Registry auth file on host: `/opt/registry/auth/htpasswd`

## Client Usage
1. `docker login 192.168.1.15:5000`
2. `docker tag <image> 192.168.1.15:5000/<repo>/<image>:<tag>`
3. `docker push 192.168.1.15:5000/<repo>/<image>:<tag>`

## Kubernetes Usage
- k3s nodes use `/etc/rancher/k3s/registries.yaml` for this registry.
- Current test image repository: `192.168.1.15:5000/lab/hello-world:latest`
'@

$searchExistingQuery = @'
query ($query: String!, $locale: String!) {
  pages {
    search(query: $query, locale: $locale, path: "") {
      results { id path title }
    }
  }
}
'@
$existingSearch = Invoke-WikiGql -Query $searchExistingQuery -Variables @{ query = "container registry lab-registry01"; locale = $locale }
$match = @($existingSearch.pages.search.results) | Where-Object { $_.path -eq $path } | Select-Object -First 1
if ($null -eq $match) {
  $match = @($existingSearch.pages.search.results) | Where-Object { $_.title -eq $title } | Select-Object -First 1
}

if ($null -ne $match -and $match.id) {
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
    id = [int]$match.id
    content = $content
    description = $description
    editor = "markdown"
    isPublished = $true
    isPrivate = $false
    locale = $locale
    path = $path
    tags = $tags
    title = $title
  }

  if (-not $result.pages.update.responseResult.succeeded) {
    throw "Wiki update failed: $($result.pages.update.responseResult.message)"
  }

  Write-Host ("wiki_action=updated path=/en/{0}" -f $result.pages.update.page.path)
} else {
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
    content = $content
    description = $description
    editor = "markdown"
    isPublished = $true
    isPrivate = $false
    locale = $locale
    path = $path
    tags = $tags
    title = $title
  }

  if (-not $result.pages.create.responseResult.succeeded) {
    throw "Wiki create failed: $($result.pages.create.responseResult.message)"
  }

  Write-Host ("wiki_action=created path=/en/{0}" -f $result.pages.create.page.path)
}

$searchQuery = @'
query ($query: String!, $locale: String!) {
  pages {
    search(query: $query, locale: $locale, path: "") {
      results { id path title }
    }
  }
}
'@

$search = Invoke-WikiGql -Query $searchQuery -Variables @{ query = "lab-registry01"; locale = "en" }
$count = @($search.pages.search.results).Count
Write-Host ("wiki_search_results={0}" -f $count)
if ($count -gt 0) {
  $search.pages.search.results | ForEach-Object {
    Write-Host ("wiki_result=/en/{0} title={1}" -f $_.path, $_.title)
  }
}
