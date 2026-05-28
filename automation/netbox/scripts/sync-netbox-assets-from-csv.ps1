param(
  [string]$CsvPath = "",
  [string]$EnvPath = "",
  [string]$NetBoxBaseUrl = "http://192.168.1.80:32081",
  [switch]$WhatIf,
  [switch]$IncludeHostnameOnly
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
    [hashtable]$Headers,
    [object]$Body
  )

  $uri = "$script:BaseUrl$Path"
  if ($null -ne $Body) {
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $Headers -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 30)
  }
  return Invoke-RestMethod -Method $Method -Uri $uri -Headers $Headers
}

function Ensure-Tag {
  param([string]$Name,[string]$Slug,[string]$Color)
  $existing = Invoke-NetBox -Method GET -Path "/api/extras/tags/?slug=$(Encode-Q $Slug)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ name = $Name; slug = $Slug; color = $Color; description = 'Imported/managed by automation scripts' }
  return (Invoke-NetBox -Method POST -Path '/api/extras/tags/' -Headers $script:Headers -Body $body).id
}

function Ensure-Site {
  param([string]$Name,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/sites/?slug=$(Encode-Q $Slug)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ name = $Name; slug = $Slug; status = 'active' }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/sites/' -Headers $script:Headers -Body $body).id
}

function Ensure-Manufacturer {
  param([string]$Name,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/manufacturers/?slug=$(Encode-Q $Slug)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ name = $Name; slug = $Slug }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/manufacturers/' -Headers $script:Headers -Body $body).id
}

function Ensure-DeviceRole {
  param([string]$Name,[string]$Slug,[string]$Color)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/device-roles/?slug=$(Encode-Q $Slug)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ name = $Name; slug = $Slug; color = $Color }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/device-roles/' -Headers $script:Headers -Body $body).id
}

function Ensure-DeviceType {
  param([int]$ManufacturerId,[string]$Model,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/device-types/?slug=$(Encode-Q $Slug)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ manufacturer = $ManufacturerId; model = $Model; slug = $Slug }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/device-types/' -Headers $script:Headers -Body $body).id
}

function Ensure-ClusterType {
  param([string]$Name,[string]$Slug)
  $existing = Invoke-NetBox -Method GET -Path "/api/virtualization/cluster-types/?slug=$(Encode-Q $Slug)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ name = $Name; slug = $Slug }
  return (Invoke-NetBox -Method POST -Path '/api/virtualization/cluster-types/' -Headers $script:Headers -Body $body).id
}

function Ensure-Cluster {
  param([string]$Name,[int]$TypeId,[int]$SiteId)
  $existing = Invoke-NetBox -Method GET -Path "/api/virtualization/clusters/?name=$(Encode-Q $Name)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ name = $Name; type = $TypeId; status = 'active'; scope_type = 'dcim.site'; scope_id = $SiteId }
  return (Invoke-NetBox -Method POST -Path '/api/virtualization/clusters/' -Headers $script:Headers -Body $body).id
}

function Get-OrCreate-Device {
  param(
    [string]$Name,
    [int]$DeviceTypeId,
    [int]$RoleId,
    [int]$SiteId,
    [string]$Description,
    [string]$Comments,
    [int[]]$TagIds
  )

  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/devices/?name=$(Encode-Q $Name)" -Headers $script:Headers
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
    $id = $existing.results[0].id
    [void](Invoke-NetBox -Method PATCH -Path "/api/dcim/devices/$id/" -Headers $script:Headers -Body $payload)
    return @{ id = $id; action = 'updated' }
  }

  $created = Invoke-NetBox -Method POST -Path '/api/dcim/devices/' -Headers $script:Headers -Body $payload
  return @{ id = $created.id; action = 'created' }
}

