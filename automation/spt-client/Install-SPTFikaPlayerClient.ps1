param(
  [ValidateSet("Interactive", "Setup", "Mods", "Restore", "Package")]
  [string]$Mode = "Interactive",
  [string]$SptRoot = "",
  [string]$ModPackagePath = "",
  [string]$ServerUrl = "https://192.168.1.86:6969",
  [switch]$SkipPrerequisites,
  [switch]$NoElevate
)

$ErrorActionPreference = "Stop"

$Script:StepIndex = 0
$Script:StepTotal = 8

function Write-UiLine {
  param(
    [string]$Message = "",
    [ConsoleColor]$Color = [ConsoleColor]::Gray
  )
  Write-Host $Message -ForegroundColor $Color
}

function Write-UiHeader {
  Clear-Host
  Write-Host ""
  Write-Host "  SPT / Fika Player Client Setup" -ForegroundColor Cyan
  Write-Host "  --------------------------------" -ForegroundColor DarkCyan
  Write-Host "  Installs the local SPT/Fika client surface needed to connect to SPT02." -ForegroundColor Gray
  Write-Host "  Server URL: $ServerUrl" -ForegroundColor Gray
  Write-Host ""
}

function Update-SetupProgress {
  param(
    [string]$Status,
    [int]$Step = -1
  )
  if ($Step -ge 0) {
    $Script:StepIndex = $Step
  } else {
    $Script:StepIndex++
  }
  $percent = [Math]::Min(100, [Math]::Round(($Script:StepIndex / $Script:StepTotal) * 100))
  Write-Progress -Activity "SPT/Fika player setup" -Status $Status -PercentComplete $percent
  Write-UiLine ("[{0}/{1}] {2}" -f $Script:StepIndex, $Script:StepTotal, $Status) Cyan
}

function Read-RequiredValue {
  param(
    [string]$Prompt,
    [string]$Default = ""
  )
  while ($true) {
    if ([string]::IsNullOrWhiteSpace($Default)) {
      $value = Read-Host $Prompt
    } else {
      $value = Read-Host "$Prompt [$Default]"
      if ([string]::IsNullOrWhiteSpace($value)) {
        $value = $Default
      }
    }
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value.Trim('"')
    }
    Write-UiLine "A value is required." Yellow
  }
}

function Read-OptionalValue {
  param(
    [string]$Prompt,
    [string]$Default = ""
  )
  if ([string]::IsNullOrWhiteSpace($Default)) {
    $value = Read-Host $Prompt
  } else {
    $value = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($value)) {
      $value = $Default
    }
  }
  return $value.Trim('"')
}

function Read-YesNo {
  param(
    [string]$Prompt,
    [bool]$DefaultYes = $true
  )
  $suffix = "Y/n"
  if (-not $DefaultYes) {
    $suffix = "y/N"
  }
  while ($true) {
    $answer = Read-Host "$Prompt [$suffix]"
    if ([string]::IsNullOrWhiteSpace($answer)) {
      return $DefaultYes
    }
    switch ($answer.Trim().ToLowerInvariant()) {
      "y" { return $true }
      "yes" { return $true }
      "n" { return $false }
      "no" { return $false }
      default { Write-UiLine "Enter yes or no." Yellow }
    }
  }
}

