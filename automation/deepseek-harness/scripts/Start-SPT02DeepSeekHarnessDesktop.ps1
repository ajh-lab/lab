# Run in the interactive SPT02 helios account after Desktop installation.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'DeepSeekHarnessDesktopInstall'
$exe = Join-Path $env:LOCALAPPDATA 'Programs\DeepSeek Harness\DeepSeek Harness.exe'
$keyPath = Join-Path $env:LOCALAPPDATA 'DeepSeekHarness\litellm-key.dpapi'
foreach ($path in @($exe, $keyPath)) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Required path missing: $path" }
}
New-Item -ItemType Directory -Force -Path $root | Out-Null
$env:DSH_HOME = Join-Path $env:USERPROFILE '.dsh-lab-desktop'
$env:DSH_TELEMETRY_MODE = 'DISABLED'
$secureKey = ConvertTo-SecureString (Get-Content -LiteralPath $keyPath -Raw)
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
try {
  $env:LITELLM_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
try {
  # Windows PowerShell launches GUI executables asynchronously with &.
  # Keep the redirecting parent alive until Desktop and its children exit.
  $process = Start-Process -FilePath $exe -WorkingDirectory $env:USERPROFILE `
    -WindowStyle Normal -Wait -PassThru `
    -RedirectStandardOutput (Join-Path $root "desktop-$stamp-stdout.log") `
    -RedirectStandardError (Join-Path $root "desktop-$stamp-stderr.log")
  if ($process.ExitCode -ne 0) { throw "DeepSeek Harness exited with code $($process.ExitCode)" }
} finally {
  Remove-Item Env:\LITELLM_API_KEY -ErrorAction SilentlyContinue
}