function Get-OrCreate-DeviceInterface {
  param([int]$DeviceId,[string]$Name)
  $existing = Invoke-NetBox -Method GET -Path "/api/dcim/interfaces/?device_id=$DeviceId&name=$(Encode-Q $Name)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ device = $DeviceId; name = $Name; type = 'virtual'; enabled = $true }
  return (Invoke-NetBox -Method POST -Path '/api/dcim/interfaces/' -Headers $script:Headers -Body $body).id
}

function Get-OrCreate-VM {
  param(
    [string]$Name,
    [int]$ClusterId,
    [string]$Description,
    [string]$Comments,
    [int[]]$TagIds
  )

  $existing = Invoke-NetBox -Method GET -Path "/api/virtualization/virtual-machines/?name=$(Encode-Q $Name)" -Headers $script:Headers
  $payload = @{
    name = $Name
    status = 'active'
    cluster = $ClusterId
    description = $Description
    comments = $Comments
    tags = $TagIds
  }

  if ($existing.count -gt 0) {
    $id = $existing.results[0].id
    [void](Invoke-NetBox -Method PATCH -Path "/api/virtualization/virtual-machines/$id/" -Headers $script:Headers -Body $payload)
    return @{ id = $id; action = 'updated' }
  }

  $created = Invoke-NetBox -Method POST -Path '/api/virtualization/virtual-machines/' -Headers $script:Headers -Body $payload
  return @{ id = $created.id; action = 'created' }
}

function Get-OrCreate-VMInterface {
  param([int]$VMId,[string]$Name)
  $existing = Invoke-NetBox -Method GET -Path "/api/virtualization/interfaces/?virtual_machine_id=$VMId&name=$(Encode-Q $Name)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ virtual_machine = $VMId; name = $Name; enabled = $true }
  return (Invoke-NetBox -Method POST -Path '/api/virtualization/interfaces/' -Headers $script:Headers -Body $body).id
}

function Ensure-IP {
  param([string]$Address)
  $existing = Invoke-NetBox -Method GET -Path "/api/ipam/ip-addresses/?address=$(Encode-Q $Address)" -Headers $script:Headers
  if ($existing.count -gt 0) { return $existing.results[0].id }
  $body = @{ address = $Address; status = 'active' }
  return (Invoke-NetBox -Method POST -Path '/api/ipam/ip-addresses/' -Headers $script:Headers -Body $body).id
}

