# Home Lab AI Baseline Context

Last updated: 2026-06-20 13:15 (America/Chicago)

## Purpose

This repository is the baseline operational context for the home lab. It is intended to be AI-ingestable and kept current as infrastructure changes.

## AI Workspace Model

This `lab` repo is the primary AI workspace for operations, infrastructure, and ticket-driven delivery.

Standard workflow conventions:

1. Durable context and standards live in root context files.
2. Active code work happens under `repositories/` (agent clones/uses target repos here).
3. Temporary ticket execution artifacts live under `tmp/`.
4. Each ticket gets its own folder and local context file:
   - Folder: `tmp/<ticket-number>/`
   - Context file: `tmp/<ticket-number>/<ticket-number>-context.md`
   - Example: `tmp/DEVOPS-142/DEVOPS-142-context.md`

## Source of Truth Files

- `network_devices.csv`: canonical network inventory and device metadata.
- `.env`: credentials and secrets (never commit to git).
- `automation/common/SecretResolver.psm1`: shared OpenBAO-first secret resolution module.
- `automation/secrets/scripts/sync-env-to-openbao.ps1`: sync `.env` bootstrap values into OpenBAO KV v2.
- `automation/agent/scripts/bootstrap-lab-context.ps1`: mandatory agent bootstrap entrypoint.
- `k8s/helm/*` and `k8s/manifests/*`: deployment definitions for lab services.
- `automation/n8n/*`: n8n workflow exports/templates and API helper scripts.
- `automation/netbox/*`: NetBox IPAM + asset sync scripts.
- `automation/unifi/*`: UniFi (UDM Pro) inventory fetch + NetBox sync scripts.
- `automation/wikijs/*`: Wiki.js API automation scripts.
- `automation/ai-workstation/*`: AI workstation automation and Strix Halo backend sync scripts.
- `sub-context/ai-infrastructure-context.md`: infrastructure-specific supplemental context.
- `phase1-agent-todo.md`: first-phase execution backlog for agent platform, knowledge system, and automation control plane.
- `phase1-agent-queue.yaml` + `phase1-agent-queue.json`: machine-readable execution queue for agent task orchestration.
- `repositories/`: workspace for repos the agent clones/pulls for implementation work.
- `tmp/`: transient ticket working area (`tmp/<ticket-number>/<ticket-number>-context.md` pattern).

## Repo Layout

```text
lab/
  ai-baseline-context.md
  sub-context/
    ai-infrastructure-context.md
  network_devices.csv
  .env                      # gitignored (secrets)
  .gitignore
  .kubeconfig-192.168.1.80.yaml
  repositories/             # agent code workspace (cloned repos, feature work)
  tmp/                      # ticket temp workspace
    <ticket-number>/
      <ticket-number>-context.md
  automation/
    n8n/
      README.md
      scripts/
        export-workflows.ps1
        import-workflow.ps1
      workflows/
        exports/
        templates/
    netbox/
      README.md
      scripts/
        sync-network-devices-to-netbox.ps1
        sync-netbox-assets-from-csv.ps1
    unifi/
      README.md
      data/
        unifi-inventory-latest.json
      scripts/
        fetch-unifi-inventory.ps1
        sync-unifi-to-netbox.ps1
    wikijs/
      scripts/
        upsert-registry-page.ps1
    ai-workstation/
      README.md
      scripts/
        sync-strix-halo-backend.ps1
    common/
      SecretResolver.psm1
    secrets/
      README.md
      scripts/
        sync-env-to-openbao.ps1
    agent/
      scripts/
        bootstrap-lab-context.ps1
  k8s/
    helm/
      argocd/
      cert-manager/
      falco/
      grafana/
      loki/
      minio/
      n8n/
      netbox/
      opencost/
      prometheus/
      velero/
      external-secrets/
      openbao/              # legacy values; chart currently incompatible with k3s 1.28
    manifests/
      openbao/
        openbao-dev.yaml
      external-secrets/
        openbao/
          store-and-sample.yaml
```

## Network Inventory Model (`network_devices.csv`)

Current columns:

- `IPAddress`
- `HostOctet`
- `UsableHost`
- `Reachable` (ICMP perspective)
- `LatencyMs`
- `Hostname`
- `CheckedAt`
- `Name`
- `Description`
- `Notes`
- `CredentialRef` (keys in `.env`)
- `MgmtReachable`
- `LastUpdated`

### Update Rules

1. Keep `network_devices.csv` as inventory source of truth.
2. Update `Name`, `Description`, `Notes`, and `CredentialRef` when a device is identified.
3. Store only credential key references in CSV/Markdown.
4. Include infra outside `192.168.1.0/24` when relevant.
5. Update `LastUpdated` on every manual edit.
6. NetBox is the system-of-record for modeled assets (Devices/VMs, interfaces, primary IP relationships) after sync.

## Current Environment Facts

### Home Lab Layout Summary

- Primary LAN: `192.168.1.0/24`
- Gateway/router: UniFi Dream Machine Pro Max at `192.168.1.1`
- Core switch management: Cisco Catalyst 2960X at `192.168.1.2`
- k3s cluster control plane: `oma01rpicls01mstr01` at `192.168.1.80`
- k3s worker nodes: `192.168.1.81-84`
- Secrets backend: `lab-secrets01` at `192.168.1.25`, OpenBao API `http://192.168.1.25:8200`
- PostgreSQL service host: `lab-pgsql01` at `192.168.1.216`
- Container registry host: `lab-registry01` at `192.168.1.15:5000`
- AI workstation: `ai-workstation-evox2` at `192.168.1.123`
- SPT/Fika server host: `SPT02` at `192.168.1.86`
- Most k3s web services are exposed either by NodePort on `192.168.1.80` or Traefik ingress with `*.192.168.1.80.sslip.io` hostnames.

### Network

- Primary LAN: `192.168.1.0/24`
- Gateway/router: Ubiquiti UniFi Dream Machine Pro Max (`192.168.1.1`)
- Cisco switch mgmt: `192.168.1.2/24` (migrated from `192.168.0.2/24`)

### Cisco Switch

- Device: Cisco Catalyst 2960X 48-port PoE (`csgsw01`)
- Management SVI: `Vlan1 = 192.168.1.2/24`
- Default gateway: `192.168.1.1`
- Change executed over USB console and saved with `write memory`.

### k3s Cluster

- Control-plane: `oma01rpicls01mstr01` (`192.168.1.80`)
- Control-plane status: `Ready`
- k3s upgraded on 2026-04-12: `v1.28.8+k3s1` -> `v1.28.15+k3s1`
- OS package updates applied on control-plane (Debian 12 + Raspberry Pi package refresh)

