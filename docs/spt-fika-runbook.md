# SPT/Fika Server Runbook

## Overview

This runbook documents the lab SPT/Fika Escape From Tarkov co-op setup.

- Service host: `SPT02`
- Platform: Windows 10 physical host
- IP address: `192.168.1.86`
- SPT root: `C:\SPT`
- SPT backend: `C:\SPT\SPT\SPT.Server.exe`
- SPT backend URL: `https://192.168.1.86:6969`
- Fika headless manager: `C:\SPT\FikaHeadlessManager.exe`
- VPN server: UDM Pro WireGuard server `SPT-Fika-WireGuard`
- VPN subnet: `192.168.86.0/24`
- LAN subnet: `192.168.1.0/24`
- Credentials source of truth: OpenBao path `secret/homelab/vms/spt02`

Do not store SPT02 passwords, VPN private keys, Discord webhook URLs, or API tokens in Git, Wiki.js pages, Discord, NetBox comments, or command output.

## Architecture

SPT and Fika have two separate networking roles.

The SPT backend serves profiles, inventory, traders, flea, launcher login, Fika coordination, and other backend APIs. In this lab the backend runs on `SPT02` at `https://192.168.1.86:6969`.

The raid host is the game client that actually hosts a raid. That can be either:

- The Fika headless EFT client running on `SPT02`
- A normal player EFT/SPT/Fika client, such as Adam's local gaming workstation

When the headless client is selected, raid simulation and AI run on `SPT02`. When a player clicks `HOST RAID` without selecting the headless host, raid simulation and AI run on that player's machine.

### Main Flows

Headless-hosted raid:

```text
Player over VPN or LAN
  -> SPT02 TCP 6969 for SPT/Fika backend
  -> SPT02 UDP 25565 for Fika raid traffic
```

Player-hosted raid:

```text
Player over VPN or LAN
  -> SPT02 TCP 6969 for SPT/Fika backend
  -> Raid host player's PC UDP 25565 for Fika raid traffic
```

Project Fika documents that the raid is hosted by the game client of the user that clicks `HOST RAID`, not by `SPT.Server`. The headless client is an optional way to offload that host role to a separate EFT instance. Reference:

- https://wiki.project-fika.com/faqandguides
- https://wiki.project-fika.com/advanced-features/headless-client

## Endpoints And Ports

| Endpoint | Purpose | Scope |
| --- | --- | --- |
| `https://192.168.1.86:6969` | SPT/Fika backend | LAN and VPN players |
| `https://192.168.1.86:6969/fika/headless/get` | Headless status endpoint | Operators only |
| `192.168.1.86:25565/udp` | Fika raid traffic when SPT02 headless hosts | LAN and VPN players |
| `<player-host-ip>:25565/udp` | Fika raid traffic when a player hosts | LAN and VPN players |
| `192.168.1.86:5985/tcp` | WinRM management | AI workstation/admin network only |
| `192.168.1.86:22/tcp` | OpenSSH management | AI workstation/admin network only |

## VPN Access With UDM Pro

Remote players should connect through WireGuard on the UDM Pro. Do not expose SPT/Fika directly to the WAN unless that has been explicitly approved.

Current VPN server:

- Name: `SPT-Fika-WireGuard`
- VPN type: WireGuard
- VPN subnet: `192.168.86.1/24`
- WAN listener: `51820/udp`
- DNS pushed to clients: `192.168.1.1`
- Intended access: split tunnel into the lab only

### Create A New VPN Client Profile

Use one WireGuard client profile per person/device.

1. Open the UniFi Network application for the UDM Pro.
2. Go to `Settings`.
3. Go to `VPN`.
4. Under `VPN Server`, select or manage `SPT-Fika-WireGuard`.
5. Create a new WireGuard client profile.
6. Name it with a clear owner/device label, such as `eft-adam-laptop` or `eft-friend1-pc`.
7. Download or copy the generated WireGuard configuration.
8. Share the config with the user out of band.
9. Do not reuse a profile across multiple users.
10. If access should be revoked, remove that WireGuard client profile from the UDM Pro.

If the generated tunnel name contains characters the Windows WireGuard client rejects, edit only the local config file's `[Interface]` tunnel name or import filename to a simple value such as `spt-fika-friend1`. Do not modify keys unless regenerating the profile.

### UDM Firewall Intent

VPN users should be treated as a landing zone, not as general LAN clients.

Allow:

- `192.168.86.0/24` to `192.168.1.86:6969/tcp`
- `192.168.86.0/24` to `192.168.1.86:25565/udp`
- Optional: `192.168.86.0/24` to a player host's UDP `25565` only while that player is hosting

Deny:

- `192.168.86.0/24` to other `192.168.1.0/24` destinations

