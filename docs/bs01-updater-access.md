# BS01 appliance updater access

## Account and trust

Platform #1087's operator-invoked updater runs on `bs01-data` as the locked
system account `droneops-updater`. There is no update timer or inbound update
API. Source and configuration are root-owned. The account owns its bounded
bundle store and scratch space. Install the `droneops-update` wrapper from
`automation/droneops/releases/` at `/usr/local/bin/droneops-update`, root:root
0755. It fixes the source/config paths and selects Helm's ConfigMap storage
driver. Every manual baseline, upgrade, history and rollback command must
also use `HELM_DRIVER=configmap`.

The dedicated Kubernetes client certificate has subject
`CN=droneops-bs01-updater`, with no administrator group. Its RBAC is
`k8s/field/bs01/updater/access.yaml`. It can read node readiness and manage
the current platform chart kinds in `droneops`, the existing namespace's
metadata, and the one existing Longhorn attachment snapshot schedule.
It cannot read/write native Secrets, remove PVCs/namespaces, manage RBAC,
execute into pods or change unrelated applications. This is still a trusted
deployment principal: workload-spec authority can indirectly expose mounted
secrets. Protect its credentials and permit only independently signed,
reviewed release content. RBAC is not a sandbox for hostile signed charts.

Existing certificate, middleware and Longhorn schedule permissions allow
updates to named resources only. A later release that needs a new kind or
resource outside these bounds must receive a reviewed access change; do not
widen this role automatically after a failed update.

Protected operator credential custody is
`secret/homelab/droneops/releases/devices/bs01-operator` in OpenBao. Store only
this device's SSH private/public key and Kubernetes client credential there.
Release signer private keys never go to BS01. Device catalog credentials and
public verification trust use the separate path in the
[catalog runbook](droneops-release-catalog.md).

On BS01, root owns `/etc/droneops/updater`, with updater group read/traverse
access only. Give this user a traverse-only POSIX ACL on the existing private
`/etc/droneops` parent; preserve all existing secret-file modes and ownership.
Private credentials are 0640 root:droneops-updater. Public trust files use the
same protected directory. Do not change the existing native secret values.

## SSH and fixed sudo privileges

Use a unique Ed25519 key, pinned host keys independently read from the current
trusted administrative SSH connections, and a root-owned known-hosts file.
Create the locked `droneops-updater` SSH account on the three K3s nodes. Its
authorized key must include `restrict,from="192.168.1.109"`; no forwarding,
PTY or password login is needed. Node sudo rules allow only these commands:

- `k3s ctr -n k8s.io images list`
- `k3s ctr -n k8s.io images check --quiet`
- `k3s ctr -n k8s.io images import --digests --base-name REPOSITORY -`,
  with the repository constrained by an anchored sudo argument regex.

On the data node, grant only the exact fixed
`/usr/local/libexec/droneops/flyway-version-readonly` helper already reviewed
in the platform repository. It runs a fixed read-only PostgreSQL transaction;
never grant arbitrary psql, runuser, shell or generic K3s sudo. Root owns the
helper and every parent directory, and validates each sudoers file with
`visudo -cf` before installation.

## Verification and recovery

Before provisioning, the new Kubernetes identity could neither read nodes
nor create a ConfigMap in `droneops` (observed RED, 2026-10-09 UTC).
After applying the reviewed access manifest, require affirmative checks for
node inventory and release ConfigMap operations, and negative checks for
Secret reads, cluster role writes, PVC deletion, pod exec and unrelated
namespace writes. Repeat using the actual issued credential on BS01.
Test the SSH inventory and fixed Flyway read and prove an unrelated sudo
command fails. These checks do not activate Helm or prove rollback.

Keep the existing administrative recovery path available. Revoke this
principal by removing only its role bindings and SSH authorized key. Its
Kubernetes certificate cannot be individually revoked; removing bindings
removes API authorization. Rotate before expiry through a new reviewed CSR,
replace the protected kubeconfig atomically and test it. Never delete native
Secrets or persistent volumes as an updater recovery step.

Provisioning, credential tests and Helm activation remain separate measured
evidence; source configuration alone does not prove live access or an install.
