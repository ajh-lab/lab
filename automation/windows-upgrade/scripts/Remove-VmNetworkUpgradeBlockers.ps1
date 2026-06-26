$ErrorActionPreference = 'Continue'

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Error 'Run this script from an elevated PowerShell session.'
  exit 1
}

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$OutputDir = Join-Path $RepoRoot 'tmp\windows-upgrade'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$logPath = Join-Path $OutputDir 'Remove-VmNetworkUpgradeBlockers.log'
Start-Transcript -Path $logPath -Force | Out-Null

Write-Host 'Stopping VMware and VirtualBox services...'
$serviceNames = @(
  'VBoxSDS',
  'VMAuthdService',
  'VMnetDHCP',
  'VMware NAT Service',
  'VMUSBArbService',
  'VmwareAutostartService'
)

foreach ($name in $serviceNames) {
  $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
  if ($svc) {
    Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
    Set-Service -Name $name -StartupType Disabled -ErrorAction SilentlyContinue
  }
}

Write-Host 'Disabling VMware and VirtualBox network filter bindings...'
$bindingIds = @('oracle_VBoxNetLwf', 'vmware_bridge')
foreach ($componentId in $bindingIds) {
  Get-NetAdapterBinding -AllBindings -IncludeHidden -ComponentID $componentId -ErrorAction SilentlyContinue |
    Where-Object Enabled |
    ForEach-Object {
      Disable-NetAdapterBinding -Name $_.Name -ComponentID $_.ComponentID -ErrorAction SilentlyContinue
    }
}

Write-Host 'Removing VMware and VirtualBox virtual network adapters...'
$deviceInstanceIds = @(
  'ROOT\NET\0000',
  'ROOT\VMWARE\0000',
  'ROOT\VMWARE\0001'
)

foreach ($instanceId in $deviceInstanceIds) {
  pnputil /remove-device $instanceId
}

Write-Host 'Removing VMware and VirtualBox network driver packages...'
$driverPackages = @(
  'oem22.inf', # VirtualBox Host-Only Ethernet Adapter
  'oem32.inf', # VirtualBox NDIS6 Bridged Networking Driver
  'oem47.inf', # VMware virtual ethernet adapters
  'oem46.inf'  # VMware Bridge Protocol
)

foreach ($driver in $driverPackages) {
  pnputil /delete-driver $driver /uninstall /force
}

Write-Host 'Disabling remaining VMware and VirtualBox kernel drivers...'
$driverServiceNames = @(
  'VBoxNetLwf',
  'VBoxSup',
  'VBoxUSBMon',
  'hcmon',
  'vmci',
  'VMnetBridge',
  'VMnetuserif',
  'vmusb',
  'vmx86'
)

foreach ($name in $driverServiceNames) {
  sc.exe stop $name | Out-Host
  sc.exe config $name start= disabled | Out-Host
}

Write-Host 'Removing remaining VMware and VirtualBox PnP devices and driver packages...'
pnputil /remove-device 'ROOT\VMWVMCIHOSTDEV\0000'

$extraDriverPackages = @(
  'oem11.inf', # VirtualBox USB driver
  'oem48.inf', # VMware VMCI
  'oem38.inf'  # VMware USB
)

foreach ($driver in $extraDriverPackages) {
  pnputil /delete-driver $driver /uninstall /force
}

Write-Host 'Current VMware/VirtualBox network adapters:'
Get-NetAdapter -IncludeHidden |
  Where-Object { $_.Name -match 'VMware|VirtualBox|VBox' -or $_.InterfaceDescription -match 'VMware|VirtualBox|VBox' } |
  Select-Object Name, InterfaceDescription, Status, ifIndex |
  Format-Table -AutoSize

Write-Host 'Current VMware/VirtualBox PnP devices:'
Get-PnpDevice -PresentOnly |
  Where-Object { $_.FriendlyName -match 'VMware|VirtualBox|VBox' -or $_.InstanceId -match 'VMWARE|VBOX|ORACLE' } |
  Select-Object Status, Class, FriendlyName, InstanceId |
  Format-Table -Wrap -AutoSize

Write-Host "Log written to $logPath"
Stop-Transcript | Out-Null
