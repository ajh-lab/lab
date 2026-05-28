param(
  [string]$EnvPath = "",
  [string]$InputPath = "",
  [switch]$FetchFresh,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Encode-Q {
  param([string]$Value)
  return [uri]::EscapeDataString($Value)
}

function Invoke-NetBox {
  param(
    [Parameter(Mandatory = $true)][ValidateSet('GET','POST','PATCH')][string]$Method,
    [Parameter(Mandatory = $true)][string]$Path,
    [object]$Body
  )

  $uri = "$script:NetBoxBase$Path"
  if ($null -ne $Body) {
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $script:NetBoxHeaders -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 30)
  }
  return Invoke-RestMethod -Method $Method -Uri $uri -Headers $script:NetBoxHeaders
}

function Ensure-Tag {
  param([string]$Name,[string]$Slug,[string]$Color)
  $existing = Invoke-NetBox -Method GET -Path "/api/extras/tags/?slug=$(Encode-Q $Slug)"
  if ($existing.count -gt 0) { return $existing.results[0].id }

  if ($WhatIf) { return 0 }

  $body = @{ name = $Name; slug = $Slug; color = $Color; description = 'Managed by UniFi automation sync' }
  return (Invoke-NetBox -Method POST -Path '/api/extras/tags/' -Body $body).id
}