function Classify-Row {
  param([object]$Row)

  $text = @($Row.Name,$Row.Hostname,$Row.Description,$Row.Notes) -join ' '
  $l = $text.ToLowerInvariant()

  if ($l -match 'cisco' -or $l -match 'catalyst' -or $l -match 'switch') {
    return @{
      assetType = 'device'
      roleSlug = 'network-switch'
      roleName = 'Network Switch'
      roleColor = 'ff9800'
      manufacturerSlug = 'cisco'
      manufacturerName = 'Cisco'
      deviceTypeSlug = 'catalyst-2960x-48poe'
      deviceTypeModel = 'Catalyst 2960X-48PoE'
      interfaceName = 'Vlan1'
    }
  }

  if ($l -match 'vmware host' -or $l -match 'workstation') {
    return @{
      assetType = 'device'
      roleSlug = 'hypervisor-host'
      roleName = 'Hypervisor Host'
      roleColor = '9c27b0'
      manufacturerSlug = 'generic'
      manufacturerName = 'Generic'
      deviceTypeSlug = 'windows-workstation-host'
      deviceTypeModel = 'Windows Workstation Host'
      interfaceName = 'mgmt0'
    }
  }

  if ($l -match 'rancherweb01' -or $l -match 'virtual machine' -or $l -match 'ubuntu vm' -or $l -match 'vm running' -or $l -match 'running rancher server') {
    return @{
      assetType = 'vm'
      interfaceName = 'eth0'
      clusterName = 'homelab-vms'
    }
  }

  if ($l -match 'worker' -or $l -match 'wknd') {
    return @{
      assetType = 'device'
      roleSlug = 'k3s-worker'
      roleName = 'k3s Worker'
      roleColor = '4caf50'
      manufacturerSlug = 'raspberry-pi'
      manufacturerName = 'Raspberry Pi'
      deviceTypeSlug = 'raspberry-pi-5'
      deviceTypeModel = 'Raspberry Pi 5'
      interfaceName = 'eth0'
    }
  }

  if ($l -match 'master' -or $l -match 'control-plane' -or $l -match 'mstr') {
    return @{
      assetType = 'device'
      roleSlug = 'k3s-control-plane'
      roleName = 'k3s Control Plane'
      roleColor = '3f51b5'
      manufacturerSlug = 'raspberry-pi'
      manufacturerName = 'Raspberry Pi'
      deviceTypeSlug = 'raspberry-pi-5'
      deviceTypeModel = 'Raspberry Pi 5'
      interfaceName = 'eth0'
    }
  }

  return @{
    assetType = 'device'
    roleSlug = 'infra-node'
    roleName = 'Infrastructure Node'
    roleColor = '607d8b'
    manufacturerSlug = 'generic'
    manufacturerName = 'Generic'
    deviceTypeSlug = 'generic-device'
    deviceTypeModel = 'Generic Device'
    interfaceName = 'mgmt0'
  }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$secretModule = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $secretModule -Force

if ([string]::IsNullOrWhiteSpace($CsvPath)) { $CsvPath = Join-Path $repoRoot 'network_devices.csv' }
if ([string]::IsNullOrWhiteSpace($EnvPath)) { $EnvPath = Join-Path $repoRoot '.env' }

if (-not (Test-Path -LiteralPath $CsvPath)) { throw "CSV not found: $CsvPath" }

$envMap = Get-LabEnvMap -Path $EnvPath
$token = Resolve-LabSecret -Key 'NETBOX_ADMIN_API_TOKEN' -EnvMap $envMap

$script:BaseUrl = $NetBoxBaseUrl
$script:Headers = @{ Authorization = "Token $token" }

[void](Invoke-NetBox -Method GET -Path '/api/ipam/ip-addresses/?limit=1' -Headers $script:Headers)

$allRows = Import-Csv -LiteralPath $CsvPath | Where-Object { $_.UsableHost -eq 'TRUE' -and -not [string]::IsNullOrWhiteSpace($_.IPAddress) }
if ($IncludeHostnameOnly) {
  $assetRows = $allRows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Name) -or -not [string]::IsNullOrWhiteSpace($_.Hostname) }
} else {
  $assetRows = $allRows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Name) }
}

$tagId = $null
$siteId = $null
$clusterTypeId = $null
$clusterId = $null
if (-not $WhatIf) {
  $tagId = Ensure-Tag -Name 'network-csv-import' -Slug 'network-csv-import' -Color '607d8b'
  $siteId = Ensure-Site -Name 'HomeLab' -Slug 'homelab'
  $clusterTypeId = Ensure-ClusterType -Name 'KVM' -Slug 'kvm'
  $clusterId = Ensure-Cluster -Name 'homelab-vms' -TypeId $clusterTypeId -SiteId $siteId
}

$devicesCreated = 0
$devicesUpdated = 0
$vmsCreated = 0
$vmsUpdated = 0
$linksUpdated = 0
$failed = 0
$errors = New-Object System.Collections.Generic.List[string]