Keep the deny rule below the explicit SPT/Fika allow rules.

The configured UniFi Integration API key is useful for inventory sync but did not expose firewall-rule write endpoints during the SPT02 migration. Verify these UDM rules in the UniFi Network UI after moving the service from SPT01 to SPT02.

SPT02 Windows Firewall has matching host rules:

- `SPT Fika Backend TCP 6969 LAN+VPN`: TCP `6969` from `192.168.1.0/24` and `192.168.86.0/24`
- `SPT Fika Raid UDP 25565 LAN+VPN`: UDP `25565` from `192.168.1.0/24` and `192.168.86.0/24`

## Player Setup

Every player needs their own legal EFT installation, their own SPT install that matches the server's SPT version, and the Fika client plugin that matches the server.

Minimum setup:

1. Install WireGuard.
2. Import the WireGuard config provided by the operator.
3. Activate the tunnel.
4. Confirm the player can reach `https://192.168.1.86:6969`.
5. Install or copy the matching SPT client.
6. Install the matching Fika client plugin.
7. Start the SPT Launcher.
8. Set the launcher URL to `https://192.168.1.86:6969`.
9. Set the launcher game path to the local SPT root, for example `C:\SPT`.
10. Launch the game.

Baseline validation should be done with only Fika and required SPT plugins loaded. Add mods after the baseline works.

### Interactive Player Setup Script

Use the repo script below to streamline player setup on a Windows PC:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\automation\spt-client\Install-SPTFikaPlayerClient.ps1
```

The script is interactive and uses colored prompts plus a progress bar. It can:

- Prompt for the target install drive and SPT folder, such as `C:\SPT` or `G:\SPT`.
- Detect an existing SPT install by checking for `SPT.Server.exe` and `SPT.Launcher.exe`; if found, it skips the SPT installer step.
- Detect an existing Fika install by checking for `BepInEx\plugins\Fika` and `SPT\user\mods\fika-server`; if found, it skips the Fika installer step.
- Check/install common Windows prerequisites with `winget`.
- Optionally install WireGuard for VPN users.
- Launch the official SPT installer from the selected install folder.
- Download or prompt for `Fika-Installer.exe`, then launch it from the SPT root.
- Back up existing non-baseline mods/plugins into a timestamped folder before applying the SPT02 mod package.
- Restore a previous mod setup from those timestamped backups, so users can flip between their normal local mod setup and the SPT02-compatible setup.
- Apply an operator-provided SPT02 client mod package.
- Print the launcher values the player must use:
  - SPT Game Path: the selected local SPT root.
  - URL: `https://192.168.1.86:6969`.

Interactive menu options:

1. Full setup: install/check SPT, install/check Fika, then apply SPT02 mods.
2. Mods only: back up current mods and apply the SPT02 mod package.
3. Restore a previous mod setup.
4. Build a player mod package from an existing SPT install.
5. Exit.

Mod backups are stored under the selected SPT root:

```text
_disabled-client-baseline\
```

Each backup has a timestamped folder name, such as:

```text
setup-20260608-134500
pre-restore-20260608-140012
```

The restore workflow backs up the current active non-baseline mods before restoring the selected backup. This preserves the SPT02 mod set and the user's previous local mod set as switchable snapshots.

The official SPT installer remains interactive. SPT's installer page says it checks the required .NET version, duplicates the legitimate EFT installation, patches the duplicated EFT files, and installs SPT into the selected folder:

- https://forge.sp-tarkov.com/installer

The Fika installer also remains interactive. Project Fika's install guide says the user must already have a working SPT installation, copy `Fika-Installer.exe` to the SPT install root, then run it and choose `Install Fika`:

- https://wiki.project-fika.com/installing-fika
- https://wiki.project-fika.com/installing-fika/installation

To build the mod package from a known-good local SPT install, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\automation\spt-client\Install-SPTFikaPlayerClient.ps1 -Mode Package
```

The package mode exports active client/server mod files into a ZIP with this structure:

```text
bepinex-plugins\
bepinex-patchers\
server-mods\
manifest.json
```

The setup mode can then consume that ZIP on a player PC:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\automation\spt-client\Install-SPTFikaPlayerClient.ps1 -Mode Setup -ModPackagePath "C:\Users\Public\Downloads\spt02-client-modpack.zip"
```

To apply only the SPT02 mod package to an existing SPT/Fika install:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\automation\spt-client\Install-SPTFikaPlayerClient.ps1 -Mode Mods -ModPackagePath "C:\Users\Public\Downloads\spt02-client-modpack.zip"
```

To restore a previous local mod setup:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\automation\spt-client\Install-SPTFikaPlayerClient.ps1 -Mode Restore
```

