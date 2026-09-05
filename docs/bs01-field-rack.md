# BS01 Field Rack

## Purpose

The BS01 field rack is the portable Iron Meridian Systems base-station environment for DroneOps field testing. It is intended to run without dependency on an HQ service when disconnected, while still being able to synchronize and report upstream when connectivity exists.

## Nodes

| Host | IP | Hardware | Role |
| --- | --- | --- | --- |
| `bs01-gw` | `192.168.1.108` | Dell OptiPlex 3060 Micro | Field gateway for hardware adapters and DroneOps gateway daemon |
| `bs01-data` | `192.168.1.109` | Dell OptiPlex 3046 Micro | Field data server for PostgreSQL/PostGIS and video/object-storage staging paths |
| `bs01-wknd01` | `192.168.1.110` | Dell OptiPlex 7040 Micro | k3s server/control-plane, embedded etcd, schedulable worker |
| `bs01-wknd02` | `192.168.1.111` | Dell OptiPlex 7040 Micro | k3s server/control-plane, embedded etcd, schedulable worker |
| `bs01-wknd03` | `192.168.1.112` | Dell OptiPlex 7040 Micro | k3s server/control-plane, embedded etcd, schedulable worker |

All five nodes use static addresses on `192.168.1.0/24` with gateway/DNS `192.168.1.1`.

## Secrets

SSH credentials are stored in OpenBAO KV v2. Do not put credentials in docs, Git, Wiki.js, or Kanban cards.

| Host | OpenBAO path |
| --- | --- |
| `bs01-gw` | `secret/homelab/vms/bs01-gw` |
| `bs01-data` | `secret/homelab/vms/bs01-data` |
| `bs01-wknd01` | `secret/homelab/vms/bs01-wknd01` |
| `bs01-wknd02` | `secret/homelab/vms/bs01-wknd02` |
| `bs01-wknd03` | `secret/homelab/vms/bs01-wknd03` |

The legacy path `secret/homelab/vms/bst01-gw` is retained as a compatibility alias for older references.

## k3s Cluster

The field k3s cluster is a three-server HA k3s install using embedded etcd. All three 7040 nodes run the k3s server service and remain schedulable.

- API endpoint: `https://192.168.1.110:6443`
- Current verified version: `v1.36.3+k3s1`
- Baseline components: CoreDNS, metrics-server, local-path-provisioner, Traefik
- Longhorn storage: deployed by ArgoCD from `k8s/field/bs01/argocd/longhorn-application.yaml`
- ArgoCD Image Updater: deploy with
  `k8s/field/bs01/argocd-image-updater` so DroneOps BS01 service images can
  move from mutable `sha-latest` pulls to immutable `sha-<commit>` tags through
  GitOps. The BS01 overlay reuses the shared lab manifest and removes the main
  lab node selector.
- Longhorn runbook: `docs/bs01-longhorn-runbook.md`
- Rack-local cert-manager and PKI runbook: `docs/bs01-pki-runbook.md`
- OpenBAO cluster access path: `secret/homelab/k3s/bs01-field`
  - Fields: `api_endpoint`, `primary_server`, `nodes`, `kubeconfig`
  - Treat `kubeconfig` as sensitive.

Verification from `bs01-wknd01`:

```bash
sudo k3s kubectl get nodes -o wide
sudo k3s kubectl get pods -A
```

## Gateway GPS

`bs01-gw` has an optional Microsoft Streets & Trips-era Pharos USB GPS for
locating the field base station. The verified receiver enumerates as USB
`067b:aaa0`, binds to the Linux `pl2303` driver, and emits NMEA at 4800 baud.
The gateway repository owns its repeatable udev and `gpsd` configuration under
`deploy/gpsd/`.

The udev rule provides the stable path `/dev/droneops-base-gps`. `gpsd` listens
only on loopback (`127.0.0.1:2947` and the local Unix socket); it must not be
exposed directly to the browser or LAN.

On 2026-08-28, `gpsd` identified the receiver as SiRF PharNav `07S203`, but the
indoor puck reported `mode=1` with zero visible or used satellites. This proves
the host and serial path, not a valid position. Place the puck outdoors or at a
window with a broad sky view and require `mode>=2` plus finite latitude and
longitude before accepting a fix. Do not accept NMEA `V` status, placeholder
coordinates, or the receiver's stale pre-fix clock.

Future application integration should update the platform-owned BS01 node
location. It must not represent base-station GPS as Tello/vehicle telemetry or
write PostgreSQL directly from the gateway.

## Longhorn Storage

Each k3s node has a dedicated 256 GB NVMe drive mounted at `/var/lib/longhorn` for Longhorn replicated cluster storage. The OS disk remains `/dev/sda` on each worker and must not be touched during storage operations.

| Host | Longhorn disk | Serial | Filesystem UUID |
| --- | --- | --- | --- |
| `bs01-wknd01` | `/dev/nvme0n1p1` | `MQ44B37803249` | `e1c9f1f9-1e84-467d-a534-1976947f256f` |
| `bs01-wknd02` | `/dev/nvme0n1p1` | `MQ44B37801758` | `97538229-24f7-4dec-9893-82d15ca86e23` |
| `bs01-wknd03` | `/dev/nvme0n1p1` | `MR12W53800132` | `b3bedbab-e2a0-4bfc-87c4-7b864980f997` |

Longhorn is the default storage class for k3s workloads that need persistent volumes. `local-path` remains installed but is not the default. PostgreSQL/PostGIS stays on `bs01-data`; Longhorn is not the primary data plane and should not be used for large DroneOps video payload storage.

## Rack-Local PKI

The BS01 GitOps source includes a three-replica cert-manager deployment and a
versioned DroneOps ingress root/intermediate hierarchy. The issuer private keys
are generated inside the cluster and retained only in Kubernetes Secrets
replicated by embedded etcd. They are not OpenBAO runtime dependencies and must
never enter Git, documentation, command output, or browser artifacts.

The cert-manager deployment is pinned to `v1.21.1`, the supported release used
for Kubernetes 1.36 compatibility and explicit disabled automatic renewal on
the versioned root Certificate.

The root is manually rotated; the intermediate and later 90-day console leaf
have bounded renewal windows. The three server-local etcd snapshot sets are the
current issuer backup coverage. This is rack-local recovery only: the
unavailable Longhorn BackupTarget does not protect Kubernetes Secrets and does
not establish off-rack disaster recovery. See `docs/bs01-pki-runbook.md`.

## MOTD

Each node uses the shared Iron Meridian Systems MOTD installed at:

```text
/etc/update-motd.d/00-iron-meridian
/etc/iron-meridian-role
```

The MOTD includes the IMS ASCII banner, role name, role description, system details, service state, and unauthorized-access warning.

Ubuntu's optional `motd-news.timer` is disabled on the field-rack hosts so the
console MOTD stays local, deterministic, and free of external news-fetch
failures. The OptiPlex nodes do not have IPMI/BMC hardware, so
`openipmi.service` is disabled to avoid false failed-unit noise.

## Inventory

`network_devices.csv` is the source-of-truth inventory file in this repo. NetBox should model the five hosts as physical Dell OptiPlex Micro devices at site `BS01 Field Rack`.