Workers (all currently `Ready`):

- `oma01rpicls01wknd01` (`192.168.1.81`)
- `oma01rpicls01wknd02` (`192.168.1.82`)
- `oma01rpicls01wknd03` (`192.168.1.83`)
- `oma01rpicls01wknd04` (`192.168.1.84`)

Worker recovery note:

- Worker inventory addressing was corrected to `192.168.1.81-84` on 2026-04-13.
- Worker `K3S_URL` references were corrected from `192.168.0.180` to `192.168.1.80` and agent services restarted (2026-04-30).

### Rancher

- Rancher VM host: `rancherweb01` (`192.168.1.79`)
- Rancher webhook issue fixed on 2026-04-12:
  - `rancher-webhook` pod now healthy on master
  - service endpoints are populated
  - namespace creation admission works again
- Deployment pinned to master node selector to avoid scheduling back onto unreachable worker nodes.

### PostgreSQL Service Host

- Host: `lab-pgsql01` (`192.168.1.216`, Ubuntu 24.04 LTS)
- Networking: static `192.168.1.216/24`, gateway `192.168.1.1` (netplan; cloud-init netplan disabled)
- PostgreSQL service is active and listening on `0.0.0.0:5432`
- Access controls:
  - `password_encryption = scram-sha-256`
  - `pg_hba.conf` allows `192.168.1.0/24` with `scram-sha-256`
  - UFW enabled with `5432/tcp` restricted to `192.168.1.0/24`
- Bootstrap objects:
  - admin role: `lab_admin` (LOGIN, CREATEDB)
  - default database: `lab_platform`
  - application database: `wikijs` with role `wikijs`
- Credential references:
  - SSH: `LAB-PGSQL01_*`
  - Database: `LAB_PGSQL01_DB_*`

### Secrets Service Host

- Host: `lab-secrets01` (`192.168.1.25`, Ubuntu 24.04 LTS)
- Networking: static `192.168.1.25/24`, gateway `192.168.1.1` (netplan; cloud-init netplan disabled)
- OpenBao service:
  - binary/service install: `openbao` (`bao`) `2.5.3`
  - systemd unit: `openbao` (enabled, active)
  - storage backend: local file storage (`/opt/openbao/data`)
  - API listener: `http://192.168.1.25:8200`
  - initialization: completed (Shamir 1/1), instance currently unsealed
  - secrets engine: `secret/` mounted as KV v2
  - `.env` bootstrap snapshot path: `secret/homelab/bootstrap/env`
  - curated runtime/service paths in use:
    - `secret/homelab/services/n8n`
    - `secret/homelab/services/netbox`
    - `secret/homelab/services/unifi`
    - `secret/homelab/registry/lab-registry01`
    - `secret/lab/runtime/*` (legacy runtime path still in use for some services including Wiki.js DB credentials)
  - agent policies: `lab-context-read` (read/list env) and `lab-deploy-write` (read env + write runtime)
  - ESO policy/token: `eso-read-lab` with token stored in k8s secret `external-secrets/openbao-eso-token`
  - firewall: `8200/tcp` allowed from `192.168.1.0/24`
- Credential references:
  - SSH: `LAB_SECRETS01_*`
  - OpenBao: `LAB_SECRETS01_OPENBAO_*`

### Container Registry Host

- Host: `lab-registry01` (`192.168.1.15`, Ubuntu 24.04 LTS)
- Networking: static `192.168.1.15/24`, gateway `192.168.1.1`
- Runtime:
  - Docker Engine `29.4.1`
  - Docker Registry v2 container (`registry`) listening on `:5000`
- Endpoint: `http://192.168.1.15:5000`
- Storage/auth paths:
  - data: `/opt/registry/data`
  - auth file: `/opt/registry/auth/htpasswd`
  - compose: `/opt/registry/docker-compose.yml`
- Credential references:
  - SSH: `LAB_REGISTRY01_*`
  - Registry auth: `LAB_REGISTRY01_REGISTRY_*`

### AI Workstation

- Host: `ai-workstation-evox2` (`192.168.1.123`, Fedora 43, AMD Strix Halo / Radeon 8060S)
- SSH: key-based access validated from Windows; management user references in `.env` as `AI_WORKSTATION_*`
- Sudo password source of truth: OpenBao KV v2 path `secret/homelab/bootstrap/env`, field `AI_WORKSTATION_PASSWORD`; do not store the password in git or Markdown.
- Dedicated AI storage: `/mnt/ai` (btrfs subvolume, persistent via `/etc/fstab`)
- AI data directories:
  - `/mnt/ai/models`
  - `/mnt/ai/ollama`
  - `/mnt/ai/llama`
  - `/mnt/ai/qdrant`
  - `/mnt/ai/docker`
  - `/mnt/ai/logs`
  - `/mnt/ai/agent`
  - `/mnt/ai/voice`
  - `/mnt/ai/open-webui`
- Runtime/services (validated 2026-05-23):
  - `ollama` systemd service active (`0.21.2`)
  - `qdrant` active via Docker (`http://192.168.1.123:6333`)
  - `open-webui` active via Docker (`http://192.168.1.123:3000`)
  - local tool-calling agent active (`http://192.168.1.123:8777/health`)
  - cockpit socket active (`https://192.168.1.123:9090`)
  - `hermes-gateway` user systemd service active (`Hermes Agent v0.13.0 / 2026.5.7`)
    - Model: `hermes-qwen3-coder:30b-64k` via local Ollama OpenAI-compatible endpoint (`http://127.0.0.1:11434/v1`)
    - Runtime model alias points to `qwen3-coder:30b-a3b-q8_0` with `PARAMETER num_ctx 65536`; Hermes config also sets `model.context_length=65536` and `model.ollama_num_ctx=65536`.
    - Latency note: raw Ollama response for a trivial prompt is fast with the capped alias, but full Hermes browser/CLI chat remains dominated by tool-enabled agent prompt overhead. Simple chat without toolsets tested much faster than tool-enabled chat.
    - OpenBao env injected through systemd drop-in with read-only policy `hermes-bootstrap-env-read`; helper command `openbao-env-get FIELD_NAME` reads fields from `secret/homelab/bootstrap/env`.
    - Hermes sudo support: Hermes expects `SUDO_PASSWORD` in the process environment, not in `config.yaml`. Both Hermes services are started through `/home/helios/.local/bin/hermes-openbao-sudo-env`, which resolves `AI_WORKSTATION_PASSWORD` from OpenBao and exports it as `SUDO_PASSWORD` before launching Hermes.
    - Hermes sudo drop-ins:
      - `/home/helios/.config/systemd/user/hermes-gateway.service.d/30-sudo-password-openbao.conf`
      - `/home/helios/.config/systemd/user/hermes-dashboard.service.d/30-sudo-password-openbao.conf`
  - `hermes-dashboard` user systemd service active, bound to `127.0.0.1:9119` for SSH-tunneled browser access
  - `lab-update-check.timer` user systemd timer active; runs weekly Saturday morning with jitter and writes update-check logs to `/mnt/ai/logs/system-updates/latest.log`. This checks for package updates only; it does not perform unattended upgrades.
  - `openclaw-gateway` user systemd service installed but disabled/inactive as of 2026-05-09 while Hermes Discord connectivity is being tested (`OpenClaw 2026.5.7`, loopback `127.0.0.1:18789`, token-auth)
  - OpenClaw Discord channel validated on 2026-05-09: bot token resolved as `Helios`, configured `helios` Discord channel readable, gateway restarted after stale process cleanup.