function Test-IsAdministrator {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Restart-Elevated {
  if ($NoElevate -or (Test-IsAdministrator)) {
    return
  }
  Write-UiLine "Administrator rights are recommended for installing prerequisites and Fika firewall rules." Yellow
  if (-not (Read-YesNo "Relaunch this script as administrator now?" $true)) {
    return
  }
  $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
  if ($Mode -ne "Interactive") {
    $args += "-Mode"
    $args += $Mode
  }
  if (-not [string]::IsNullOrWhiteSpace($SptRoot)) {
    $args += "-SptRoot"
    $args += "`"$SptRoot`""
  }
  if (-not [string]::IsNullOrWhiteSpace($ModPackagePath)) {
    $args += "-ModPackagePath"
    $args += "`"$ModPackagePath`""
  }
  if (-not [string]::IsNullOrWhiteSpace($ServerUrl)) {
    $args += "-ServerUrl"
    $args += "`"$ServerUrl`""
  }
  Start-Process -FilePath "powershell.exe" -ArgumentList $args -Verb RunAs
  exit
}

function Select-InstallRoot {
  if (-not [string]::IsNullOrWhiteSpace($SptRoot)) {
    return $SptRoot
  }

  Write-UiLine "Available drives:" DarkCyan
  Get-PSDrive -PSProvider FileSystem |
    Where-Object { $_.Free -gt 0 } |
    Sort-Object Name |
    ForEach-Object {
      $freeGb = [Math]::Round($_.Free / 1GB, 1)
      Write-UiLine ("  {0}:  {1} GB free" -f $_.Name, $freeGb) Gray
    }

  $drive = Read-RequiredValue "Install drive letter" "C"
  $drive = $drive.TrimEnd(":")
  $defaultRoot = "$($drive):\SPT"
  return Read-RequiredValue "SPT install folder" $defaultRoot
}

function Test-CommandAvailable {
  param([string]$Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage {
  param(
    [string]$Id,
    [string]$DisplayName
  )
  if (-not (Test-CommandAvailable "winget.exe")) {
    Write-UiLine "winget is not available. Skipping $DisplayName." Yellow
    return
  }

  Write-UiLine "Checking $DisplayName..." Gray
  $listOutput = & winget.exe list --id $Id --exact --accept-source-agreements 2>$null
  if ($LASTEXITCODE -eq 0 -and ($listOutput -join "`n") -match [regex]::Escape($Id)) {
    Write-UiLine "  Already installed: $DisplayName" Green
    return
  }

  Write-UiLine "  Installing: $DisplayName" Yellow
  & winget.exe install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) {
    Write-UiLine "  winget could not install $DisplayName. Install it manually if the setup later complains." Yellow
  } else {
    Write-UiLine "  Installed: $DisplayName" Green
  }
}

function Install-Prerequisites {
  if ($SkipPrerequisites) {
    Write-UiLine "Skipping prerequisite installation by request." Yellow
    return
  }

  if (-not (Read-YesNo "Install/check common prerequisites with winget?")) {
    return
  }

  $packages = @(
    @{ Id = "Microsoft.VCRedist.2015+.x64"; Name = "Microsoft Visual C++ Redistributable 2015-2022 x64" },
    @{ Id = "Microsoft.DotNet.DesktopRuntime.8"; Name = ".NET Desktop Runtime 8" },
    @{ Id = "Microsoft.DotNet.DesktopRuntime.9"; Name = ".NET Desktop Runtime 9" },
    @{ Id = "7zip.7zip"; Name = "7-Zip" }
  )

  foreach ($package in $packages) {
    Install-WingetPackage -Id $package.Id -DisplayName $package.Name
  }

  if (Read-YesNo "Install WireGuard for VPN connectivity?" $true) {
    Install-WingetPackage -Id "WireGuard.WireGuard" -DisplayName "WireGuard"
  }
}

function Open-DownloadPage {
  param(
    [string]$Url,
    [string]$Name
  )
  Write-UiLine "Opening $Name download page:" DarkCyan
  Write-UiLine "  $Url" Gray
  Start-Process $Url
}

function Resolve-InstallerPath {
  param(
    [string]$Prompt,
    [string]$DownloadUrl,
    [string]$DownloadName
  )
  while ($true) {
    $path = Read-OptionalValue $Prompt
    if ([string]::IsNullOrWhiteSpace($path)) {
      Open-DownloadPage -Url $DownloadUrl -Name $DownloadName
      Write-UiLine "Download the installer, then paste the full path to the .exe." Yellow
      $path = Read-RequiredValue "Installer path"
    }
    if (Test-Path -LiteralPath $path) {
      return (Resolve-Path -LiteralPath $path).Path
    }
    Write-UiLine "File not found: $path" Yellow
  }
}

