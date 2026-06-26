$ErrorActionPreference = 'Continue'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$OutputDir = Join-Path $RepoRoot 'tmp\windows-upgrade'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Out = Join-Path $OutputDir 'UpgradeFeatureState.txt'

if (Test-Path -LiteralPath $Out) {
    Remove-Item -LiteralPath $Out -Force
}

function Write-Out {
    param([string]$Message)
    $Message | Out-File -LiteralPath $Out -Append -Encoding utf8
}

Write-Out "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Out "Running elevated: $((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))"

Write-Out ''
Write-Out '===== BCD ====='
& bcdedit.exe /enum '{current}' 2>&1 | ForEach-Object { Write-Out $_ }

Write-Out ''
Write-Out '===== Optional Features ====='
Get-WindowsOptionalFeature -Online |
    Where-Object { $_.FeatureName -match 'Hyper|VirtualMachine|Containers|Subsystem|Sandbox|Platform' } |
    Sort-Object FeatureName |
    ForEach-Object { Write-Out ("{0} = {1}" -f $_.FeatureName, $_.State) }

Write-Out ''
Write-Out '===== Relevant Services ====='
$serviceNames = @(
    'gvm',
    'hvservice',
    'VMSP',
    'VMSMP',
    'VMSNPXY',
    'VMSNPXYMP',
    'VMSVSF',
    'VMSVSP',
    'vmcompute',
    'vmms',
    'hns'
)

foreach ($name in $serviceNames) {
    $item = Get-ItemProperty -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Services\$name" -ErrorAction SilentlyContinue
    if ($item) {
        Write-Out ("{0}: DisplayName='{1}' Start={2} Type={3} ImagePath='{4}'" -f $name, $item.DisplayName, $item.Start, $item.Type, $item.ImagePath)
    }
}
