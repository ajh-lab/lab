# Home Lab AI Baseline Context

Last updated: 2026-04-27 17:13 (America/Chicago)

## Purpose

This repository is the baseline operational context for the home lab. It is intended to be AI-ingestable and kept current as infrastructure changes.

## Source of Truth Files

- `network_devices.csv`: canonical network inventory and device metadata.
- `.env`: credentials and secrets (never commit to git).
- `k8s/helm/*` and `k8s/manifests/*`: deployment definitions for lab services.
- `automation/n8n/*`: n8n workflow exports/templates and API helper scripts.
- `automation/netbox/*`: NetBox IPAM + asset sync scripts.
- `automation/unifi/*`: UniFi (UDM Pro) inventory fetch + NetBox sync scripts.
- `automation/ai-workstation/*`: AI workstation automation and Strix Halo backend sync scripts.

## Repo Layout

```text
lab/
  ai-baseline-context.md
  network_devices.csv
  .env                      # gitignored (secrets)
  .gitignore
  .kubeconfig-192.168.1.80.yaml
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
    ai-workstation/
      README.md
      scripts/
        sync-strix-halo-backend.ps1
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

Workers (all currently `NotReady`):

- `oma01rpicls01wknd01` (`192.168.1.81`)
- `oma01rpicls01wknd02` (`192.168.1.82`)
- `oma01rpicls01wknd03` (`192.168.1.83`)
- `oma01rpicls01wknd04` (`192.168.1.84`)

Worker recovery note:

- Worker inventory addressing was corrected to `192.168.1.81-84` on 2026-04-13.
- Cluster readiness still needs validation after the address correction.

### Rancher

- Rancher VM host: `rancherweb01` (`192.168.1.79`)
- Rancher webhook issue fixed on 2026-04-12:
  - `rancher-webhook` pod now healthy on master
  - service endpoints are populated
  - namespace creation admission works again
- Deployment pinned to master node selector to avoid scheduling back onto unreachable worker nodes.

### AI Workstation

- Host: `ai-workstation-evox2` (`192.168.1.123`, Fedora 43, AMD Strix Halo / Radeon 8060S)
- SSH: key-based access validated from Windows; management user references in `.env` as `AI_WORKSTATION_*`
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
- Runtime/services (2026-04-27):
  - `ollama` systemd service active (`0.21.2`)
  - `qdrant` active via Docker (`http://192.168.1.123:6333`)
  - `open-webui` active via Docker (`http://192.168.1.123:3000`)
  - local tool-calling agent active (`http://192.168.1.123:8777/health`)
  - cockpit socket active (`https://192.168.1.123:9090`)
- Installed Ollama models:
  - `qwen2.5:1.5b`
  - `llama3.2:1b`
  - `tinyllama:latest`
- `llama.cpp` built and installed from source with Vulkan support (`/usr/local/bin/llama-cli`)

### Strix Halo Backend (Required)

- Backend repo: `https://github.com/kyuz0/amd-strix-halo-toolboxes`
- Remote checkout path: `/mnt/ai/llama/amd-strix-halo-toolboxes`
- Provisioned toolbox container: `llama-rocm-7.2.2`
- GPU visibility validation command:
  - `toolbox run -c llama-rocm-7.2.2 llama-cli --list-devices`
- Repo sync script:
  - `automation/ai-workstation/scripts/sync-strix-halo-backend.ps1`

## Platform Services (Live)

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
  - `1` VM in `virtualization/virtual-machines` (`rancherweb01`) with `primary_ip4` linkage.
  - Current VM cluster for lab guests: `homelab-vms`.

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

- Namespace: `openbao`
- Deployed via manifest (`k8s/manifests/openbao/openbao-dev.yaml`)
- Service: NodePort `32000`
- URL/API: `http://192.168.1.80:32000`
- Mode: `dev` (lab bootstrap only, not production-safe)

### External Secrets Operator (ESO)

- Namespace: `external-secrets`
- Helm chart: `external-secrets/external-secrets` version `0.10.7`
- Reason for version pin: compatible with current k3s/k8s level and avoids CRD validation issues seen with newer release.
- PushSecret processing disabled (`processPushSecret=false`) to match CRD selection.

### OpenBao + ESO integration

- `ClusterSecretStore`: `openbao-store`
- Demo `ExternalSecret`: `default/openbao-sample-secret`
- Synced secret output: `default/demo-from-openbao`
- Vault endpoint in store: `http://openbao.openbao.svc.cluster.local:8200`
- Manifest path: `k8s/manifests/external-secrets/openbao/store-and-sample.yaml`

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
- Current state: deployed and ready; no issuer configured yet.

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

Credentials are stored in `.env` and referenced by key name only.

Current key groups include:

- `SWITCH_CISCO_2960_*`
- `K3S_MASTER_*`
- `RANCHERWEB01_*`
- `VM_HOST_IP`
- `N8N_*`
- `NETBOX_*`
- `UDM_PRO_*`
- `OPENBAO_ROOT_TOKEN`
- `ARGOCD_ADMIN_*`
- `GRAFANA_ADMIN_PASSWORD`
- `VELERO_MINIO_*`

`.env` is excluded by `.gitignore`.

## Operational Notes for Future AI Agents

1. Load inventory context from `network_devices.csv` first.
2. Resolve device credentials via `.env` key references from `CredentialRef`.
3. Validate management reachability before attempting remote ops.
4. For k3s changes, verify Rancher webhook health first (`cattle-system/rancher-webhook`).
5. Keep service definitions in `k8s/` aligned with runtime state after every change.
6. For n8n workflow changes, export updated JSON to `automation/n8n/workflows/exports/` and keep reusable templates in `automation/n8n/workflows/templates/`.
7. For inventory updates, run both NetBox sync scripts: first `sync-network-devices-to-netbox.ps1` (IPs/prefixes), then `sync-netbox-assets-from-csv.ps1` (devices/VMs + primary IP links).
8. For UniFi context refresh, run `automation/unifi/scripts/fetch-unifi-inventory.ps1` and then `automation/unifi/scripts/sync-unifi-to-netbox.ps1 -FetchFresh`.
9. For Strix Halo workstation inference backend operations, use `kyuz0/amd-strix-halo-toolboxes` and keep it synced with `automation/ai-workstation/scripts/sync-strix-halo-backend.ps1`.

## Next Actions

- Recover the 4 worker Pis (`192.168.1.81-84`) and restore `Ready` state.
- After worker recovery, run OS/k3s patch upgrades on each worker to align with control-plane (`v1.28.15+k3s1`).
- Create a cert-manager `ClusterIssuer` and migrate exposed NodePort apps to HTTPS ingress where practical.
- Replace OpenBao dev mode with persistent/non-dev configuration when ready.
- Complete n8n email summary flow by attaching IMAP credentials, replacing manual trigger with a schedule trigger, and adding a delivery node (email/Slack/Teams).
