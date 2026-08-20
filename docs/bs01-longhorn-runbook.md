# BS01 Longhorn Runbook

## Purpose

Longhorn provides replicated Kubernetes persistent volumes for the BS01 field k3s cluster. It is intended for k3s-hosted services that need durable cluster storage, such as observability, ArgoCD state, NATS/JetStream, or internal service data.

Longhorn does not replace `bs01-data`. PostgreSQL/PostGIS remains on `bs01-data` at `192.168.1.109`, and large DroneOps video payloads should stay outside PostgreSQL and Longhorn unless a future design explicitly changes that boundary.

## GitOps Source

Longhorn is deployed to the BS01 cluster by ArgoCD from:

```text
k8s/field/bs01/argocd/longhorn-application.yaml
```

The current chart target is Longhorn `1.12.1` from:

```text
https://charts.longhorn.io
```

The Application disables the chart pre-upgrade checker job for ArgoCD-driven installs. Without this, ArgoCD can run the Longhorn pre-upgrade hook before the Longhorn service account exists.

## Nodes And Disks

Each k3s worker/control-plane node has a dedicated 256 GB NVMe drive mounted at `/var/lib/longhorn`.

| Node | Longhorn disk | Model | Serial | Filesystem UUID | Mount |
| --- | --- | --- | --- | --- | --- |
| `bs01-wknd01` | `/dev/nvme0n1p1` | SPCC M.2 PCIe SSD | `MQ44B37803249` | `e1c9f1f9-1e84-467d-a534-1976947f256f` | `/var/lib/longhorn` |
| `bs01-wknd02` | `/dev/nvme0n1p1` | SPCC M.2 PCIe SSD | `MQ44B37801758` | `97538229-24f7-4dec-9893-82d15ca86e23` | `/var/lib/longhorn` |
| `bs01-wknd03` | `/dev/nvme0n1p1` | SPCC M.2 PCIe SSD | `MR12W53800132` | `b3bedbab-e2a0-4bfc-87c4-7b864980f997` | `/var/lib/longhorn` |

The OS disk on each worker is `/dev/sda`; do not wipe or partition `/dev/sda`. Root is mounted from `/dev/mapper/ubuntu--vg-ubuntu--lv`, and `/boot` plus `/boot/efi` live on `/dev/sda` partitions.

## Host Prerequisites

The following packages and services are required on each worker:

```bash
sudo apt-get install -y open-iscsi nfs-common cryptsetup dmsetup jq util-linux parted e2fsprogs
sudo systemctl enable --now iscsid
sudo modprobe iscsi_tcp
```

The Longhorn disk is mounted by UUID in `/etc/fstab` with `noatime` at `/var/lib/longhorn`.

## Verification

Run these commands from `bs01-wknd01`:

```bash
sudo k3s kubectl -n argocd get application longhorn
sudo k3s kubectl -n longhorn-system get pods -o wide
sudo k3s kubectl -n longhorn-system get nodes.longhorn.io
sudo k3s kubectl get storageclass
```

Expected storage classes:

```text
longhorn (default)
longhorn-static
local-path
```

`local-path` should not be the default storage class after Longhorn is installed.

## Smoke Test

Use a temporary PVC to verify that Longhorn can bind, mount, write, and reattach across pod recreation:

```bash
sudo k3s kubectl create ns longhorn-smoke
cat <<'EOF' | sudo k3s kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-smoke-pvc
  namespace: longhorn-smoke
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: longhorn-smoke-writer
  namespace: longhorn-smoke
spec:
  restartPolicy: Never
  containers:
    - name: writer
      image: busybox:1.36
      command: ["sh", "-c", "set -e; date -u > /data/proof.txt; cat /data/proof.txt; sync"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: longhorn-smoke-pvc
EOF
sudo k3s kubectl -n longhorn-smoke wait --for=jsonpath='{.status.phase}'=Succeeded pod/longhorn-smoke-writer --timeout=240s
sudo k3s kubectl -n longhorn-smoke logs longhorn-smoke-writer
sudo k3s kubectl -n longhorn-smoke delete pod longhorn-smoke-writer --wait=true
```

Then create a reader pod against the same PVC:

```bash
cat <<'EOF' | sudo k3s kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: longhorn-smoke-reader
  namespace: longhorn-smoke
spec:
  restartPolicy: Never
  containers:
    - name: reader
      image: busybox:1.36
      command: ["sh", "-c", "set -e; test -s /data/proof.txt; cat /data/proof.txt"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: longhorn-smoke-pvc
EOF
sudo k3s kubectl -n longhorn-smoke wait --for=jsonpath='{.status.phase}'=Succeeded pod/longhorn-smoke-reader --timeout=240s
sudo k3s kubectl -n longhorn-smoke logs longhorn-smoke-reader
sudo k3s kubectl delete ns longhorn-smoke
```

## UI Access

The Longhorn UI service is internal-only:

```bash
sudo k3s kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80
```

Then open:

```text
http://127.0.0.1:8080
```

Do not expose the Longhorn UI publicly without authentication and network controls.

## Operational Notes

- Keep the default replica count at `3` while all three worker nodes are available.
- Check Longhorn node and disk health after any field-rack power event.
- Treat `/var/lib/longhorn` as Longhorn-owned. Do not manually write service data there.
- For cluster rebuilds, confirm `/dev/nvme0n1` is still the dedicated Longhorn disk before reusing it.
- PostgreSQL backups and DroneOps video retention are separate concerns and should not be solved by Longhorn alone.
