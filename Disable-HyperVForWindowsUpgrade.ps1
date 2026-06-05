$ErrorActionPreference = 'Continue'
$LogPath = Join-Path $PSScriptRoot 'Disable-HyperVForWindowsUpgrade.log'

function Write-Log {
    param([string]$Message)
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    $line | Tee-Object -FilePath $LogPath -Append
}

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
Write-Log 'Starting Hyper-V disablement for Windows upgrade retry.'
Write-Log "Running elevated: $($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"

Write-Log 'Current BCD entry:'
& bcdedit.exe /enum '{current}' 2>&1 | ForEach-Object { Write-Log "bcdedit before: $_" }

$features = @(
    'Microsoft-Hyper-V-All',
    'HypervisorPlatform',
    'VirtualMachinePlatform',
    'Containers',
    'Containers-DisposableClientVM'
)

Write-Log 'Current optional feature states:'
foreach ($feature in $features) {
    $state = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
    if ($state) {
        Write-Log "$feature before: $($state.State)"
    } else {
        Write-Log "$feature before: not found"
    }
}

foreach ($feature in $features) {
    $state = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
    if ($state -and $state.State -eq 'Enabled') {
        Write-Log "Disabling optional feature: $feature"
        Disable-WindowsOptionalFeature -Online -FeatureName $feature -NoRestart 2>&1 |
            ForEach-Object { Write-Log "Disable ${feature}: $_" }
    } else {
        Write-Log "Skipping optional feature: $feature"
    }
}

$services = @('gvm')
foreach ($service in $services) {
    $item = Get-ItemProperty -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Services\$service" -ErrorAction SilentlyContinue
    if ($item) {
        Write-Log "$service before: Start=$($item.Start), ImagePath=$($item.ImagePath)"
        Write-Log "Disabling service: $service"
        & sc.exe config $service start= disabled 2>&1 | ForEach-Object { Write-Log "sc ${service}: $_" }
    } else {
        Write-Log "$service not found"
    }
}

Write-Log 'Setting hypervisorlaunchtype Off.'
& bcdedit.exe /set hypervisorlaunchtype off 2>&1 | ForEach-Object { Write-Log "bcdedit set: $_" }

Write-Log 'Feature states after requested changes:'
foreach ($feature in $features) {
    $state = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
    if ($state) {
        Write-Log "$feature after: $($state.State)"
    }
}

Write-Log 'BCD entry after requested changes:'
& bcdedit.exe /enum '{current}' 2>&1 | ForEach-Object { Write-Log "bcdedit after: $_" }

Write-Log 'Done. Reboot is required before retrying the Windows 11 upgrade.'