function Get-LatestGitHubAsset {
  param(
    [string]$Repo,
    [string]$AssetPattern
  )
  $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing
  $asset = $release.assets | Where-Object { $_.name -match $AssetPattern } | Select-Object -First 1
  if (-not $asset) {
    throw "No release asset matching '$AssetPattern' found for $Repo."
  }
  return $asset.browser_download_url
}

function Install-Spt {
  param([string]$Root)
  if ((Test-Path -LiteralPath (Join-Path $Root "SPT.Server.exe")) -and (Test-Path -LiteralPath (Join-Path $Root "SPT.Launcher.exe"))) {
    Write-UiLine "SPT already appears installed at $Root." Green
    return
  }

  New-Item -ItemType Directory -Path $Root -Force | Out-Null
  Write-UiLine "The official SPT installer is interactive and should run from the SPT install folder." Yellow
  Write-UiLine "SPT installer notes: it checks .NET, duplicates EFT, patches EFT, and installs SPT into the selected folder." Gray

  $installer = Resolve-InstallerPath `
    -Prompt "Path to SPT installer .exe, or press Enter to open the download page" `
    -DownloadUrl "https://forge.sp-tarkov.com/installer" `
    -DownloadName "SPT Installer"

  $targetInstaller = Join-Path $Root (Split-Path -Leaf $installer)
  if ($installer -ne $targetInstaller) {
    Copy-Item -LiteralPath $installer -Destination $targetInstaller -Force
  }

  Write-UiLine "Launching SPT installer from $Root. Complete the installer UI before continuing." Cyan
  Start-Process -FilePath $targetInstaller -WorkingDirectory $Root -Wait

  if (-not (Test-Path -LiteralPath (Join-Path $Root "SPT.Server.exe"))) {
    throw "SPT.Server.exe was not found in $Root after the installer exited."
  }
  if (-not (Test-Path -LiteralPath (Join-Path $Root "SPT.Launcher.exe"))) {
    throw "SPT.Launcher.exe was not found in $Root after the installer exited."
  }
}

function Install-Fika {
  param([string]$Root)
  $fikaPlugin = Join-Path $Root "BepInEx\plugins\Fika"
  $fikaServer = Join-Path $Root "SPT\user\mods\fika-server"
  if ((Test-Path -LiteralPath $fikaPlugin) -and (Test-Path -LiteralPath $fikaServer)) {
    Write-UiLine "Fika already appears installed at $Root." Green
    return
  }

  $downloadedInstaller = ""
  if (Read-YesNo "Try to download the latest Fika installer from GitHub automatically?" $true) {
    try {
      $assetUrl = Get-LatestGitHubAsset -Repo "project-fika/Fika-Installer" -AssetPattern "Fika-Installer.*\.exe$"
      $downloadedInstaller = Join-Path $env:TEMP "Fika-Installer.exe"
      Write-UiLine "Downloading Fika installer..." Cyan
      Invoke-WebRequest -Uri $assetUrl -OutFile $downloadedInstaller -UseBasicParsing
    } catch {
      Write-UiLine "Automatic Fika download failed: $($_.Exception.Message)" Yellow
    }
  }

  if ([string]::IsNullOrWhiteSpace($downloadedInstaller) -or -not (Test-Path -LiteralPath $downloadedInstaller)) {
    $downloadedInstaller = Resolve-InstallerPath `
      -Prompt "Path to Fika-Installer.exe, or press Enter to open the Fika install guide" `
      -DownloadUrl "https://wiki.project-fika.com/installing-fika/installation" `
      -DownloadName "Fika installation guide"
  }

  $targetInstaller = Join-Path $Root "Fika-Installer.exe"
  Copy-Item -LiteralPath $downloadedInstaller -Destination $targetInstaller -Force

  Write-UiLine "Launching Fika installer. Choose Install Fika in the installer UI." Cyan
  Start-Process -FilePath $targetInstaller -WorkingDirectory $Root -Wait

  if (-not (Test-Path -LiteralPath $fikaPlugin)) {
    Write-UiLine "Fika client plugin was not found after installer exit. Check installer output." Yellow
  }
  if (-not (Test-Path -LiteralPath $fikaServer)) {
    Write-UiLine "Fika server mod was not found after installer exit. Check installer output." Yellow
  }
}

