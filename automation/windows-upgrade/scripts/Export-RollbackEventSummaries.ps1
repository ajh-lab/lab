$ErrorActionPreference = 'Continue'
$Base = 'C:\$WINDOWS.~BT\Sources\Rollback\evtlogs'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$OutputDir = Join-Path $RepoRoot 'tmp\windows-upgrade'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Out = Join-Path $OutputDir 'RollbackEventSummary.txt'

function Write-Out {
    param([string]$Message)
    $Message | Out-File -LiteralPath $Out -Append -Encoding utf8
}

if (Test-Path -LiteralPath $Out) {
    Remove-Item -LiteralPath $Out -Force
}

Write-Out "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Out "Running elevated: $((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"

$logs = @(
    'System.evtx',
    'Setup.evtx',
    'Application.evtx',
    'Microsoft-Windows-Kernel-PnP%4Configuration.evtx',
    'Microsoft-Windows-Kernel-PnP%4Device Management.evtx',
    'Microsoft-Windows-Kernel-Boot%4Operational.evtx',
    'Microsoft-Windows-Kernel-Dump%4Operational.evtx',
    'Microsoft-Windows-DeviceSetupManager%4Admin.evtx',
    'Microsoft-Windows-DeviceSetupManager%4Operational.evtx',
    'Microsoft-Windows-CodeIntegrity%4Operational.evtx',
    'Microsoft-Windows-Hyper-V-VmSwitch-Operational.evtx',
    'Microsoft-Windows-Hyper-V-Hypervisor-Admin.evtx'
)

foreach ($log in $logs) {
    $path = Join-Path $Base $log
    Write-Out ''
    Write-Out "===== $log ====="
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Out 'Missing'
        continue
    }

    try {
        $events = Get-WinEvent -Path $path -ErrorAction Stop |
            Where-Object { $_.Level -in 1,2,3 } |
            Select-Object -First 80
        foreach ($event in $events) {
            $message = ($event.Message -replace "`r?`n", ' ') -replace '\s+', ' '
            Write-Out ("{0:u} Id={1} Level={2} Provider={3} Message={4}" -f $event.TimeCreated, $event.Id, $event.LevelDisplayName, $event.ProviderName, $message)
        }
    } catch {
        Write-Out "ERROR: $($_.Exception.Message)"
    }
}