- Workstation package updates applied on 2026-05-23 via `dnf5 upgrade --refresh` (kernel and userspace updates included).
- Kernel note: `7.0.9-105.fc43` is installed; workstation is still running `7.0.8-100.fc43` until the next reboot.
- Installed Ollama models:
  - `hermes-qwen3-coder:30b-64k` (local alias, 64k context cap for Hermes)
  - `hermes-qwen3-coder:latest-64k` (local alias, lower-precision 64k comparison)
  - `qwen3-coder:30b-a3b-q8_0`
  - `qwen3-coder:latest`
  - `gpt-oss:120b`
  - `gemma4:latest`
  - `qwen2.5vl:7b`
  - `nomic-embed-text:latest`
  - `qwen2.5:1.5b`
  - `llama3.2:1b`
  - `tinyllama:latest`
- `llama.cpp` built and installed from source with Vulkan support (`/usr/local/bin/llama-cli`)

### SPT/Fika Server

- Host: `spt02` (`192.168.1.86`, Windows 10 Pro physical host)
- Purpose: Dedicated SPT/Fika backend and Fika headless host for Single Player Tarkov co-op hosting.
- Migration note: `spt02` replaces the previous `spt01` ESXi VM because the VM was too slow for reliable Fika headless hosting.
- Network:
  - Primary LAN IP: `192.168.1.86/24`
  - Gateway: `192.168.1.1`
  - SPT/Fika backend endpoint: `https://192.168.1.86:6969`
  - Fika headless endpoint check: `https://192.168.1.86:6969/fika/headless/get`
  - OpenSSH Server: `22/tcp`
  - WinRM: `5985/tcp`
- Remote player VPN:
  - UDM WireGuard server: `SPT-Fika-WireGuard`
  - VPN subnet/server address: `192.168.86.1/24`
  - WireGuard listener: `51820/udp` on WAN
  - DNS pushed to VPN clients: `192.168.1.1`
  - Add player client profiles in UniFi Network under Settings > VPN > VPN Server > `SPT-Fika-WireGuard` > Add Client, then share the generated WireGuard config out of band.
  - Router firewall rules on UDM classic `LAN_IN`:
    - `SPT Fika VPN allow backend TCP 6969`: `192.168.86.0/24` -> `192.168.1.86:6969/tcp`
    - `SPT Fika VPN allow raid UDP 25565`: `192.168.86.0/24` -> `192.168.1.86:25565/udp`
    - `SPT Fika VPN drop other LAN access`: drops `192.168.86.0/24` -> `192.168.1.0/24`
  - SPT02 Windows Firewall allows Fika ports only from `192.168.1.0/24` and `192.168.86.0/24`.
  - Do not expose SPT/Fika with direct WAN port forwards.
- Host power/network stability:
  - Windows sleep, hibernate, disk idle sleep, and hybrid sleep should remain disabled for server hosting.
  - NIC power saving should remain disabled so Windows does not drop the network adapter during idle periods.
- Documentation:
  - Wiki.js page: `https://wikijs.192.168.1.80.sslip.io/en/services/spt02`
  - Wiki upsert automation: `automation/wikijs/scripts/upsert-spt-fika-page.ps1`
- Credentials:
  - Bootstrap `.env` keys: use `SPT02_HOST` for the host when present; current automation can still resolve the shared SPT admin credentials from `SPT01_USER` and `SPT01_PASSWORD` because SPT02 was built with the same local administrator account.
  - Dedicated OpenBao KV v2 path: `secret/homelab/vms/spt02`
  - Dedicated OpenBao fields: `host`, `username`, `password`, `ssh_user`, `ssh_host`
  - Do not put the SPT02 password in docs, Git, Wiki.js, Slack, Discord, or command logs.