foreach ($row in $assetRows) {
  try {
    $name = if (-not [string]::IsNullOrWhiteSpace($row.Name)) { $row.Name.Trim() } elseif (-not [string]::IsNullOrWhiteSpace($row.Hostname)) { $row.Hostname.Trim() } else { "ip-$($row.IPAddress.Replace('.','-'))" }
    $classification = Classify-Row -Row $row

    $ip = $row.IPAddress.Trim()
    $address = if ($ip.Contains(':')) { "$ip/128" } else { "$ip/32" }

    $description = $row.Description
    if ([string]::IsNullOrWhiteSpace($description)) { $description = "Imported from network_devices.csv" }

    $commentsLines = @(
      'Source: network_devices.csv',
      "Reachable: $($row.Reachable)",
      "MgmtReachable: $($row.MgmtReachable)",
      "CheckedAt: $($row.CheckedAt)",
      "LastUpdated: $($row.LastUpdated)"
    )
    if (-not [string]::IsNullOrWhiteSpace($row.Notes)) { $commentsLines += "Notes: $($row.Notes.Trim())" }
    if (-not [string]::IsNullOrWhiteSpace($row.CredentialRef)) { $commentsLines += "CredentialRef: $($row.CredentialRef.Trim())" }
    $comments = ($commentsLines -join "`n")

    if ($WhatIf) {
      Write-Host "[WhatIf] Would sync $name ($address) as $($classification.assetType)"
      continue
    }

    $ipId = Ensure-IP -Address $address

    if ($classification.assetType -eq 'vm') {
      $vm = Get-OrCreate-VM -Name $name -ClusterId $clusterId -Description $description -Comments $comments -TagIds @($tagId)
      if ($vm.action -eq 'created') { $vmsCreated++ } else { $vmsUpdated++ }

      $vmIfId = Get-OrCreate-VMInterface -VMId $vm.id -Name $classification.interfaceName
      $ipPayload = @{
        dns_name = if (-not [string]::IsNullOrWhiteSpace($row.Hostname)) { $row.Hostname.Trim() } else { '' }
        assigned_object_type = 'virtualization.vminterface'
        assigned_object_id = $vmIfId
      }
      [void](Invoke-NetBox -Method PATCH -Path "/api/ipam/ip-addresses/$ipId/" -Headers $script:Headers -Body $ipPayload)
      [void](Invoke-NetBox -Method PATCH -Path "/api/virtualization/virtual-machines/$($vm.id)/" -Headers $script:Headers -Body @{ primary_ip4 = $ipId })
      $linksUpdated++
    }
    else {
      $manufacturerId = Ensure-Manufacturer -Name $classification.manufacturerName -Slug $classification.manufacturerSlug
      $roleId = Ensure-DeviceRole -Name $classification.roleName -Slug $classification.roleSlug -Color $classification.roleColor
      $deviceTypeId = Ensure-DeviceType -ManufacturerId $manufacturerId -Model $classification.deviceTypeModel -Slug $classification.deviceTypeSlug

      $device = Get-OrCreate-Device -Name $name -DeviceTypeId $deviceTypeId -RoleId $roleId -SiteId $siteId -Description $description -Comments $comments -TagIds @($tagId)
      if ($device.action -eq 'created') { $devicesCreated++ } else { $devicesUpdated++ }

      $ifId = Get-OrCreate-DeviceInterface -DeviceId $device.id -Name $classification.interfaceName
      $ipPayload = @{
        dns_name = if (-not [string]::IsNullOrWhiteSpace($row.Hostname)) { $row.Hostname.Trim() } else { '' }
        assigned_object_type = 'dcim.interface'
        assigned_object_id = $ifId
      }
      [void](Invoke-NetBox -Method PATCH -Path "/api/ipam/ip-addresses/$ipId/" -Headers $script:Headers -Body $ipPayload)
      [void](Invoke-NetBox -Method PATCH -Path "/api/dcim/devices/$($device.id)/" -Headers $script:Headers -Body @{ primary_ip4 = $ipId })
      $linksUpdated++
    }
  }
  catch {
    $failed++
    $detail = $_.Exception.Message
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
      $detail = "$detail | $($_.ErrorDetails.Message)"
    }
    $errors.Add("$($row.IPAddress): $detail")
  }
}

Write-Host "Asset sync complete. device_created=$devicesCreated device_updated=$devicesUpdated vm_created=$vmsCreated vm_updated=$vmsUpdated links_updated=$linksUpdated failed=$failed total=$($assetRows.Count)"
if ($errors.Count -gt 0) {
  Write-Host 'Failures:'
  $errors | Select-Object -First 20 | ForEach-Object { Write-Host " - $_" }
}