function Move-ExistingClientMods {
  param([string]$Root)
  if (-not (Read-YesNo "Back up existing non-baseline mods/plugins before applying the SPT02 package?" $true)) {
    return ""
  }

  return Backup-ActiveModSet -Root $Root -Reason "setup"
}

function Get-ModSurfacePaths {
  param([string]$Root)
  return [ordered]@{
    PluginPath = Join-Path $Root "BepInEx\plugins"
    ModsPath = Join-Path $Root "SPT\user\mods"
    PatcherPath = Join-Path $Root "BepInEx\patchers"
  }
}

function Get-ActiveSwitchableMods {
  param([string]$Root)
  $paths = Get-ModSurfacePaths -Root $Root
  $keepPluginNames = @("Fika", "spt")
  $keepPatcherNames = @("spt-prepatch.dll")
  $keepServerModNames = @("fika-server")
  $items = @()

  if (Test-Path -LiteralPath $paths.PluginPath) {
    $items += Get-ChildItem -LiteralPath $paths.PluginPath -Force | Where-Object { $keepPluginNames -notcontains $_.Name } | ForEach-Object {
      [pscustomobject]@{ Type = "bepinex-plugins"; Item = $_ }
    }
  }

  if (Test-Path -LiteralPath $paths.ModsPath) {
    $items += Get-ChildItem -LiteralPath $paths.ModsPath -Force | Where-Object { $keepServerModNames -notcontains $_.Name } | ForEach-Object {
      [pscustomobject]@{ Type = "server-mods"; Item = $_ }
    }
  }

  if (Test-Path -LiteralPath $paths.PatcherPath) {
    $items += Get-ChildItem -LiteralPath $paths.PatcherPath -Force | Where-Object { $keepPatcherNames -notcontains $_.Name } | ForEach-Object {
      [pscustomobject]@{ Type = "bepinex-patchers"; Item = $_ }
    }
  }

  return @($items)
}

function Backup-ActiveModSet {
  param(
    [string]$Root,
    [string]$Reason = "manual"
  )

  $activeItems = @(Get-ActiveSwitchableMods -Root $Root)
  if ($activeItems.Count -eq 0) {
    Write-UiLine "No non-baseline mods/plugins are active, so no backup is needed." Green
    return ""
  }

  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $backupRoot = Join-Path $Root "_disabled-client-baseline\$Reason-$stamp"
  $pluginBackup = Join-Path $backupRoot "bepinex-plugins"
  $modBackup = Join-Path $backupRoot "server-mods"
  $patcherBackup = Join-Path $backupRoot "bepinex-patchers"
  New-Item -ItemType Directory -Path $pluginBackup, $modBackup, $patcherBackup -Force | Out-Null

  foreach ($entry in $activeItems) {
    switch ($entry.Type) {
      "bepinex-plugins" { $destination = $pluginBackup }
      "server-mods" { $destination = $modBackup }
      "bepinex-patchers" { $destination = $patcherBackup }
      default { throw "Unknown mod surface type: $($entry.Type)" }
    }
    Move-Item -LiteralPath $entry.Item.FullName -Destination $destination -Force
  }

  $metadata = [ordered]@{
    created = (Get-Date).ToString("s")
    reason = $Reason
    sourceRoot = $Root
    itemCount = $activeItems.Count
  }
  $metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backupRoot "backup-metadata.json") -Encoding UTF8

  Write-UiLine "Backed up active non-baseline mods to $backupRoot" Green
  return $backupRoot
}