- Installed paths on `SPT02`:
  - SPT/Fika root: `C:\SPT`
  - SPT backend: `C:\SPT\SPT\SPT.Server.exe`
  - Original EFT files: `C:\Battlestate Games\Escape From Tarkov`
  - Fika headless manager: `C:\SPT\FikaHeadlessManager.exe`
  - Operator automation: `C:\SPT\automation`
  - Disabled copied desktop mods:
    - `C:\SPT\_disabled-headless\baseline-20260605-141312`
    - `C:\SPT\_disabled-headless\baseline-cleanup-20260605-151018`
    - `C:\SPT\_disabled-headless\baseline-profile-cache-cleanup-20260605-151323`
  - Active baseline mods:
  - BepInEx plugins: `Fika`, `spt`
  - Added BepInEx plugins:
    - `HomelabFikaHeadlessCrcFix` (`C:\SPT\BepInEx\plugins\HomelabFikaHeadlessCrcFix`)
    - `JBOBYH`, `RaiRai.ColorConverterAPI.dll`, `QuestsExtended`, `TTC.dll`, `UnityToolkit`, `WTT-ClientCommonLib`, and `WTT-ContentBackportClient`
  - BepInEx patchers: `spt-prepatch.dll`
  - Server mods include `fika-server`, `[SVM] Server Value Modifier`, `TTC`, `QuestsExtended`, WTT content/common libraries, Stat Rewards, Fika Discord Presence, and the other active mods listed in `docs/spt-fika-runbook.md`.
  - SAIN/BigBrain were disabled on 2026-06-07 while troubleshooting bots spawning but not moving/reacting, then restored after later profile/mod cleanup:
    - SPT02 quarantine: `C:\SPT\_disabled-headless\sain-bigbrain-disabled-20260607-182745`
    - Local client quarantine: `C:\SPT\_disabled-client-baseline\sain-bigbrain-disabled-20260607-182719`
    - Disabled components: `Solarint-SAIN-ServerMod`, `SAIN`, `DrakiaXYZ-BigBrain.dll`, `DrakiaXYZ-Waypoints`, and related BepInEx config files.
  - SamSWAT Fire Support disabled on 2026-06-07 during bot behavior isolation because Forge marks it Fika-incompatible:
    - SPT02 quarantine: `C:\SPT\_disabled-headless\firesupport-disabled-20260607-184211`
    - Local client quarantine: `C:\SPT\_disabled-client-baseline\firesupport-disabled-20260607-184148`
  - WTT-Artem disabled on 2026-06-07 during bot behavior isolation after logs traced item deserialization errors to Artem helmet/vest custom item IDs:
    - SPT02 quarantine: `C:\SPT\_disabled-headless\wtt-artem-disabled-20260607-192633`
    - No active local `WTT-Artem` folder was present to move.
  - Local `Chadnovski` profile cleanup on 2026-06-07:
    - Backup: `C:\SPT\_migration-backups\profile-cleanup-artem-20260607-1948\6a1f4c94ed07eef6542364cd.json`
    - Removed stale Artem item instance `6a224d1f643943abf019d3c3` with missing template `6673b1ac5cae0610f1079d76` from local `C:\SPT\SPT\user\profiles\6a1f4c94ed07eef6542364cd.json`.
    - This stale local profile item caused Fika profile deserialization errors on the headless host when entering Factory after `WTT-Artem` was removed.
  - `WTT-PackNStrap` was previously disabled because it generated unsupported `CustomContainerTemplate` taxonomy data when only the server mod was restored. It was re-enabled on 2026-06-08 after adding `UseItemsFromAnywhere.dll` and restoring the PackNStrap/BeltSlot BepInEx plugins on SPT02/headless and local `C:\SPT`; backend and headless startup validated.
  - `MergeConsumablesFika.dll` was installed on SPT02/headless and local `C:\SPT` on 2026-06-08 after live raid logs showed Fika inventory conversion exceptions in `ItemControllerExecutePacket` / `ObservedInventoryController.CreateOperationFromDescriptor`. Keep `MergeConsumables.dll`, `MergeConsumablesFika.dll`, and `MergeConsumablesServer` together so custom merge operations use the dedicated Fika sync packet instead of Fika's generic inventory operation path.
  - `LootNET` 1.0.6 was installed on SPT02/headless and local `C:\SPT` on 2026-06-08:
    - SPT02/local client plugin: `C:\SPT\BepInEx\plugins\LootNet`
    - SPT02/local server mod: `C:\SPT\SPT\user\mods\LootNetServer`
    - Forge page: `https://forge.sp-tarkov.com/mod/2679/lootnet`
    - Install backup path on both hosts: `C:\SPT\_mod-install-backups\lootnet-1.0.6-20260608-220720`
    - SPT02 startup validated after install: `LootNet v1.0.6 loaded`, `LootNet: loaded 6503 flea prices`, Fika plugin validation completed, and the headless websocket registered.
  - `automation/spt-client/Install-SPTFikaPlayerClient.ps1` validates expected SPT02 mod package components after setup/modpack install. The expected list includes LootNET, MergeConsumables Fika sync, WTT PackNStrap/content/Armory, Color Converter API, TTC, Climbable Ladders, Stat Rewards, Caliber Split Ammo Cases, Collector Backport Patch, Tarkov Rare Collectibles, Medical SICC Case, Handy Toolbox, and Disciples Ballistic Case Plus. Rebuild the player mod package after adding/changing required client/server mods.
  - On 2026-06-09, these server-side item/container mods were installed on SPT02 and local `C:\SPT`, then SPT02 backend startup was validated without mod-specific load errors: `CaliberSplitAmmoCases` 2.0.2, `CollectorBackportPatch` 0.1.1, `yellowdoge-tarkovrarecollectibles` 1.1.5, `MedicalSICCcase` 5.0.3, `Handy` 1.0.0, and `RepublicanJesus-DiscipleBallisticCasePlus` 1.0.0.
  - SVM source restored from `C:\SPT\_disabled-headless\baseline-20260605-141312\SPT\user\mods\[SVM] Server Value Modifier`.
  - SVM active preset: `Noname`.
  - Discord Raid Map is disabled on SPT02/headless as of 2026-06-08:
    - Disabled path: `C:\SPT\_disabled-headless\discord-raid-map-headless-unstable-20260608-105554`
    - Config path: `C:\SPT\BepInEx\config\com.fiodor.discordraidmap.cfg`
    - Patch source path on SPT02: `C:\SPT\_mod-sources\DiscordRaidMap`
    - A local lab patch was tested that changed the plugin version to `1.0.1` and added `Initial Delay Seconds = 30` so the first Discord map render/upload waits until after the Fika headless raid creation window.
    - The patched build loaded, but the SPT02 headless client still crashed during raid startup, so the mod was moved back out of active `BepInEx\plugins`.
    - Uses the shared Discord webhook URL. The webhook secret must not be written to Git, Wiki.js, Discord messages, or command logs.
  - MoreBotsAPI / Black Division are disabled on SPT02/headless and local `C:\SPT` as of 2026-06-08:
    - SPT02 quarantine: `C:\SPT\_disabled-headless\morebots-blackdiv-raidinit-crash-20260608-124634`
    - Local client quarantine: `C:\SPT\_disabled-client-baseline\morebots-blackdiv-raidinit-crash-20260608-125316`
    - Disabled components include `MoreBotsAPI`, `MoreBotsPrepatch.dll`, `MoreBotsServer`, `BlackDiv`, `BlackDiv.dll`, and `BlackDivServer`.
    - Reason: the SPT02 headless client restarted/crashed during Reserve raid initialization, and `BepInEx\LogOutput_prev.log` showed `System.NullReferenceException` in `MoreBotsAPI.Patches.BotsControllerInitPatch.PatchPostfix` during bot controller initialization.
  - TTC installed on SPT02 and local `C:\SPT` on 2026-06-07:
    - Forge page: `https://forge.sp-tarkov.com/mod/2226/ttc-tarkov-trading-cards`
    - Installed TTC version: `3.0.8`
    - Dependencies installed: Color Converter API, Quests Extended, Item Preview QoL.
    - Forge lists Fika compatibility as unknown; validated state is backend/headless startup only, not full raid behavior.
    - Install backups: local `C:\SPT\_migration-backups\ttc-install-20260607-154320`; SPT02 `C:\SPT\_migration-backups\ttc-install-20260607-154342`.
  - Desktop player profile `Chadnovski` is active on SPT02 again as of 2026-06-08. It was re-imported from local `C:\SPT\SPT\user\profiles\6a1f4c94ed07eef6542364cd.json` to SPT02 active profiles, replacing the prior SPT02 copy. The replaced SPT02 profile and Discord Raid Map state were backed up under `C:\SPT\_mod-install-backups\discord-raid-map-profile-import-20260608-100754`.
  - The generated headless profile was backed up and cleaned of invalid scav inventory items left over from copied desktop mods.
  - `C:\SPT\SPT\SPT_Data\configs\core.json` has `removeModItemsFromProfile` and `removeInvalidTradersFromProfile` enabled to strip invalid modded items/trader data if a dirty profile is loaded again.