function Ensure-Site {
  param([string]$Name,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/sites/?slug=$(Encode-Q $Slug)"
  if ($existing.count -gt 0) { return $existing.results[0].id }

  if ($WhatIf) { return 0 }

  $body = @{ name = $Name; slug = $Slug; status = 'active' }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/sites/' -Body $body).id
}

function Ensure-Manufacturer {
  param([string]$Name,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/manufacturers/?slug=$(Encode-Q $Slug)"
  if ($existing.count -gt 0) { return $existing.results[0].id }

  if ($WhatIf) { return 0 }

  return (Invoke-NetBox -Method POST -Path '/api/dcim/manufacturers/' -Body @{ name = $Name; slug = $Slug }).id
}

function Ensure-Role {
  param([string]$Name,[string]$Slug,[string]$Color)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/device-roles/?slug=$(Encode-Q $Slug)"
  if ($existing.count -gt 0) { return $existing.results[0].id }

  if ($WhatIf) { return 0 }

  return (Invoke-NetBox -Method POST -Path '/api/dcim/device-roles/' -Body @{ name = $Name; slug = $Slug; color = $Color }).id
}

function Ensure-DeviceType {
  param([int]$ManufacturerId,[string]$Model,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/device-types/?slug=$(Encode-Q $Slug)"
  if ($existing.count -gt 0) { return $existing.results[0].id }

  if ($WhatIf) { return 0 }

  $body = @{ manufacturer = $ManufacturerId; model = $Model; slug = $Slug }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/device-types/' -Body $body).id
}

function Ensure-Device {
  param(
    [string]$Name,
    [int]$DeviceTypeId,
    [int]$RoleId,
    [int]$SiteId,
    [string]$Description,
    [string]$Comments,
    [int[]]$TagIds
  )

  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/devices/?name=$(Encode-Q $Name)"
  $payload = @{
    name = $Name
    status = 'active'
    device_type = $DeviceTypeId
    role = $RoleId
    site = $SiteId
    description = $Description
    comments = $Comments
    tags = $TagIds
  }

  if ($existing.count -gt 0) {
    if (-not $WhatIf) { [void](Invoke-NetBox -Method PATCH -Path "/api/dcim/devices/$($existing.results[0].id)/" -Body $payload) }
    return [pscustomobject]@{ id = $existing.results[0].id; action = 'updated' }
  }

  if ($WhatIf) {
    return [pscustomobject]@{ id = 0; action = 'created' }
  }

  $created = Invoke-NetBox -Method POST -Path '/api/dcim/devices/' -Body $payload
  return [pscustomobject]@{ id = $created.id; action = 'created' }
}

function Ensure-DeviceInterface {
  param([int]$DeviceId,[string]$IfName)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/interfaces/?device_id=$DeviceId&name=$(Encode-Q $IfName)"
  if ($existing.count -gt 0) { return $existing.results[0].id }

  if ($WhatIf) { return 0 }

  return (Invoke-NetBox -Method POST -Path '/api/dcim/interfaces/' -Body @{ device = $DeviceId; name = $IfName; type = 'virtual'; enabled = $true }).id
}

function Ensure-IPAddress {
  param([string]$Address)
  $existing = Invoke-NetBox -Method GET -Path "/api/ipam/ip-addresses/?address=$(Encode-Q $Address)"
  if ($existing.count -gt 0) { return $existing.results[0] }

  if ($WhatIf) {
    return [pscustomobject]@{ id = 0; address = $Address; tags = @(); assigned_object_id = $null; assigned_object_type = $null }
  }

  return (Invoke-NetBox -Method POST -Path '/api/ipam/ip-addresses/' -Body @{ address = $Address; status = 'active' })
}

function Test-PrivateIPv4 {
  param([string]$Ip)
  try {
    $addr = [System.Net.IPAddress]::Parse($Ip)
    if ($addr.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) { return $false }
    $b = $addr.GetAddressBytes()
    if ($b[0] -eq 10) { return $true }
    if ($b[0] -eq 172 -and $b[1] -ge 16 -and $b[1] -le 31) { return $true }
    if ($b[0] -eq 192 -and $b[1] -eq 168) { return $true }
    return $false
  } catch {
    return $false
  }
}

function To-Slug {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return 'unknown' }
  $s = $Text.ToLowerInvariant() -replace '[^a-z0-9]+','-' -replace '-{2,}','-'
  $s = $s.Trim('-')
  if ([string]::IsNullOrWhiteSpace($s)) { return 'unknown' }
  if ($s.Length -gt 50) { $s = $s.Substring(0,50).Trim('-') }
  return $s
}

function Get-ClientIpPayload {
  param(
    [object]$Client,
    [int]$TagId,
    [string]$SiteName
  )

  $name = if ([string]::IsNullOrWhiteSpace($Client.name)) { $Client.macAddress } else { $Client.name }
  $comments = @(
    'Source: UniFi Integration API',
    "Site: $SiteName",
    "ClientType: $($Client.type)",
    "MAC: $($Client.macAddress)",
    "UniFiClientId: $($Client.id)",
    "UplinkDeviceId: $($Client.uplinkDeviceId)",
    "ConnectedAt: $($Client.connectedAt)"
  ) -join "`n"

  return @{
    status = 'active'
    description = "UniFi client: $name"
    comments = $comments
    tags = @($TagId)
  }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$secretModule = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $secretModule -Force

if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot '.env'
}
if ([string]::IsNullOrWhiteSpace($InputPath)) {
  $InputPath = Join-Path $repoRoot 'automation\unifi\data\unifi-inventory-latest.json'
}

$envMap = Get-LabEnvMap -Path $EnvPath
$netBoxToken = Resolve-LabSecret -Key 'NETBOX_ADMIN_API_TOKEN' -EnvMap $envMap
$script:UdmHost = $envMap['UDM_PRO_HOST']
if ([string]::IsNullOrWhiteSpace($script:UdmHost)) {
  $script:UdmHost = '192.168.1.1'
}

$script:NetBoxBase = 'http://192.168.1.80:32081'
$script:NetBoxHeaders = @{ Authorization = "Token $netBoxToken" }
[void](Invoke-NetBox -Method GET -Path '/api/status/')

if ($FetchFresh -or -not (Test-Path -LiteralPath $InputPath)) {
  $fetchScript = Join-Path $PSScriptRoot 'fetch-unifi-inventory.ps1'
  & powershell -NoProfile -ExecutionPolicy Bypass -File $fetchScript -EnvPath $EnvPath -OutputPath $InputPath
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch UniFi inventory"
  }
}

$inv = Get-Content -LiteralPath $InputPath -Raw | ConvertFrom-Json
$sites = @($inv.sites)

$tagUnifi = Ensure-Tag -Name 'unifi' -Slug 'unifi' -Color '2196f3'
$tagUnifiDevice = Ensure-Tag -Name 'unifi-device' -Slug 'unifi-device' -Color '3f51b5'
$tagUnifiClient = Ensure-Tag -Name 'unifi-client' -Slug 'unifi-client' -Color '00bcd4'
$siteId = Ensure-Site -Name 'HomeLab' -Slug 'homelab'
$mfrId = Ensure-Manufacturer -Name 'Ubiquiti' -Slug 'ubiquiti'
$roleId = Ensure-Role -Name 'Gateway Firewall' -Slug 'gateway-firewall' -Color 'ff5722'

$devicesCreated = 0
$devicesUpdated = 0
$clientsCreated = 0
$clientsUpdated = 0
$clientsSkipped = 0
$errors = New-Object System.Collections.Generic.List[string]

foreach ($site in $sites) {
  $siteName = if ([string]::IsNullOrWhiteSpace($site.name)) { $site.id } else { $site.name }

  foreach ($dev in @($site.devices)) {
    try {
      $devName = if ([string]::IsNullOrWhiteSpace($dev.name)) { "unifi-device-$($dev.id.Substring(0,8))" } else { $dev.name.Trim() }
      $model = if ([string]::IsNullOrWhiteSpace($dev.model)) { 'UniFi Device' } else { $dev.model.Trim() }
      $dtSlug = "ubiquiti-" + (To-Slug -Text $model)
      $dtId = Ensure-DeviceType -ManufacturerId $mfrId -Model $model -Slug $dtSlug

      $comments = @(
        'Source: UniFi Integration API',
        "Site: $siteName",
        "UniFiDeviceId: $($dev.id)",
        "MAC: $($dev.macAddress)",
        "State: $($dev.state)",
        "Firmware: $($dev.firmwareVersion)",
        "Features: $((@($dev.features.PSObject.Properties.Name) -join ', '))"
      ) -join "`n"

      $dRes = Ensure-Device -Name $devName -DeviceTypeId $dtId -RoleId $roleId -SiteId $siteId -Description "UniFi $model" -Comments $comments -TagIds @($tagUnifi, $tagUnifiDevice)
      if ($dRes.action -eq 'created') { $devicesCreated++ } else { $devicesUpdated++ }

      $ip = [string]$dev.ipAddress
      $isUdmModel = (($dev.model -as [string]) -match 'UDM') -or (($dev.name -as [string]) -match 'Dream Machine')
      if ((-not (Test-PrivateIPv4 -Ip $ip)) -and $isUdmModel -and (Test-PrivateIPv4 -Ip $script:UdmHost)) {
        $ip = $script:UdmHost
      }

      if (-not [string]::IsNullOrWhiteSpace($ip) -and (Test-PrivateIPv4 -Ip $ip)) {
        $ifId = Ensure-DeviceInterface -DeviceId $dRes.id -IfName 'mgmt0'
        $ipObj = Ensure-IPAddress -Address "$ip/32"

        if (-not $WhatIf) {
          $canAssign = ($null -eq $ipObj.assigned_object_id) -or ($ipObj.assigned_object_type -eq 'dcim.interface' -and [int]$ipObj.assigned_object_id -eq [int]$ifId)
          if ($canAssign) {
            $ipBody = @{ assigned_object_type = 'dcim.interface'; assigned_object_id = $ifId; tags = @($tagUnifi, $tagUnifiDevice); description = "UniFi device: $devName" }
            [void](Invoke-NetBox -Method PATCH -Path "/api/ipam/ip-addresses/$($ipObj.id)/" -Body $ipBody)
            [void](Invoke-NetBox -Method PATCH -Path "/api/dcim/devices/$($dRes.id)/" -Body @{ primary_ip4 = $ipObj.id })
          }
        }
      }
    } catch {
      $errors.Add("device $($dev.id): $($_.Exception.Message)")
    }
  }

  foreach ($client in @($site.clients)) {
    try {
      $ip = [string]$client.ipAddress
      if ([string]::IsNullOrWhiteSpace($ip) -or -not (Test-PrivateIPv4 -Ip $ip)) {
        $clientsSkipped++
        continue
      }

      $address = "$ip/32"
      $existing = Invoke-NetBox -Method GET -Path "/api/ipam/ip-addresses/?address=$(Encode-Q $address)"
      $payload = Get-ClientIpPayload -Client $client -TagId $tagUnifiClient -SiteName $siteName
      $payload.tags = @($tagUnifi, $tagUnifiClient)

      if ($existing.count -eq 0) {
        if (-not $WhatIf) {
          $createBody = @{ address = $address; status = 'active'; description = $payload.description; comments = $payload.comments; tags = $payload.tags }
          [void](Invoke-NetBox -Method POST -Path '/api/ipam/ip-addresses/' -Body $createBody)
        }
        $clientsCreated++
        continue
      }

      $ipObj = $existing.results[0]

      # Be conservative: do not overwrite assigned infrastructure addresses.
      if ($null -ne $ipObj.assigned_object_id) {
        $clientsSkipped++
        continue
      }

      if (-not $WhatIf) {
        [void](Invoke-NetBox -Method PATCH -Path "/api/ipam/ip-addresses/$($ipObj.id)/" -Body $payload)
      }
      $clientsUpdated++
    } catch {
      $errors.Add("client $($client.id): $($_.Exception.Message)")
    }
  }
}

Write-Host ("UniFi->NetBox sync complete. devices_created={0} devices_updated={1} clients_created={2} clients_updated={3} clients_skipped={4} errors={5}" -f $devicesCreated, $devicesUpdated, $clientsCreated, $clientsUpdated, $clientsSkipped, $errors.Count)
if ($errors.Count -gt 0) {
  Write-Host 'Error samples:'
  $errors | Select-Object -First 20 | ForEach-Object { Write-Host " - $_" }
}
