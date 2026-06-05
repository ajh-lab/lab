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

$path = "services/spt01"
$locale = "en"
$tags = @("services", "gaming", "spt", "fika", "ubuntu", "vm")
$title = "SPT/Fika Server (spt01)"
$description = "Windows 10 VM for hosting SPT/Fika Escape From Tarkov co-op service"
$content = @'
# SPT/Fika Server (spt01)

## Overview
- Hostname: `spt01`
- Role: SPT/Fika server host
- Platform: Windows 10 VM
- IP: `192.168.1.85`
- Gateway: `192.168.1.1`
- Network: `192.168.1.0/24`
- NetBox object: VM in `homelab-vms`

## Credentials
- Source of truth: OpenBao path `secret/homelab/vms/spt01`
- Bootstrap `.env` references: `SPT01_HOST`, `SPT01_USER`, `SPT01_PASSWORD`
- Do not store passwords in Wiki.js, Git, NetBox comments, or command logs.

## Network Access
- Intended access pattern: remote users connect through UDM WireGuard VPN.
- Keep SPT/Fika service ports scoped to this host only.
- Do not expose SPT/Fika directly with WAN port forwards unless explicitly approved.
- Current management status: WinRM was not reachable from the lab workstation during the 2026-06-05 automation run.

## Planned Service
- SPT backend and Fika co-op hosting.
- Expected service ports to validate before firewall rules:
  - `6969/tcp`
  - `25565/udp`

## Current Build State
- `C:\SPT` was copied from the gaming workstation to `SPT01`.
- Original EFT files were copied to `C:\Battlestate Games\Escape From Tarkov`.
- Fika Installer `v1.1.7` was downloaded to `C:\SPT\Fika-Installer.exe`.
- Fika server/client components were installed into `C:\SPT`.
- .NET 9 runtime and ASP.NET Core 9 runtime were installed for `SPT.Server.exe`.
- Fika config was generated and set to advertise `https://192.168.1.85:6969`.
- Fika headless installation completed from `C:\SPT`.
- Startup tasks:
  - `SPT01-SPT-Server` starts `C:\SPT\SPT\SPT.Server.exe` at `helios` logon.
  - `SPT01-Fika-Headless` runs `C:\SPT\automation\Start-FikaHeadlessAfterServer.ps1`, which waits for `https://127.0.0.1:6969/client/game/version/validate` before launching `C:\SPT\FikaHeadlessManager.exe`.
- Current validation: the delayed helper starts after SPT is ready, but Fika currently reports an empty headless list at `/fika/headless/get`; the manager appears to exit without leaving an `EscapeFromTarkov` headless process running.
- Baseline mod cleanup completed:
  - Active BepInEx plugins: `Fika`, `spt`
  - Active server mods: `fika-server`
  - Disabled copied desktop mods path: `C:\SPT\_disabled-headless\baseline-20260605-141312`
- Operator control script:
  - Script: `C:\SPT\automation\Manage-SPT01-Fika.ps1`
  - Non-interactive action script: `C:\SPT\automation\Invoke-SPT01-FikaAction.ps1 -Action Status|Start|Stop|Restart`
  - Launcher: `C:\Users\helios\Desktop\SPT01 Fika Server Manager.lnk`
  - Menu options: start, stop, restart, refresh status, exit.
  - Repo sources:
    - `automation/spt01/Manage-SPT01-Fika.ps1`
    - `automation/spt01/Invoke-SPT01-FikaAction.ps1`
- OpenSSH/Hermes access:
  - OpenSSH Server is installed on `SPT01` and listens on `22/tcp`.
  - Default SSH shell is Windows PowerShell 5.1.
  - `helios@ai-workstation-evox2` is authorized for key-based SSH to `helios@192.168.1.85`.
  - Hermes command pattern from AI workstation: `ssh helios@192.168.1.85 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT01-FikaAction.ps1 -Action Status"`

## Setup Notes
- Static IP should be reserved in UniFi for the VM MAC address.
- If WinRM is not reachable, verify the VM virtual NIC is connected to the LAN-backed port group/network, confirm the Windows static address is applied, set the network profile to Private, and enable PowerShell Remoting.
- Once reachable, install service prerequisites, deploy SPT/Fika files, configure the server to listen on `192.168.1.85`, and create a Windows scheduled task or service wrapper for persistence.
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

$existingSearch = Invoke-WikiGql -Query $searchExistingQuery -Variables @{ query = "spt01"; locale = $locale }
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