- Operator scripts:
  - Interactive desktop menu: `C:\SPT\automation\Manage-SPT02-Fika.ps1`
  - Desktop launcher: `C:\Users\helios\Desktop\SPT02 Fika Server Manager.lnk`
  - Non-interactive action script: `C:\SPT\automation\Invoke-SPT02-FikaAction.ps1`
  - Delayed headless launcher: `C:\SPT\automation\Start-FikaHeadlessAfterServer.ps1`
  - Repo sources:
    - `automation/spt02/Manage-SPT02-Fika.ps1`
    - `automation/spt02/Invoke-SPT02-FikaAction.ps1`
    - `automation/spt02/Start-FikaHeadlessAfterServer.ps1`
    - `automation/spt02/SPT02-Fika-Server-Manager.cmd`
    - `automation/spt-client/Install-SPTFikaPlayerClient.ps1` interactive player setup, SPT02 mod-package install, timestamped mod backup/restore, and mod-package build utility.
- Scheduled tasks on `spt02`:
  - `SPT02-SPT-Server`: starts `C:\SPT\SPT\SPT.Server.exe` at `helios` logon.
  - `SPT02-Fika-Headless`: runs `C:\SPT\automation\Start-FikaHeadlessAfterServer.ps1`, waits for `https://127.0.0.1:6969/fika/headless/get`, then starts `C:\SPT\FikaHeadlessManager.exe`.
- Hermes/AI workstation control path:
  - OpenSSH Server is installed on `spt02`; default SSH shell is Windows PowerShell 5.1.
  - `helios@ai-workstation-evox2` is authorized for key-based SSH to `helios@192.168.1.86`.
  - If access from this Windows workstation to `ai-workstation-evox2` fails, use the `AI_WORKSTATION_*` keys from `.env` / OpenBao bootstrap (`secret/homelab/bootstrap/env`) and the AI Workstation Sudo Credential section below.
  - Validated from `ai-workstation-evox2`:
    - `ssh helios@192.168.1.86 hostname`
    - `ssh helios@192.168.1.86 whoami`
  - Hermes-safe command pattern:
    - `ssh helios@192.168.1.86 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status"`
    - Replace `Status` with `Start`, `Stop`, or `Restart` as needed.
  - Use the non-interactive action script for Discord/Hermes requests; do not use the interactive menu script from Hermes.
- Current validation state:
  - SSH from `ai-workstation-evox2` to `spt02` works with key-based auth.
  - The non-interactive `Status` action returns JSON over SSH.
  - SPT starts cleanly with the current active SPT02 mod set.
  - The old `/client/game/version/validate` readiness probe was removed because it caused empty-body route cast errors in SPT logs.
  - `FikaHeadlessManager.exe` and `EscapeFromTarkov.exe` remain running after startup, and `/fika/headless/get` returns the registered headless profile after the EFT headless client finishes loading.
  - Validated through `ai-workstation-evox2` SSH on 2026-06-07: `Invoke-SPT02-FikaAction.ps1 -Action Restart` restarted the stack and returned backend-ready status.
  - 2026-06-07 bot movement isolation: SAIN/BigBrain/Waypoints were removed from SPT02 and local `C:\SPT` after bots still spawned but did not move/react with the full SAIN/BigBrain/Waypoints stack active.
  - 2026-06-07 TTC validation: `[TTC] Tarkov Trading Cards` `3.0.8` installed on SPT02 and local `C:\SPT`; SPT backend loaded TTC, created cards/quests/Kolya trader data, generated loot, and Fika headless registered after restart without TTC startup errors.
  - 2026-06-08 mod additions installed on SPT02 and local `C:\SPT`: `StatRewards` 1.1.1, `tarkin-ladders` 1.0.2, `FikaDiscordPresence` 1.0.2, `BlackDivServer`/Black Division 1.1.1, `MoreBotsServer`/MoreBotsAPI 2.0.1, and `DrakiaXYZ-BigBrain.dll` 1.4.0. `BlackDivServer`/Black Division and `MoreBotsServer`/MoreBotsAPI were later disabled the same day after the headless raid-init crash described above.
  - Fika Discord Presence webhook and Fika API key are configured only on SPT02 in `C:\SPT\SPT\user\mods\FikaDiscordPresence\config.json`. The webhook URL and API key are secrets; do not write them to Git, Wiki.js, Discord messages, or command logs. The local `C:\SPT` copy remains installed but should not be configured with the webhook to avoid duplicate Discord status posts.

### Strix Halo Backend (Required)

- Backend repo: `https://github.com/kyuz0/amd-strix-halo-toolboxes`
- Remote checkout path: `/mnt/ai/llama/amd-strix-halo-toolboxes`
- Provisioned toolbox container: `llama-rocm-7.2.2`
- GPU visibility validation command:
  - `toolbox run -c llama-rocm-7.2.2 llama-cli --list-devices`
- Repo sync script:
  - `automation/ai-workstation/scripts/sync-strix-halo-backend.ps1`

## Platform Services (Live)

### PulseTrader (Planned / Not Yet Deployed)

- Purpose: safety-constrained Kalshi BTC 15-minute market experiment platform for observe/paper-first market watching, deterministic risk gating, and a modern dark second-monitor dashboard.
- Current deployment status: **not deployed to k3s yet** as of 2026-06-20. No `pulsetrader` namespace, ArgoCD Application, Service, Ingress, or live URL exists in the cluster yet.
- GitHub repository: `https://github.com/AJHeitzman/PulseTrader`
- Local lab checkout: `repositories/PulseTrader`
- AI workstation checkout: `/mnt/ai/agent/PulseTrader`
- Hermes Kanban board: `pulsetrader` (`PulseTrader`)
- Current committed implementation state:
  - Initial FastAPI API scaffold.
  - Safe runtime config defaults: `MODE=observe`, `LIVE_TRADING_ENABLED=false`.
  - Mock current market endpoint for early API scaffolding and tests.
  - Advisory-only agent analysis interface.
  - Documentation for modern dark UI design and post-deploy verification.
- Important data-provider rule:
  - Mock providers are only for tests, local offline development, deterministic demos, and CI.
  - Deployed observe/paper mode should use real read-only Kalshi/BTC market data APIs when configured.
  - UI must consume PulseTrader backend API endpoints and must not own provider selection.