function Get-ModBackups {
  param([string]$Root)
  $backupBase = Join-Path $Root "_disabled-client-baseline"
  if (-not (Test-Path -LiteralPath $backupBase)) {
    return @()
  }

  return @(Get-ChildItem -LiteralPath $backupBase -Directory -Force | Where-Object {
    (Test-Path -LiteralPath (Join-Path $_.FullName "bepinex-plugins")) -or
    (Test-Path -LiteralPath (Join-Path $_.FullName "server-mods")) -or
    (Test-Path -LiteralPath (Join-Path $_.FullName "bepinex-patchers"))
  } | Sort-Object LastWriteTime -Descending)
}

function Select-ModBackup {
  param([string]$Root)
  $backups = @(Get-ModBackups -Root $Root)
  if ($backups.Count -eq 0) {
    Write-UiLine "No mod backups were found under $Root\_disabled-client-baseline." Yellow
    return $null
  }

  Write-UiLine "Available mod backups:" DarkCyan
  for ($i = 0; $i -lt $backups.Count; $i++) {
    $backup = $backups[$i]
    $metadataPath = Join-Path $backup.FullName "backup-metadata.json"
    $reason = "unknown"
    $itemCount = "unknown"
    if (Test-Path -LiteralPath $metadataPath) {
      try {
        $metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
        $reason = $metadata.reason
        $itemCount = $metadata.itemCount
      } catch {
        $reason = "metadata unreadable"
      }
    }
    Write-UiLine ("  {0}. {1}  ({2}, {3} items, {4})" -f ($i + 1), $backup.Name, $reason, $itemCount, $backup.LastWriteTime) Gray
  }

  while ($true) {
    $selection = Read-Host "Backup number to restore, or press Enter to cancel"
    if ([string]::IsNullOrWhiteSpace($selection)) {
      return $null
    }
    $number = 0
    if ([int]::TryParse($selection, [ref]$number) -and $number -ge 1 -and $number -le $backups.Count) {
      return $backups[$number - 1]
    }
    Write-UiLine "Choose a number from 1 to $($backups.Count)." Yellow
  }
}

function Restore-ModBackup {
  param(
    [string]$Root,
    [string]$BackupPath = ""
  )

  if ([string]::IsNullOrWhiteSpace($BackupPath)) {
    $selected = Select-ModBackup -Root $Root
    if (-not $selected) {
      return
    }
    $BackupPath = $selected.FullName
  }

  if (-not (Test-Path -LiteralPath $BackupPath)) {
    throw "Backup path not found: $BackupPath"
  }

  Write-UiLine "Before restoring, the currently active non-baseline mods will be backed up." Yellow
  $currentBackup = Backup-ActiveModSet -Root $Root -Reason "pre-restore"
  if (-not [string]::IsNullOrWhiteSpace($currentBackup)) {
    Write-UiLine "Current active mod set saved at $currentBackup" Green
  }

  $pluginSource = Join-Path $BackupPath "bepinex-plugins"
  $patcherSource = Join-Path $BackupPath "bepinex-patchers"
  $modsSource = Join-Path $BackupPath "server-mods"

  Copy-PackageChildren -Source $pluginSource -Destination (Join-Path $Root "BepInEx\plugins") | Out-Null
  Copy-PackageChildren -Source $patcherSource -Destination (Join-Path $Root "BepInEx\patchers") | Out-Null
  Copy-PackageChildren -Source $modsSource -Destination (Join-Path $Root "SPT\user\mods") | Out-Null

  Write-UiLine "Restored mod backup from $BackupPath" Green
}

function Copy-PackageChildren {
  param(
    [string]$Source,
    [string]$Destination
  )
  if (-not (Test-Path -LiteralPath $Source)) {
    return $false
  }
  New-Item -ItemType Directory -Path $Destination -Force | Out-Null
  Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
  }
  return $true
}

