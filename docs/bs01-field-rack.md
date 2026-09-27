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

### Encrypted runtime Secrets and local recovery (2026-09-27)

All three K3s servers reported Secret encryption `Enabled`, rotation stage
`reencrypt_finished`, and matching server encryption hashes after the
documented HA enable and key-rotation sequence. K3s was restarted one server
at a time; no host was rebooted. The BS01 DroneOps runtime now consumes two
native Secrets for its database URL, NATS token, and recording-context
projection token. The two runtime ExternalSecrets and their ESO-owned targets
were removed after a guarded value-equivalent transfer. The registry pull
ExternalSecret remains under DroneOps #1087 for artifact delivery.

Independent `bs01-data` holds protected root-owned generations under
`/srv/droneops/k3s-recovery/`: `2026-09-27-pre-encryption/`,
`2026-09-27-encrypted/`, `2026-09-27-native-staged/`, and
`2026-09-27-native-cutover/`. Directories are `0700`, artifacts `0600`.
The final generation includes fresh encrypted etcd snapshots and matching
server tokens/configuration from all three nodes, plus the exact K3s binary;
source/destination SHA-256 checks passed. A loopback-only isolated restore
from that generation started a ready API and returned metadata for nine
namespaces, seven DroneOps deployments, and four Secret names including both
native targets, without displaying values. The sandbox and transfer staging
were removed. This is recovery on another rack host, not off-rack disaster
recovery. DroneOps #670 owns a physical disconnected cold boot. The detailed
operational record is in the platform repository's
`docs/runbooks/bs01-local-secret-commissioning.md`.

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

## Data Host Root Capacity

This section has a [BS01 storage runbook mirror](https://wikijs.192.168.1.80.sslip.io/en/runbooks/bs01-longhorn-storage). The 2026-09-26 update below is verified in source control; Wiki mirror synchronization was not performed.

On 2026-09-16, the owner-approved 20 GiB expansion grew bs01-data's ext4
root LV `/dev/ubuntu-vg/ubuntu-lv` from 13918 to 19038 4 MiB extents
(54.37 to 74.37 GiB; 79851159552 bytes). Existing free extents in
`ubuntu-vg` supplied the space; no partition or physical disk changed.
Online resize2fs completed. Readback showed 74% used and approximately
18.5 GiB available, a point-in-time measurement rather than a capacity SLA.
PostgreSQL recovered from full-disk connection rejection without restart,
authenticated DroneOps APIs returned 200, and the waiting Argo migration
and fleet rollout completed successfully.

The pre-expansion LVM metadata backup is retained root:root mode 0600 at
`/var/backups/issue-856-ubuntu-vg-before-expansion-20260916.conf`, verified
identical to the original `/run` copy. It is not a database backup and must
not be applied blindly to shrink the grown filesystem. No data was deleted.
Telemetry retention and database-aware readiness need separate scoped work;
this recovery did not change either. The incident belongs to
[DroneOps #856](https://github.com/ajh-lab/droneops-platform/issues/856).

On 2026-09-26, the owner authorized a second bounded capacity recovery.
Before mutation, the 74.37 GiB root LV's 72.9 GiB ext4 filesystem had
848,072,704 bytes (about 809 MiB) available, and PostgreSQL was active.
The only PV was `/dev/sda3` in `ubuntu-vg`; its 8,798 free 4 MiB extents
supplied an online expansion of the same root LV to 108.73 GiB. Online
`resize2fs` grew the filesystem to 106.7 GiB, with 35,685,191,680 bytes
(33.2 GiB) available immediately afterward. No partition, second LV,
physical disk, or reboot was changed. A root-only mode 0600 LVM metadata
backup was created at
`/var/backups/issue-669-ubuntu-vg-before-capacity-expansion-20260926.conf`.
As with the prior backup, this is not a database backup or a shrink plan.

The dominant consumer was `droneops.public.telemetry` at about 61 GB, with
46 GB of table data and 15 GB of indexes. A full read-only classification
counted 35,373,014 rows: 35,373,006 carried the exact simulator envelope
and explicit simulated payload markers, and eight did not. Platform
[PR #1102](https://github.com/ajh-lab/droneops-platform/pull/1102) disabled
automatic field simulation through GitOps. After the observed simulator
write rate reached zero, a guarded transaction copied the eight other rows
into a staging table, checked their count, truncated only the telemetry
table without cascade while retaining the sequence, restored the eight
original rows, and checked their full-row content before commit. A second
post-commit comparison found zero missing or extra rows; the staging copy
was then removed. No real, unknown, or unclassified row was deleted.

Post-change telemetry occupied 172,032 bytes, and the ext4 root had
100,687,859,712 bytes (93.8 GiB) available at 8% use. PostgreSQL remained
in production and ready, Flyway V064 successful, and DroneOps Argo
`Synced`/`Healthy` with all seven deployments Ready. The simulator auto-tick
remained off. Durable opt-in, retention, partitioning, idempotency, and
capacity alerts are tracked by
[DroneOps #1101](https://github.com/ajh-lab/droneops-platform/issues/1101),
separate from native Secret issue #669. These are point-in-time observations,
not a storage or backup retention guarantee.

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
