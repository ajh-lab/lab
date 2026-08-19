$ErrorActionPreference = 'Stop'

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'This script must be run from an elevated PowerShell session.'
}

$logPath = Join-Path $PSScriptRoot 'vsm-bcd-change.log'
"=== $(Get-Date -Format o) Before ===" | Out-File -LiteralPath $logPath -Encoding utf8
& bcdedit /enum '{current}' | Out-File -LiteralPath $logPath -Encoding utf8 -Append

& bcdedit /set '{current}' vsmlaunchtype Off | Out-File -LiteralPath $logPath -Encoding utf8 -Append

"=== $(Get-Date -Format o) After ===" | Out-File -LiteralPath $logPath -Encoding utf8 -Append
& bcdedit /enum '{current}' | Out-File -LiteralPath $logPath -Encoding utf8 -Append