- Safety model:
  - Default mode is observe only.
  - Live trading must remain disabled unless intentionally configured by the owner.
  - Any future live-limited order path must go through deterministic risk gate code.
  - LLM/Hermes/agent analysis is advisory only and must not hold Kalshi credentials, place orders, modify risk state, or bypass risk checks.
  - Market orders are forbidden by project policy.
- CI/CD target state captured in Hermes cards:
  - GitHub Actions PR checks must run on the lab self-hosted runner in k3s/ARC, not GitHub-hosted runners.
  - PR checks should include Python tests, safety/risk tests, frontend install/build/typecheck/test where applicable, manifest validation, Dockerfile validation, and practical secret-leak checks.
  - GitHub Actions image workflow should build API, worker, and UI images after tests pass.
  - Images should push to the lab registry at `192.168.1.15:5000`, using immutable commit SHA tags.
  - Expected image naming convention: `192.168.1.15:5000/lab/pulsetrader-api`, `192.168.1.15:5000/lab/pulsetrader-worker`, and `192.168.1.15:5000/lab/pulsetrader-ui` unless revised during implementation.
  - Registry credentials should come from OpenBao/GitHub Actions secrets, not committed files.
  - CD should use ArgoCD in the k3s lab, with an ArgoCD Application targeting the PulseTrader repo and k3s manifests.
- Planned k3s/GitOps target:
  - Namespace: `pulsetrader`
  - ArgoCD Application: `pulsetrader`
  - Expected dashboard URL: `https://pulsetrader.192.168.1.80.sslip.io` unless the deployment card chooses a different lab hostname.
  - Deployment should include API, worker, and UI processes with readiness/liveness probes, resource requests/limits, and safe ConfigMap defaults.
  - Traefik ingress should follow the existing lab `*.192.168.1.80.sslip.io` pattern.
- Planned OpenBao/ESO work:
  - Define PulseTrader runtime secret paths, likely `secret/homelab/services/pulsetrader` and/or `secret/lab/runtime/pulsetrader`.
  - Store Kalshi read-only credentials, optional future live credentials, provider config, and any registry/k8s secret references in OpenBao.
  - Add ESO manifests only if pods require runtime secrets.
  - Observe/paper mode must remain runnable without live Kalshi credentials.
- Planned Wiki.js page:
  - `https://wikijs.192.168.1.80.sslip.io/en/services/pulsetrader`
  - The page should include repo URL, ArgoCD app, namespace, service URL, registry images, safety defaults, provider policy, secret policy, CI/CD workflow, and rollback/post-deploy checklist links.
- Planned NetBox work:
  - Model PulseTrader only after deployment details are real. Do not invent IPs.
  - Capture service dependencies on k3s, ArgoCD, lab registry, OpenBao, Wiki.js, and optional PostgreSQL if persistence is added later.
- Key PulseTrader Kanban cards added on 2026-06-20:
  - `[CI/CD] Configure GitHub Actions PR checks on lab self-hosted runner`
  - `[CI/CD] Build PulseTrader images in GitHub Actions`
  - `[CI/CD] Push images to lab registry`
  - `[CI/CD] Wire registry credentials through OpenBao and GitHub Actions secrets`
  - `[CD] Create ArgoCD Application for PulseTrader`
  - `[CD] Finalize k3s manifests for lab deployment`
  - `[CD] Deploy and verify PulseTrader through ArgoCD`
  - `[Docs/Ops] Publish PulseTrader Wiki.js service page`
  - `[Docs/Ops] Update NetBox for PulseTrader service`
  - `[Docs/Ops] Create OpenBao runtime secret plan for PulseTrader`
  - `[Docs/Ops] Update lab baseline context after PulseTrader deployment`

Operational note for future agents:
- Do not treat PulseTrader as live until the k3s namespace, ArgoCD app, services, ingress, Wiki.js page, OpenBao paths, and NetBox updates have been verified and reflected back into this baseline.
- Before implementing PulseTrader CI/CD, inspect the existing ARC runner apps/namespaces (`arc-systems`, `arc-runners`) and use the correct self-hosted runner labels for this lab.
- Before publishing deployment manifests, replace placeholder repo URLs/hosts with `https://github.com/AJHeitzman/PulseTrader.git` and the lab hostname/registry values above.

### n8n

- Namespace: `n8n`
- Service: NodePort `31789`
- URL: `http://192.168.1.80:31789`
- Public API base: `http://192.168.1.80:31789/api/v1`
- HTTP mode kept intentionally (`N8N_SECURE_COOKIE=false`) for current LAN-only bootstrap.
- API auth key reference: `N8N_API_KEY` (stored in `.env`).
- API-created workflows currently present:
  - `8btFWCnCOFCDWc6V`: `TMP API Connectivity Check`
  - `lvHCeJc2qBvuceY8`: `Email Important Summary (API Scaffold)` (template scaffold, not production-final)

### NetBox (IPAM)

- Namespace: `netbox`
- Helm chart: `netbox/netbox` (`8.0.29`)
- Service: NodePort `32081`
- URL: `http://192.168.1.80:32081/login/`
- Worker wait-for-backend init was disabled in values to avoid rollout deadlock during first bootstrap.
- `API_TOKEN_PEPPERS` is configured via `extraConfig` secret `netbox-extra-config` to enable v2 API token creation.
- `network_devices.csv` sync helper: `automation/netbox/scripts/sync-network-devices-to-netbox.ps1`
- NetBox asset sync helper: `automation/netbox/scripts/sync-netbox-assets-from-csv.ps1`
- Current sync state (2026-04-13):
  - `258` usable hosts from CSV upserted into NetBox IP addresses and tagged `network-csv-import`.
  - `7` physical devices in `dcim/devices` with `primary_ip4` linkage.
  - `2` VMs in `virtualization/virtual-machines` with `primary_ip4` linkage:
    - `rancherweb01`
    - `lab-registry01`
  - Current VM cluster for lab guests: `homelab-vms`.

### Container Registry (Docker Registry v2)

- Host/VM: `lab-registry01` (`192.168.1.15`)
- Endpoint: `http://192.168.1.15:5000`
- Auth: basic auth (`htpasswd`)
- OpenBao credentials path: `secret/homelab/registry/lab-registry01`
- k3s integration:
  - all nodes configured with `/etc/rancher/k3s/registries.yaml` for `192.168.1.15:5000`
  - worker `K3S_URL` corrected to `https://192.168.1.80:6443` after subnet migration
  - validation image: `192.168.1.15:5000/lab/hello-world:latest`

### UniFi / UDM API Automation