Do not build the package from a folder that contains currently disabled troubleshooting mods. The script intentionally excludes the baseline `Fika` and `spt` plugins from the package because the Fika installer should install those. It also excludes the headless-only `HomelabFikaHeadlessCrcFix` plugin.

### Baseline Mod Quarantine Script

This script moves non-baseline client mods/plugins out of the active SPT path. Adjust `$SptRoot` if the user's install is not `C:\SPT`.

```powershell
$SptRoot = "C:\SPT"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $SptRoot "_disabled-client-baseline\$Stamp"
$PluginBackup = Join-Path $BackupRoot "bepinex-plugins"
$ModBackup = Join-Path $BackupRoot "server-mods"
$PatcherBackup = Join-Path $BackupRoot "bepinex-patchers"

New-Item -ItemType Directory -Path $PluginBackup, $ModBackup, $PatcherBackup -Force | Out-Null

$PluginPath = Join-Path $SptRoot "BepInEx\plugins"
$ModsPath = Join-Path $SptRoot "SPT\user\mods"
$PatcherPath = Join-Path $SptRoot "BepInEx\patchers"

$KeepPluginNames = @("Fika", "spt")
$KeepPatcherNames = @("spt-prepatch.dll")
$KeepServerModNames = @("fika-server")

if (Test-Path -LiteralPath $PluginPath) {
  Get-ChildItem -LiteralPath $PluginPath -Force | Where-Object {
    $KeepPluginNames -notcontains $_.Name
  } | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $PluginBackup -Force
  }
}

if (Test-Path -LiteralPath $ModsPath) {
  Get-ChildItem -LiteralPath $ModsPath -Force | Where-Object {
    $KeepServerModNames -notcontains $_.Name
  } | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $ModBackup -Force
  }
}

if (Test-Path -LiteralPath $PatcherPath) {
  Get-ChildItem -LiteralPath $PatcherPath -Force | Where-Object {
    $KeepPatcherNames -notcontains $_.Name
  } | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination $PatcherBackup -Force
  }
}

Write-Host "Baseline backup created at $BackupRoot"
```

If PowerShell blocks script execution, run this in the same PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

## Hosting Options

### Option 1: Use The SPT02 Headless Client

This is the preferred steady-state setup because it offloads raid hosting from the player's local PC.

1. Confirm SPT02 backend is running.
2. Confirm the Fika headless client is registered.
3. In game, go to the Fika host flow.
4. Select the registered headless client.
5. Start the raid.

SPT02's Fika server config has:

```json
"restartAfterAmountOfRaids": 1
```

That means the headless client should restart after every raid. A full SPT server restart should not be required after every raid.

### Option 2: Host From A Player's Local PC

The headless client is optional. A normal player can host a raid without selecting the headless client.

Requirements:

- The player's game client must be able to reach SPT02 on TCP `6969`.
- Other players must be able to reach the raid host PC on UDP `25565`.
- Windows Firewall on the raid host PC must allow inbound UDP `25565`.
- If the remote player is using VPN, routing must allow the VPN client to reach the raid host PC.

This is useful for isolating headless-client issues. The tradeoff is that AI and raid simulation load runs on the player's PC.

## Current SPT02 Profiles

Current profile state after migration:

| Profile | Purpose |
| --- | --- |
| `Chadnovski` | Imported local progression profile, re-imported from Adam's local `C:\SPT` to SPT02 on 2026-06-08 |
| `xBigDaddyof6x` | Existing SPT02 player profile |
| `headless_*` | Fika headless client profile |

An older imported `Chadnovski` progression profile was removed from active SPT02 service on 2026-06-07 after repeated headless crashes. That older copy is retained here:

```text
C:\SPT\_disabled-headless\removed-profiles-20260607-203533\6a1f4c94ed07eef6542364cd.json
```

## Current Mod State

Server-side mods are installed on SPT02 under:

```text
C:\SPT\SPT\user\mods
```

Headless/client BepInEx plugins are installed under:

```text
C:\SPT\BepInEx\plugins
```

Fika validates client plugin compatibility. Do not put every player UI plugin on the headless client. Project Fika's headless guidance says the headless client should generally only receive mods that affect AI, spawn behavior, in-raid behavior, inventory behavior, or mods explicitly required for headless compatibility:

- https://wiki.project-fika.com/faqandguides/guidance-on-which-mods-should-be-used-on-the-headless-client
- https://wiki.project-fika.com/faqandguides/set-up-required-optional-mods

### Active SPT02 Server Mods

These are the active folders currently present on SPT02 under `C:\SPT\SPT\user\mods`. The version column is the Forge version to match or verify against. The installed folders are C# server mod folders and do not currently include `package.json` manifests to read exact installed versions from disk.