function Install-ModPackage {
  param(
    [string]$Root,
    [string]$PackagePath
  )
  if ([string]::IsNullOrWhiteSpace($PackagePath)) {
    $PackagePath = Read-OptionalValue "Path to SPT02 client mod package .zip or folder, or press Enter to skip"
  }
  if ([string]::IsNullOrWhiteSpace($PackagePath)) {
    Write-UiLine "Skipping mod package installation. This is fine for a Fika baseline test, but not for the current modded SPT02 setup." Yellow
    return
  }
  if (-not (Test-Path -LiteralPath $PackagePath)) {
    throw "Mod package not found: $PackagePath"
  }

  $stage = $PackagePath
  $tempRoot = ""
  if ((Get-Item -LiteralPath $PackagePath).PSIsContainer -eq $false) {
    $tempRoot = Join-Path $env:TEMP ("spt-fika-mod-package-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    Expand-Archive -LiteralPath $PackagePath -DestinationPath $tempRoot -Force
    $stage = $tempRoot
  }

  $manifest = Join-Path $stage "manifest.json"
  if (Test-Path -LiteralPath $manifest) {
    Write-UiLine "Package manifest:" DarkCyan
    Get-Content -LiteralPath $manifest | ForEach-Object { Write-UiLine "  $_" Gray }
  }

  $installed = 0
  $pluginDest = Join-Path $Root "BepInEx\plugins"
  $patcherDest = Join-Path $Root "BepInEx\patchers"
  $modsDest = Join-Path $Root "SPT\user\mods"
  $rootDest = $Root

  $sources = @(
    @{ Names = @("bepinex-plugins", "BepInEx\plugins"); Dest = $pluginDest },
    @{ Names = @("bepinex-patchers", "BepInEx\patchers"); Dest = $patcherDest },
    @{ Names = @("server-mods", "SPT\user\mods", "user\mods"); Dest = $modsDest },
    @{ Names = @("root"); Dest = $rootDest }
  )

  foreach ($sourceGroup in $sources) {
    foreach ($name in $sourceGroup.Names) {
      $candidate = Join-Path $stage $name
      if (Copy-PackageChildren -Source $candidate -Destination $sourceGroup.Dest) {
        $installed++
        break
      }
    }
  }

  if ($tempRoot -and (Test-Path -LiteralPath $tempRoot)) {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force
  }

  if ($installed -eq 0) {
    throw "No recognized package folders were found. Expected bepinex-plugins, bepinex-patchers, server-mods, or root."
  }

  Write-UiLine "Installed mod package into $Root." Green
}

function New-ClientModPackage {
  Write-UiHeader
  $sourceRoot = Read-RequiredValue "Source SPT folder to package" "C:\SPT"
  if (-not (Test-Path -LiteralPath $sourceRoot)) {
    throw "Source SPT folder not found: $sourceRoot"
  }

  $defaultOut = Join-Path ([Environment]::GetFolderPath("Desktop")) ("spt02-client-modpack-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".zip")
  $outputZip = Read-RequiredValue "Output package path" $defaultOut
  $includeOptional = Read-YesNo "Include optional local-only client UI/status plugins?" $false

  $tempRoot = Join-Path $env:TEMP ("spt-fika-client-package-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

  $excludePluginNames = @("Fika", "spt", "HomelabFikaHeadlessCrcFix")
  if (-not $includeOptional) {
    $excludePluginNames += "MoxoPixel.MenuOverhaul"
    $excludePluginNames += "FikaDiscordPresence"
  }

  $pluginSource = Join-Path $sourceRoot "BepInEx\plugins"
  $patcherSource = Join-Path $sourceRoot "BepInEx\patchers"
  $modsSource = Join-Path $sourceRoot "SPT\user\mods"

  $pluginPackage = Join-Path $tempRoot "bepinex-plugins"
  $patcherPackage = Join-Path $tempRoot "bepinex-patchers"
  $modsPackage = Join-Path $tempRoot "server-mods"
  New-Item -ItemType Directory -Path $pluginPackage, $patcherPackage, $modsPackage -Force | Out-Null

  if (Test-Path -LiteralPath $pluginSource) {
    Get-ChildItem -LiteralPath $pluginSource -Force |
      Where-Object { $excludePluginNames -notcontains $_.Name } |
      ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $pluginPackage -Recurse -Force }
  }

  if (Test-Path -LiteralPath $patcherSource) {
    Get-ChildItem -LiteralPath $patcherSource -Force |
      Where-Object { $_.Name -eq "spt-prepatch.dll" } |
      ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $patcherPackage -Recurse -Force }
  }

  if (Test-Path -LiteralPath $modsSource) {
    Get-ChildItem -LiteralPath $modsSource -Force |
      Where-Object { $_.Name -ne "fika-server" } |
      ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $modsPackage -Recurse -Force }
  }

  $manifestObject = [ordered]@{
    name = "SPT02 player client mod package"
    created = (Get-Date).ToString("s")
    serverUrl = $ServerUrl
    sourceRoot = $sourceRoot
    notes = @(
      "Install SPT and Fika first.",
      "Apply this package with Install-SPTFikaPlayerClient.ps1.",
      "Do not include disabled/quarantined mods unless deliberately testing them."
    )
  }
  $manifestObject | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $tempRoot "manifest.json") -Encoding UTF8

  if (Test-Path -LiteralPath $outputZip) {
    Remove-Item -LiteralPath $outputZip -Force
  }
  Compress-Archive -Path (Join-Path $tempRoot "*") -DestinationPath $outputZip -Force
  Remove-Item -LiteralPath $tempRoot -Recurse -Force

  Write-UiLine "Created player mod package:" Green
  Write-UiLine "  $outputZip" Cyan
}