- UDM host: `192.168.1.1` (`UDM_PRO_HOST`)
- Auth mode: `X-API-Key` header with `.env` key `UDM_PRO_API_KEY`
- API base in use: `https://192.168.1.1/proxy/network/integration/v1`
- Discovered/used endpoints:
  - `GET /sites`
  - `GET /sites/{siteId}/devices`
  - `GET /sites/{siteId}/clients`
  - `GET /sites/{siteId}/networks`
- Scripts:
  - `automation/unifi/scripts/fetch-unifi-inventory.ps1`
  - `automation/unifi/scripts/sync-unifi-to-netbox.ps1`
- Current UniFi sync state (2026-04-13):
  - inventory fetched from UniFi: `1` site, `1` UniFi device, `46` clients, `1` network
  - NetBox updates: `Dream Machine Pro Max` device tagged `unifi,unifi-device`, primary IP set to `192.168.1.1/32`
  - `39` private-lan UniFi client IPs tagged `unifi-client` (conservative IP-level sync)

### OpenBao (Secrets backend)

- Primary OpenBao endpoint: `http://192.168.1.25:8200` (`lab-secrets01`, persistent file storage)
- Primary KV mount: `secret/` (KV v2)
- Bootstrap environment snapshot: `secret/homelab/bootstrap/env`
- AI workstation sudo password field: `AI_WORKSTATION_PASSWORD`
- Safe lookup commands on `ai-workstation-evox2`:
  - Preferred helper: `openbao-env-get AI_WORKSTATION_PASSWORD`
  - Direct OpenBao CLI form: `bao kv get -mount=secret -field=AI_WORKSTATION_PASSWORD homelab/bootstrap/env`
- Hermes OpenBao access:
  - User services: `hermes-gateway.service`, `hermes-dashboard.service`
  - OpenBao token policy: `hermes-bootstrap-env-read`
  - Env/drop-in source: `/home/helios/.config/systemd/user/*hermes*.service.d/20-openbao.conf`
  - Sudo env wrapper: `/home/helios/.local/bin/hermes-openbao-sudo-env`
  - Sudo password injection drop-ins: `/home/helios/.config/systemd/user/hermes-*.service.d/30-sudo-password-openbao.conf`
  - Required exported runtime variable for Hermes terminal sudo: `SUDO_PASSWORD`
- Legacy bootstrap endpoint still present in cluster:
  - Namespace: `openbao`
  - Deployed via manifest (`k8s/manifests/openbao/openbao-dev.yaml`)
  - Service: NodePort `32000`
  - URL/API: `http://192.168.1.80:32000`
  - Mode: `dev` (no longer used by ESO)

### External Secrets Operator (ESO)

- Namespace: `external-secrets`
- Helm chart: `external-secrets/external-secrets` version `0.10.7`
- Reason for version pin: compatible with current k3s/k8s level and avoids CRD validation issues seen with newer release.
- PushSecret processing disabled (`processPushSecret=false`) to match CRD selection.

### OpenBao + ESO integration

- `ClusterSecretStore`: `openbao-store`
- Demo `ExternalSecret`: `default/openbao-sample-secret`
- Synced secret output: `default/demo-from-openbao`
- Wiki.js `ExternalSecret`: `wikijs/wikijs-db-secret` (syncs `db-password`)
- Vault endpoint in store:
  - `http://192.168.1.25:8200`
- Vault token source in store:
  - `external-secrets/openbao-eso-token`
- Manifest path: `k8s/manifests/external-secrets/openbao/store-and-sample.yaml`

### Wiki.js

- Namespace: `wikijs`
- Helm chart: `requarks/wiki` (`3.0.0`)
- Service exposure: `ClusterIP` only (`wikijs` service)
- URL: `https://wikijs.192.168.1.80.sslip.io`
- Database backend: external PostgreSQL on `lab-pgsql01` (`192.168.1.216:5432`, DB `wikijs`)
- DB password source: ESO-managed secret `wikijs/wikijs-db-secret` from OpenBao key `lab/runtime/wikijs`
- Ingress/TLS:
  - Ingress class: `traefik`
  - TLS issuer: `cert-manager` `ClusterIssuer/lab-selfsigned`
  - TLS secret: `wikijs/wikijs-tls`
- Wiki bootstrap documentation pages created via API:
  - `/en/services/directory`
  - `/en/services/wikijs`
  - `/en/services/openbao`
  - `/en/services/netbox`
  - `/en/services/n8n`
  - `/en/services/container-registry`
  - `/en/services/observability`
  - `/en/services/argocd`

### Argo CD (GitOps)

- Namespace: `argocd`
- Helm chart: `argo/argo-cd` (`9.4.18`)
- Service: NodePort `32090` (HTTP)
- URL: `http://192.168.1.80:32090`
- Local admin credentials are stored in `.env` as `ARGOCD_ADMIN_USER` and `ARGOCD_ADMIN_PASSWORD`.

### cert-manager

- Namespace: `cert-manager`
- Helm chart: `jetstack/cert-manager` (`v1.19.4`)
- CRDs installed via chart values
- Current state: deployed and ready.
- Configured issuer: `ClusterIssuer/lab-selfsigned` (used for Wiki.js ingress TLS).

### Prometheus

- Namespace: `observability`
- Helm chart: `prometheus-community/prometheus` (`29.2.0`)
- Service: NodePort `32091`
- URL: `http://192.168.1.80:32091`

### Grafana

- Namespace: `observability`
- Helm chart: `grafana/grafana` (`10.5.15`)
- Service: NodePort `32030`
- URL: `http://192.168.1.80:32030`
- Grafana credentials are stored in `.env` (`GRAFANA_ADMIN_PASSWORD`, user `admin`).

### Loki

- Namespace: `observability`
- Helm chart: `grafana/loki-stack` (`2.10.3`)
- Service: `loki.observability.svc.cluster.local:3100` (ClusterIP)
- `promtail` DaemonSet is enabled for log shipping.

### OpenCost

- Namespace: `opencost`
- Helm chart: `opencost/opencost` (`2.5.12`)
- Service: NodePort `32093` (UI)
- URL: `http://192.168.1.80:32093`
- OpenCost is configured to use internal Prometheus at `prometheus-server.observability.svc.cluster.local`.

### Falco

- Namespace: `falco`
- Helm chart: `falcosecurity/falco` (`8.0.2`)
- Runtime status: DaemonSet healthy on schedulable node(s)
- Driver mode: legacy `ebpf` (modern eBPF failed on current RPi kernel build).

### Velero + MinIO

- Namespace: `velero`
- Velero chart: `vmware-tanzu/velero` (`12.0.0`)
- MinIO chart: `minio/minio` (`5.4.0`) as in-cluster S3-compatible target
- Backup storage location: `default` is `Available`
- Target endpoint: `velero-minio.velero.svc.cluster.local:9000`
- Node-agent daemonset enabled for filesystem backup flow.

