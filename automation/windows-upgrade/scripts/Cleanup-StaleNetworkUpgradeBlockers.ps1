$ErrorActionPreference = 'Continue'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$OutputDir = Join-Path $RepoRoot 'tmp\windows-upgrade'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$LogPath = Join-Path $OutputDir 'Cleanup-StaleNetworkUpgradeBlockers.log'

function Write-Log {
    param([string]$Message)
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    $line | Tee-Object -FilePath $LogPath -Append
}

Write-Log 'Starting stale Windows upgrade network component cleanup.'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
Write-Log "Running elevated: $($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"

$components = @(
    'oracle_vboxnetlwf',
    'vmware_bridge'
)

foreach ($component in $components) {
    Write-Log "Uninstalling NetCfg component: $component"
    $output = & netcfg.exe -v -u $component 2>&1
    foreach ($line in $output) {
        Write-Log "netcfg ${component}: $line"
    }
    Write-Log "netcfg ${component} exit code: $LASTEXITCODE"
}

$services = @(
    'VBoxNetLwf',
    'VMnetBridge'
)

foreach ($service in $services) {
    $existing = Get-Item -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Services\$service" -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Log "Deleting stale service key via sc.exe: $service"
        $output = & sc.exe delete $service 2>&1
        foreach ($line in $output) {
            Write-Log "sc ${service}: $line"
        }
        Write-Log "sc ${service} exit code: $LASTEXITCODE"
    } else {
        Write-Log "Service key already absent: $service"
    }
}

Write-Log 'Current matching NetCfg components after cleanup:'
$netcfg = & netcfg.exe -s n 2>&1
$netcfg | Where-Object { $_ -match 'oracle|vbox|vmware|bridge' } | ForEach-Object {
    Write-Log "netcfg remaining: $_"
}

Write-Log 'Cleanup complete. Reboot is recommended before the next Windows 11 upgrade attempt.'
