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
- OpenBAO cluster access path: `secret/homelab/k3s/bs01-field`
  - Fields: `api_endpoint`, `primary_server`, `nodes`, `kubeconfig`
  - Treat `kubeconfig` as sensitive.

Verification from `bs01-wknd01`:

```bash
sudo k3s kubectl get nodes -o wide
sudo k3s kubectl get pods -A
```

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