## Credential Handling

Secret resolution model is **OpenBAO-first with `.env` fallback**.

1. `.env` remains the local bootstrap source and is kept gitignored.
2. `automation/secrets/scripts/sync-env-to-openbao.ps1` syncs current `.env` values to OpenBAO.
3. Automation scripts must use `automation/common/SecretResolver.psm1` and `Resolve-LabSecret`.
4. Preferred reads are service-specific OpenBAO paths; fallback reads use `.env` only when necessary.

### AI Workstation Sudo Credential

- Secret path: `secret/homelab/bootstrap/env`
- KV mount: `secret`
- Field/key: `AI_WORKSTATION_PASSWORD`
- Purpose: sudo password for the `helios` user on `ai-workstation-evox2`.
- Do not copy the password into `ai-baseline-context.md`, Jira, Slack, command logs, or committed files.
- To test resolution without printing the secret: `openbao-env-get AI_WORKSTATION_PASSWORD >/dev/null && echo OK`
- Hermes integration: Hermes terminal sudo support reads `SUDO_PASSWORD` from its process environment. Do not put the password in `~/.hermes/config.yaml`; use the systemd wrapper/drop-ins that resolve the value from OpenBao at service start.
- Troubleshooting if Hermes cannot sudo:
  - Check OpenBao reachability from the workstation: `curl -sS http://192.168.1.25:8200/v1/sys/health`
  - Check helper resolution: `openbao-env-get AI_WORKSTATION_PASSWORD >/dev/null && echo OK`
  - Check Hermes service drop-ins: `systemctl --user cat hermes-gateway.service hermes-dashboard.service`
  - Check wrapper path: `/home/helios/.local/bin/hermes-openbao-sudo-env`
  - Restart services after secret or drop-in changes: `systemctl --user daemon-reload && systemctl --user restart hermes-gateway.service hermes-dashboard.service`

Current key groups include:

- `SWITCH_CISCO_2960_*`
- `K3S_MASTER_*`
- `RANCHERWEB01_*`
- `VM_HOST_IP`
- `LAB-PGSQL01_*`
- `LAB_PGSQL01_DB_*`
- `LAB_SECRETS01_*`
- `LAB_SECRETS01_OPENBAO_*`
- `LAB_WIKIJS_DB_*`
- `N8N_*`
- `NETBOX_*`
- `SPT02_*`
- `UDM_PRO_*`
- `OPENBAO_ROOT_TOKEN`
- `ARGOCD_ADMIN_*`
- `GRAFANA_ADMIN_PASSWORD`
- `VELERO_MINIO_*`

`.env` is excluded by `.gitignore`.

## Agent Bootstrap (Mandatory)

Before any operational task, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation\agent\scripts\bootstrap-lab-context.ps1
```

Bootstrap behavior:

1. Syncs `.env` bootstrap and curated service keys into OpenBAO.
2. Verifies required runtime secrets can be resolved through `Resolve-LabSecret`.
3. Fails fast if OpenBAO connectivity/policy is broken.

## Operational Notes for Future AI Agents

1. Run `automation/agent/scripts/bootstrap-lab-context.ps1` first.
2. Load inventory context from `network_devices.csv` first.
3. Resolve credentials with `Resolve-LabSecret`; do not implement new direct `.env` reads in automation scripts.
4. Validate management reachability before attempting remote ops.
5. For k3s changes, verify Rancher webhook health first (`cattle-system/rancher-webhook`).
6. Keep service definitions in `k8s/` aligned with runtime state after every change.
7. For n8n workflow changes, export updated JSON to `automation/n8n/workflows/exports/` and keep reusable templates in `automation/n8n/workflows/templates/`.
8. For inventory updates, run both NetBox sync scripts: first `sync-network-devices-to-netbox.ps1` (IPs/prefixes), then `sync-netbox-assets-from-csv.ps1` (devices/VMs + primary IP links).
9. For UniFi context refresh, run `automation/unifi/scripts/fetch-unifi-inventory.ps1` and then `automation/unifi/scripts/sync-unifi-to-netbox.ps1 -FetchFresh`.
10. For Strix Halo workstation inference backend operations, use `kyuz0/amd-strix-halo-toolboxes` and keep it synced with `automation/ai-workstation/scripts/sync-strix-halo-backend.ps1`.
11. `Hermes-Test` should be treated as disposable validation only; durable planning and execution state belongs in this `lab` repo.
12. For OpenClaw operations on the workstation, use `automation/ai-workstation/README.md` for install/status/security/runtime reference.
13. For SPT/Fika control requests, use the `SPT/Fika Server` section above and prefer `ssh helios@192.168.1.86 "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status|Start|Stop|Restart"` from `ai-workstation-evox2`; do not use the interactive desktop menu from Hermes/Discord.

## Next Actions

- Use `phase1-agent-todo.md` as the active first-phase execution queue.
- Keep `network_devices.csv`, NetBox, and this baseline in sync after every environment change.
- Reboot `ai-workstation-evox2` to activate newest installed Fedora kernel.
- Execute `P1-013` to expand Prometheus + Grafana coverage for k3s nodes and core services.

## OpenBrain Memory Service (Deployed 2026-05-01)

- Namespace: `openbrain`
- URL: `https://openbrain.192.168.1.80.sslip.io`
- Components:
  - External PostgreSQL + pgvector on `lab-pgsql01` (`192.168.1.216:5432`, DB `openbrain`)
  - `openbrain-mcp` (MCP server)
- Secrets source: OpenBao `secret/lab/runtime/openbrain`
  - fields: `postgres_password`, `mcp_access_key`, `embedding_api_base`, `embedding_api_key`, `embedding_model`, `chat_api_base`, `chat_api_key`, `chat_model`
- Model provider: Ollama on AI workstation (`AI_WORKSTATION_IP`)
  - embeddings: `nomic-embed-text` (vector dim 768)
  - chat metadata: `qwen3-coder:latest`
- Deployment automation:
  - `automation/openbrain/scripts/bootstrap-openbrain-secrets.ps1`
  - `automation/openbrain/scripts/deploy-openbrain.ps1`
  - `automation/openbrain/scripts/test-openbrain.ps1`
  - manifests: `k8s/manifests/openbrain/*`
  - image source: `k8s/openbrain/server/*`

Operational notes:
- OpenBrain compute runs in k3s (`openbrain-mcp`) while persistence is external on `lab-pgsql01`.
- Current image publishing uses `ttl.sh` (24h TTL). Move to the internal registry once k3s nodes are configured for insecure registry pull or TLS-enabled registry endpoints.