| SPT02 folder | Forge mod | Version | Description | Fika / headless note |
| --- | --- | --- | --- | --- |
| `[SVM] Server Value Modifier` | [Server Value Modifier [SVM]](https://forge.sp-tarkov.com/mod/236/server-value-modifier-svm) | 2.1.2 | All-in-one server value/configuration editor used to tune loot, flea, traders, raid, bot, hideout, and profile-impacting settings. | Forge has a Fika-compatible version available. Apply SVM profiles, then restart SPT/Fika. |
| `fika-server` | [Project Fika - Server](https://forge.sp-tarkov.com/mod/2357/project-fika-server) | 2.2.6 | Required server component for Fika co-op, backend coordination, presence, and headless registration. | Required. All players and the headless client must use compatible Fika versions. |
| `DrakiaXYZ-GildedKeyStorage` | [Gilded Key Storage](https://forge.sp-tarkov.com/mod/865/gilded-key-storage) | 2.0.4 | Adds progression-based key storage containers and supporting barter flow. | Server-side item/profile mod. All players should have matching required client pieces if prompted. |
| `FikaDiscordPresence` | [Fika Discord Presence](https://forge.sp-tarkov.com/mod/2583/fika-discord-presence) | 1.0.2 | Adds Discord webhook status integration for Fika sessions. | Installed on SPT02 and local `C:\SPT` on 2026-06-08. The webhook and Fika API key are configured only on SPT02 at `C:\SPT\SPT\user\mods\FikaDiscordPresence\config.json`; do not copy those secret values into Git or Wiki.js. |
| `QuestsExtended` | [Quests Extended](https://forge.sp-tarkov.com/mod/2106/quests-extended) | 4.0.3 | Adds quest condition support used by custom quests and trader/content mods. | Required for profiles/quests using extended conditions. Server side remains enabled for compatibility. |
| `SkillsExtended` | [Skills Extended](https://forge.sp-tarkov.com/mod/2383/skills-extended) | 2.2.2 | Adds and expands skill progression content. | Server mod is active for profile compatibility. The BepInEx client plugin was disabled on headless due a runtime error. |
| `Solarint-SAIN-ServerMod` | [SAIN](https://forge.sp-tarkov.com/mod/2513/sain-solarints-ai-modifications-full-ai-combat-system-replacement) | Verify on disk | Replaces and expands AI combat behavior. | Restored on SPT02 and the local client on 2026-06-07 after removing the old imported profile. Requires matching BigBrain and Waypoints client/headless plugins. |
| `StatRewards` | [Stat Rewards](https://forge.sp-tarkov.com/mod/2655/stat-rewards) | 1.1.1 | Adds configurable repeatable rewards for stat milestones such as kills, damage, looting, and other progression events. | Installed on SPT02 and local `C:\SPT` on 2026-06-08. Forge lists Fika compatibility as unknown; backend and headless startup validated only. |
| `TTC` | [[TTC] Tarkov Trading Cards](https://forge.sp-tarkov.com/mod/2226/ttc-tarkov-trading-cards) | 3.0.8 | Adds Tarkov Trading Cards, the Kolya trader, card collection quests, loot integration, and flea offers. | Forge lists Fika compatibility as unknown. Installed on SPT02 and local `C:\SPT` on 2026-06-07; backend and headless restarted cleanly. Players need the matching TTC client files and dependencies. |
| `WTT-ServerCommonLib` | [WTT - CommonLib](https://forge.sp-tarkov.com/mod/2310/wtt-commonlib) | 2.0.20 | Shared WTT library for custom items, quests, characters, and other WTT mod plumbing. | Dependency for WTT content. Forge has a Fika-compatible version available. |
| `WTT-Artem` | [WTT - Artem](https://forge.sp-tarkov.com/mod/2271/wtt-artem) | Verify on disk | Adds the Artem trader and related equipment/content. | Restored on SPT02 on 2026-06-07 after removing the old imported profile that contained stale Artem item references. |
| `WTT-Armory` | [WTT - Armory](https://forge.sp-tarkov.com/mod/2246/wtt-armory) | 2.0.5 | Adds the official WTT weapons pack, custom items, bundles, quests, bot loadouts, loot spawns, and weapon presets. | Re-enabled on SPT02 and local `C:\SPT` after SVM changes on 2026-06-07. Forge lists a Fika-compatible version and warns the mod may make profile-impacting changes. Requires WTT CommonLib and matching `WTT-ArmoryClient` files on players/headless. |
| `WTT-ContentBackport` | [WTT - Content Backport](https://forge.sp-tarkov.com/mod/2512/wtt-content-backport) | 1.0.7 | Backports EFT 1.0 content into SPT, including large content bundles and supporting database changes. | Forge has a Fika-compatible version available. Requires matching server/client/headless components. |
| `archangelwtf-contentbackportprestiges` | [Content Backport - Prestiges](https://forge.sp-tarkov.com/mod/2540/content-backport-prestiges) | 1.0.1 | Extends prestige progression for Content Backport. | Depends on WTT CommonLib and Content Backport. |
| `archangelwtf-lotsoflootredux` | [Lots of Loot Redux](https://forge.sp-tarkov.com/mod/1619/lots-of-loot-redux) | 4.0.3 | Rebalances loose/container loot to make raids less loot-starved. | Forge marks compatible versions as Fika-compatible. |
| `acidphantasm-bosseshavegpcoins` | [Bosses Have GP Coins](https://forge.sp-tarkov.com/mod/2523/bosses-have-gp-coins) | 1.0.0 | Gives bosses a configurable chance to carry GP coins. | Lightweight server-side loot tweak. |
| `acidphantasm-bosseshavelegamedals` | [Bosses Have Lega Medals](https://forge.sp-tarkov.com/mod/1539/bosses-have-lega-medals) | 2.0.1 | Gives bosses a configurable chance to carry Lega medals. | Lightweight server-side loot tweak. |
| `acidphantasm-enablelabyrinth` | [Enable Labyrinth](https://forge.sp-tarkov.com/mod/2416/enable-labyrinth) | 1.0.2 | Enables Labyrinth for PMC and Scav access and adds supporting extraction/config behavior. | Forge has a Fika-compatible version available. |
| `acidphantasm-reffriendlyquests` | [Ref - SPT Friendly Quests](https://forge.sp-tarkov.com/mod/1538/ref-spt-friendly-quests) | 2.0.3 | Converts Arena-specific Ref quests into SPT-friendly quest flow and rewards. | Forge has a Fika-compatible version available. |
| `acidphantasm-stattrack` | [StatTrack](https://forge.sp-tarkov.com/mod/1853/stattrack) | 2.0.0 | Tracks weapon kills and headshots on individual weapons. | Forge notes not to install this on the headless client. Keep it out of headless BepInEx plugins. |
| `BalancedMeds` | [BALANCED MEDS](https://forge.sp-tarkov.com/mod/179/balanced-meds) | 4.0.61 | Changes medical item uses and healing behavior. | Profile-impacting item stat mod. Test carefully with other medical/consumable mods. |
| `BarterItemsStacks` | [BarterItemsStacks](https://forge.sp-tarkov.com/mod/2480/barteritemsstacks) | 1.3.2 | Changes stack sizes for barter items and generates a configurable `config.jsonc`. | Forge lists Fika compatibility as unknown. Installed on SPT02 and local `C:\SPT`; SPT backend restarted cleanly and generated config without BarterItemsStacks errors. Players should install the matching client DLL when using this modded setup. |
| `BoxesAtRef` | [Boxes At Ref (BARF) - NG](https://forge.sp-tarkov.com/mod/2483/boxes-at-ref-barf-ng) | 2.0.0 | Adds Arena loot boxes and related items to Ref. | Server-side trader/item mod. |
| `CaliberSplitMagazineCases` | [Caliber Split Magazine Cases](https://forge.sp-tarkov.com/mod/2278/caliber-split-magazine-cases) | 2.0.1 | Adds caliber-specific magazine cases for organizing magazines. | Forge has a Fika-compatible version available. |
| `EFCL-WelcomeGifts` | [Welcome Gifts](https://forge.sp-tarkov.com/mod/740/welcome-gifts) | 4.0.0 | Adds BSG gift packages into SPT. | Requires WTT CommonLib. |
| `EventAutoProfileBackup` | [Event Auto Profile Backup](https://forge.sp-tarkov.com/mod/1973/event-auto-profile-backup) | 2.0.0 | Creates event-driven profile backups during client/server lifecycle events. | Good operational safety net before adding/removing profile-impacting mods. |
| `MC-MXLR` | [Marlin MXLR .308 ME Lever-Action Rifle](https://forge.sp-tarkov.com/mod/2484/marlin-mxlr-308-me-lever-action-rifle) | 1.2.0 | Adds the Marlin MXLR .308 ME lever-action rifle from EFT 1.0. | Forge lists Fika compatibility as unknown. Test weapon/content sync. |
| `MergeConsumablesServer` | [MergeConsumables](https://forge.sp-tarkov.com/mod/1657/mergeconsumables) | 1.5.4 | Allows merging limited-use consumables such as meds and food. | Use with [MergeConsumables - Fika sync](https://forge.sp-tarkov.com/addon/4/mergeconsumables-fika-sync) when clients need Fika sync behavior. |
| `MoreCheckmarksBackend` | [MoreCheckmarks](https://forge.sp-tarkov.com/mod/861/morecheckmarks) | 2.1.0 | Adds richer item checkmarks/tooltips for quest, hideout, barter, wishlist, and other item needs. | Forge has a Fika-compatible version available. Requires matching client plugin for UI value. |
| `mpstark-dynamicmaps` | [Dynamic Maps](https://forge.sp-tarkov.com/mod/1431/dynamic-maps) | 1.1.3 | Replaces in-game map screens with dynamic map data such as extracts, quests, markers, and other overlays. | Server component must be installed for Fika usage; players need the matching client plugin. |
| `RaidReview` | [Raid Review](https://forge.sp-tarkov.com/mod/1479/raid-review) | 1.1.1 | Web-based post-raid review/replay system with positional data, kills, looting, and heatmap-style analysis. | Forge has a Fika-compatible version available. Watch for database/runtime errors after updates. |
| `Sicc Case Fix` | [Sicc Case Fix](https://forge.sp-tarkov.com/mod/2687/sicc-case-fix) | 1.0.1 | Fixes SICC case handling for prestige 3 and 4 dog tags. | Small server-side item compatibility fix. |
| `SNACC` | [SNACC Pack](https://forge.sp-tarkov.com/mod/2448/snacc-pack) | 1.0.0 | Adds a food/drink storage pouch. | Requires WTT CommonLib. Forge has a Fika-compatible version available. |
| `SPTModViewer` | [SPTModViewer](https://forge.sp-tarkov.com/mod/2514/sptmodviewer) | 0.3.0 | Tracks installed mod status relative to Forge metadata. | Troubleshooting helper. Forge has a Fika-compatible version available. |
| `utjan.AirFilterOnlyDrainsInRaid` | [Air Filter Only Drains In Raid](https://forge.sp-tarkov.com/mod/2532/air-filter-only-drains-in-raid) | 1.0.0 | Makes hideout air filters drain only during PMC raids. | Server/client hideout QoL mod. |
| `WTT-PackNStrap` | [WTT - Pack 'N Strap](https://forge.sp-tarkov.com/mod/1278/wtt-pack-n-strap) | 2.0.4 | Adds belt/container functionality and related inventory content. | Re-enabled on 2026-06-08 after installing `UseItemsFromAnywhere.dll` and restoring PackNStrap/BeltSlot BepInEx plugins on SPT02 and local. Backend and headless startup validated. |

### Active SPT02 Headless Plugins

Current active headless BepInEx plugins:

- `BarterItemsStacksClient.dll`
- `DrakiaXYZ-BigBrain.dll`
- `DrakiaXYZ-Waypoints`
- `Fika`
- `spt`
- `HomelabFikaHeadlessCrcFix`
- `JBOBYH`
- `RaiRai.ColorConverterAPI.dll`
- `QuestsExtended`
- `SAIN`
- `TTC.dll`
- `tarkin-ladders`
- `UnityToolkit`
- `UseItemsFromAnywhere.dll`
- `WTT-ArmoryClient`
- `WTT-ClientCommonLib`
- `WTT-ContentBackportClient`
- `WTT-PackNStrap`

Active headless BepInEx patchers include:

- `spt-prepatch.dll`

Climbable Ladders is installed as `BepInEx\plugins\tarkin-ladders` on SPT02/headless and local `C:\SPT`:

| Plugin folder | Forge mod | Version | Note |
| --- | --- | --- | --- |
| `BepInEx\plugins\tarkin-ladders` | [Climbable Ladders](https://forge.sp-tarkov.com/mod/2649/climbable-ladders) | 1.0.2 | Installed on SPT02 and local `C:\SPT` on 2026-06-08. Forge has a Fika-compatible version available. |

TTC requires Color Converter API, Quests Extended, and Item Preview QoL. TTC and those client-side pieces are installed on both SPT02/headless and the local `C:\SPT` client. Backups from the install are under `C:\SPT\_migration-backups\ttc-install-20260607-154320` locally and `C:\SPT\_migration-backups\ttc-install-20260607-154342` on SPT02.

### Local Client-Only Mods

These are installed on Adam's local `C:\SPT` client but intentionally not installed on the SPT02 headless host:

| Local folder | Forge mod | Version | Reason |
| --- | --- | --- | --- |
| `BepInEx\plugins\MoxoPixel.MenuOverhaul` | [WTT - Menu Overhaul](https://forge.sp-tarkov.com/mod/1775/wtt-menu-overhaul) | 1.2.1 | Menu/UI overhaul for the local player client. It is not needed on the headless raid host and should stay off SPT02 unless Fika validation proves it is required. |

### Disabled Or Quarantined Mods

These are intentionally disabled because they caused Fika/headless startup problems, client compatibility problems, or are known to be incompatible with the current Fika setup:

| Mod | Reason |
| --- | --- |
| `DiscordRaidMap` | Disabled again on 2026-06-08 after the SPT02 headless client crashed during raid startup with Discord Raid Map enabled. A local lab patch was tested that changed the plugin version to `1.0.1` and added `Initial Delay Seconds = 30`, but the headless client still crashed after the patched build loaded. Quarantined on SPT02 under `C:\SPT\_disabled-headless\discord-raid-map-headless-unstable-20260608-105554`. The config file may still exist under `C:\SPT\BepInEx\config\com.fiodor.discordraidmap.cfg`; do not store the webhook value in Git or Wiki.js. |
| `MoreBotsAPI` / `MoreBotsServer` | Disabled on 2026-06-08 after the SPT02 headless client restarted/crashed during Reserve raid initialization. The previous BepInEx log showed `System.NullReferenceException` in `MoreBotsAPI.Patches.BotsControllerInitPatch.PatchPostfix` during bot controller initialization. Quarantined on SPT02 under `C:\SPT\_disabled-headless\morebots-blackdiv-raidinit-crash-20260608-124634`; local client copy is quarantined under `C:\SPT\_disabled-client-baseline\morebots-blackdiv-raidinit-crash-20260608-125316`. |
| `WTT - Black Division [REDACTED] Home` / `BlackDivServer` | Disabled with MoreBotsAPI on 2026-06-08 because Black Division depends on MoreBotsAPI and was the active custom bot stack when the headless client crashed during bot initialization. Quarantined in the same SPT02/local folders as MoreBotsAPI. |
| `SamSWAT.FireSupport.ArysReloaded` | Do not enable. Forge marks this mod Fika-incompatible, and it remained disabled after the 2026-06-07 mod restore. Quarantined on SPT02 under `C:\SPT\_disabled-headless\firesupport-disabled-20260607-184211`; local client plugin/config are quarantined under `C:\SPT\_disabled-client-baseline\firesupport-disabled-20260607-184148` and `C:\SPT\_disabled-client-baseline\firesupport-incompatible-redisable-20260607-203438`. |
| `FPVDroneMod` | Generated unsupported `DroneItem` taxonomy type |
| `SkillsExtended` BepInEx client plugin | Threw a missing field error on the headless/client side |
| `netVnum.Pause.dll` | Not appropriate for co-op raid hosting |

`WTT-PackNStrap` previously generated an unsupported `CustomContainerTemplate` taxonomy error when only the server mod was restored. On 2026-06-08 it was re-enabled successfully after installing `UseItemsFromAnywhere.dll` and restoring both `WTT-PackNStrap.dll` and `Trenchfoot-BeltSlot.dll` under `BepInEx\plugins\WTT-PackNStrap` on SPT02/headless and the local client.

The server-side `SkillsExtended` mod remains enabled on SPT02 for profile compatibility.

The following mods were temporarily disabled during the 2026-06-07 troubleshooting pass and then restored after the imported `Chadnovski` profile was removed from SPT02: `Solarint-SAIN-ServerMod`, `SAIN`, `DrakiaXYZ-BigBrain.dll`, `DrakiaXYZ-Waypoints`, `WTT-Artem`, `Tyfon.UIFixes.Server`, `Tyfon.UIFixes.dll`, `TTC`, `WTT-ContentBackport`, `archangelwtf-contentbackportprestiges`, `MC-MXLR`, `EFCL-WelcomeGifts`, and `SNACC`.

### Profile Cleanup Notes

On 2026-06-07, the local `Chadnovski` profile still contained stale `WTT-Artem` inventory data after `WTT-Artem` was disabled on SPT02. Fika crashed the headless host during Factory load because the local client sent a profile containing item instance `6a224d1f643943abf019d3c3` with missing template `6673b1ac5cae0610f1079d76`.

The local profile was backed up and cleaned:

```text
C:\SPT\_migration-backups\profile-cleanup-artem-20260607-1948\6a1f4c94ed07eef6542364cd.json
```

Only that stale Artem item was removed from:

```text
C:\SPT\SPT\user\profiles\6a1f4c94ed07eef6542364cd.json
```

After repeated Fika headless crashes, an older imported `Chadnovski` profile was removed from active SPT02 service on 2026-06-07 so a new clean profile could be created:

```text
C:\SPT\_disabled-headless\removed-profiles-20260607-203533\6a1f4c94ed07eef6542364cd.json
```

On 2026-06-08, Adam's current local `Chadnovski` level 21 profile was re-imported from:

```text
C:\SPT\SPT\user\profiles\6a1f4c94ed07eef6542364cd.json
```

to the same active profile path on SPT02. The previous SPT02 copy was backed up under:

```text
C:\SPT\_mod-install-backups\discord-raid-map-profile-import-20260608-100754
```

## SVM

SVM is installed server-side on SPT02:

```text
C:\SPT\SPT\user\mods\[SVM] Server Value Modifier
```

Apply SVM changes from the SVM tool, save the profile, apply it, then restart SPT/Fika with the operator script.

## Remote Management

SPT02 can be managed remotely from `ai-workstation-evox2` with WinRM or OpenSSH.

Secrets:

- OpenBao path: `secret/homelab/vms/spt02`
- Bootstrap keys: use `SPT02_HOST` for the host when present; current automation can still resolve the shared SPT admin credentials from `SPT01_USER` and `SPT01_PASSWORD` because SPT02 was built with the same local administrator account.

Management access:

- WinRM: PowerShell remoting to `192.168.1.86`
- OpenSSH: `helios@192.168.1.86`
- Default SSH shell: Windows PowerShell 5.1
- Authorized source: `helios@ai-workstation-evox2`

OpenSSH test from AI workstation:

```bash
ssh helios@192.168.1.86 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status"
```

## Operator Scripts

SPT02 has local automation under:

```text
C:\SPT\automation
```

Main non-interactive script:

```text
C:\SPT\automation\Invoke-SPT02-FikaAction.ps1
```

Valid actions:

- `Status`
- `Start`
- `Stop`
- `Restart`

Examples on SPT02:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Restart
```

Examples from AI workstation:

```bash
ssh helios@192.168.1.86 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Restart"
```

Interactive desktop menu:

```text
C:\SPT\automation\Manage-SPT02-Fika.ps1
```

Desktop shortcut:

```text
C:\Users\helios\Desktop\SPT02 Fika Server Manager.lnk
```

Startup helper:

```text
C:\SPT\automation\Start-FikaHeadlessAfterServer.ps1
```

Scheduled tasks:

- `SPT02-SPT-Server`
- `SPT02-Fika-Headless`

The headless scheduled task waits for the SPT backend readiness endpoint before starting the Fika headless manager.

## Hermes And Discord Operations

Hermes on `ai-workstation-evox2` can run the non-interactive SSH command against SPT02. This enables Discord-driven or Hermes web UI-driven operations.

Expected operator intents:

- Start SPT/Fika
- Stop SPT/Fika
- Restart SPT/Fika
- Report SPT/Fika status

Hermes should use the non-interactive script, not the interactive menu.

Canonical command pattern:

```bash
ssh helios@192.168.1.86 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Restart"
```

Replace `Restart` with `Status`, `Start`, or `Stop` when needed.

Example Discord prompt:

```text
@Helios please restart the SPT/Fika stack on SPT02 using the documented non-interactive SSH command, then report whether the backend is ready and whether the Fika headless endpoint shows a registered headless client.
```

## Troubleshooting

### Backend Is Up But Headless Does Not Show

Check status:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status
```

Check BepInEx log:

```powershell
Get-Content C:\SPT\BepInEx\LogOutput.log -Tail 200
```

Common causes:

- Headless is still loading or caching custom bundles.
- A BepInEx plugin failed before Fika validation.
- The backend item database contains custom taxonomy types unsupported by the client.
- Fika plugin CRC mismatch between player and host.

### Player Can Reach SPT But Cannot Join Raid

Check:

- Is the player connected to the WireGuard VPN?
- Can the player reach `https://192.168.1.86:6969`?
- Is the selected raid host SPT02 headless or a player PC?
- Is UDP `25565` reachable on the selected raid host?
- Does Windows Firewall allow inbound UDP `25565` from `192.168.86.0/24` and `192.168.1.0/24`?
- Do all players have matching Fika versions?
- Are extra client plugins either removed or allowed through Fika required/optional plugin configuration?

### SPT02 Network Drops

Previous mitigations:

- Disabled Windows sleep and hibernation.
- Disabled disk idle timeout.
- Disabled NIC power management.

If drops return, check the physical NIC, switch port, and cabling before changing SPT/Fika configuration.

## Source Files In This Repo

- `automation/spt02/Invoke-SPT02-FikaAction.ps1`
- `automation/spt02/Manage-SPT02-Fika.ps1`
- `automation/spt02/Start-FikaHeadlessAfterServer.ps1`
- `automation/spt02/SPT02-Fika-Server-Manager.cmd`
- `automation/wikijs/scripts/upsert-spt-fika-page.ps1`
- `docs/spt-fika-runbook.md`