function Show-PostInstallInstructions {
  param([string]$Root)
  Write-Host ""
  Write-UiLine "Setup finished." Green
  Write-UiLine "Open SPT.Launcher from:" DarkCyan
  Write-UiLine "  $Root" Gray
  Write-UiLine "Launcher values:" DarkCyan
  Write-UiLine "  SPT Game Path: $Root" Gray
  Write-UiLine "  URL: $ServerUrl" Gray
  Write-Host ""
  Write-UiLine "For VPN players, activate the WireGuard tunnel before launching the game." Yellow
}

function Invoke-PlayerSetup {
  Write-UiHeader
  Restart-Elevated

  $root = Select-InstallRoot
  $root = $root.TrimEnd("\")
  $logPath = Join-Path $env:TEMP ("spt-fika-player-setup-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
  Start-Transcript -Path $logPath -Force | Out-Null

  try {
    Update-SetupProgress -Status "Preparing install folder" -Step 1
    New-Item -ItemType Directory -Path $root -Force | Out-Null
    Write-UiLine "Install folder: $root" Green

    Update-SetupProgress -Status "Installing prerequisites"
    Install-Prerequisites

    Update-SetupProgress -Status "Installing SPT"
    Install-Spt -Root $root

    Update-SetupProgress -Status "Installing Fika"
    Install-Fika -Root $root

    Update-SetupProgress -Status "Quarantining old mods"
    Move-ExistingClientMods -Root $root

    Update-SetupProgress -Status "Installing SPT02 mod package"
    Install-ModPackage -Root $root -PackagePath $ModPackagePath

    Update-SetupProgress -Status "Validating local files"
    $required = @(
      "SPT.Server.exe",
      "SPT.Launcher.exe",
      "EscapeFromTarkov.exe",
      "BepInEx\plugins\Fika",
      "SPT\user\mods\fika-server"
    )
    foreach ($item in $required) {
      $full = Join-Path $root $item
      if (Test-Path -LiteralPath $full) {
        Write-UiLine "  OK: $item" Green
      } else {
        Write-UiLine "  Missing: $item" Yellow
      }
    }

    Update-SetupProgress -Status "Complete"
    Write-Progress -Activity "SPT/Fika player setup" -Completed
    Show-PostInstallInstructions -Root $root
    Write-UiLine "Setup log: $logPath" DarkGray
  } finally {
    Stop-Transcript | Out-Null
  }
}

function Invoke-Spt02ModSetup {
  Write-UiHeader
  $root = Select-InstallRoot
  $root = $root.TrimEnd("\")
  if (-not (Test-Path -LiteralPath $root)) {
    throw "SPT folder not found: $root"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $root "SPT.Launcher.exe"))) {
    Write-UiLine "SPT.Launcher.exe was not found in $root. This does not look like an SPT install." Yellow
    if (-not (Read-YesNo "Continue anyway?" $false)) {
      return
    }
  }

  $logPath = Join-Path $env:TEMP ("spt-fika-mod-switch-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
  Start-Transcript -Path $logPath -Force | Out-Null
  try {
    $Script:StepTotal = 4
    Update-SetupProgress -Status "Checking current SPT install" -Step 1
    Write-UiLine "SPT folder: $root" Green

    Update-SetupProgress -Status "Backing up current mods"
    Move-ExistingClientMods -Root $root | Out-Null

    Update-SetupProgress -Status "Installing SPT02 mod package"
    Install-ModPackage -Root $root -PackagePath $ModPackagePath

    Update-SetupProgress -Status "Complete"
    Write-Progress -Activity "SPT/Fika player setup" -Completed
    Show-PostInstallInstructions -Root $root
    Write-UiLine "Switch log: $logPath" DarkGray
  } finally {
    Stop-Transcript | Out-Null
    $Script:StepTotal = 8
  }
}

function Invoke-ModRestore {
  Write-UiHeader
  $root = Select-InstallRoot
  $root = $root.TrimEnd("\")
  if (-not (Test-Path -LiteralPath $root)) {
    throw "SPT folder not found: $root"
  }

  $logPath = Join-Path $env:TEMP ("spt-fika-mod-restore-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
  Start-Transcript -Path $logPath -Force | Out-Null
  try {
    $Script:StepTotal = 3
    Update-SetupProgress -Status "Selecting mod backup" -Step 1
    $backup = Select-ModBackup -Root $root
    if (-not $backup) {
      Write-Progress -Activity "SPT/Fika player setup" -Completed
      return
    }

    Update-SetupProgress -Status "Backing up current active mods"
    Update-SetupProgress -Status "Restoring selected backup"
    Restore-ModBackup -Root $root -BackupPath $backup.FullName

    Write-Progress -Activity "SPT/Fika player setup" -Completed
    Write-UiLine "Restore log: $logPath" DarkGray
  } finally {
    Stop-Transcript | Out-Null
    $Script:StepTotal = 8
  }
}

function Show-MainMenu {
  Write-UiHeader
  Write-UiLine "Choose an action:" DarkCyan
  Write-UiLine "  1. Full setup: install/check SPT, install/check Fika, then apply SPT02 mods" Gray
  Write-UiLine "  2. Mods only: back up current mods and apply the SPT02 mod package" Gray
  Write-UiLine "  3. Restore a previous mod setup" Gray
  Write-UiLine "  4. Build a player mod package from an existing SPT install" Gray
  Write-UiLine "  5. Exit" Gray
  while ($true) {
    $choice = Read-Host "Selection"
    switch ($choice) {
      "1" { Invoke-PlayerSetup; return }
      "2" { Invoke-Spt02ModSetup; return }
      "3" { Invoke-ModRestore; return }
      "4" { New-ClientModPackage; return }
      "5" { return }
      default { Write-UiLine "Choose 1, 2, 3, 4, or 5." Yellow }
    }
  }
}

switch ($Mode) {
  "Interactive" { Show-MainMenu }
  "Setup" { Invoke-PlayerSetup }
  "Mods" { Invoke-Spt02ModSetup }
  "Restore" { Invoke-ModRestore }
  "Package" { New-ClientModPackage }
}
