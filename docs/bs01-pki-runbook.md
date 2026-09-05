# BS01 Rack-Local PKI Runbook

## Purpose

This runbook installs and verifies the BS01-local cert-manager control plane and
the versioned DroneOps ingress CA hierarchy. It does not add the DroneOps leaf
certificate, change ingress routing, install workstation trust, remove the
HTTP console, or change session-cookie behavior.

## Prerequisites

- Use only `.kubeconfig-bs01-field.yaml`, whose API endpoint is
  `https://192.168.1.110:6443`. Never substitute the main lab kubeconfig.
- Confirm all three BS01 k3s servers are Ready and ArgoCD is healthy.
- Confirm `cert-manager` is not already installed and that no existing Issuer,
  ClusterIssuer, or Certificate name would collide.
- Confirm the lab GitOps PR containing both Applications and the PKI resources
  has merged to `main`.
- Preserve the current DroneOps HTTP ingress and
  `DRONEOPS_AUTH_ALLOW_INSECURE_HTTP=true` during this phase.

All commands below are non-secret checks. Never print Kubernetes Secret data,
private keys, kubeconfig contents, tokens, or environment dumps.

## GitOps Installation

Set the kubeconfig path without changing the current kubectl context:

```powershell
$bs01Kubeconfig = 'C:\Users\adamj\SourceControl\lab\.kubeconfig-bs01-field.yaml'
kubectl --kubeconfig $bs01Kubeconfig get nodes
```

Apply the cert-manager Application first and wait for its CRDs, webhook, and
three-replica controller sets to become healthy:

```powershell
kubectl --kubeconfig $bs01Kubeconfig apply -f k8s/field/bs01/argocd/cert-manager-application.yaml
kubectl --kubeconfig $bs01Kubeconfig -n argocd wait application/cert-manager --for=jsonpath='{.status.sync.status}'=Synced --timeout=300s
kubectl --kubeconfig $bs01Kubeconfig -n argocd wait application/cert-manager --for=jsonpath='{.status.health.status}'=Healthy --timeout=300s
kubectl --kubeconfig $bs01Kubeconfig -n cert-manager rollout status deployment/cert-manager --timeout=300s
kubectl --kubeconfig $bs01Kubeconfig -n cert-manager rollout status deployment/cert-manager-webhook --timeout=300s
kubectl --kubeconfig $bs01Kubeconfig -n cert-manager rollout status deployment/cert-manager-cainjector --timeout=300s
```

Only after those checks pass, apply the PKI Application:

```powershell
kubectl --kubeconfig $bs01Kubeconfig apply -f k8s/field/bs01/argocd/bs01-pki-application.yaml
kubectl --kubeconfig $bs01Kubeconfig -n argocd wait application/bs01-pki --for=jsonpath='{.status.sync.status}'=Synced --timeout=300s
kubectl --kubeconfig $bs01Kubeconfig -n argocd wait application/bs01-pki --for=jsonpath='{.status.health.status}'=Healthy --timeout=300s
```

Do not apply the PKI directory directly. ArgoCD owns reconciliation after the
two bootstrap Application objects are applied.

## Validation

Confirm controller placement, image pull policy, and Ready state. The three
replicas of each persistent component must span all three server nodes so the
required images are cached throughout the rack before offline acceptance:

```powershell
kubectl --kubeconfig $bs01Kubeconfig -n cert-manager get deploy,pods -o wide
kubectl --kubeconfig $bs01Kubeconfig -n cert-manager get pdb
kubectl --kubeconfig $bs01Kubeconfig get crd certificates.cert-manager.io issuers.cert-manager.io clusterissuers.cert-manager.io
```

Confirm the hierarchy is Ready without reading any Secret value:

```powershell
kubectl --kubeconfig $bs01Kubeconfig -n cert-manager get issuer,certificate
kubectl --kubeconfig $bs01Kubeconfig get clusterissuer bs01-ingress-ca-2026
$secretNames = @('bs01-root-ca-2026', 'bs01-ingress-ca-2026')
foreach ($secretName in $secretNames) {
  $secret = kubectl --kubeconfig $bs01Kubeconfig -n cert-manager get secret $secretName -o json | ConvertFrom-Json
  [pscustomobject]@{
    Name = $secret.metadata.name
    Type = $secret.type
    Keys = ($secret.data.PSObject.Properties.Name -join ',')
  }
}
```

Expected Secret keys are names only: `tls.crt`, `tls.key`, and where produced,
`ca.crt`. Do not decode or display `tls.key`. Validate certificate subjects,
issuers, SANs, validity, and fingerprints only through the public certificate
portions in the dedicated leaf-delivery phase.

Also re-check the embedded-etcd backup evidence. BS01 currently creates
snapshots twice daily and retains five on each server:

```powershell
kubectl --kubeconfig $bs01Kubeconfig get etcdsnapshotfiles.k3s.cattle.io -o custom-columns='NAME:.metadata.name,NODE:.spec.nodeName,LOCATION:.spec.location,SIZE:.status.size,CREATED:.metadata.creationTimestamp'
```

## Public Trust Artifact

The public root certificate is the only CA artifact intended for supported
Windows clients. Export it to an ignored task directory and verify its subject,
validity, and SHA-256 fingerprint before presenting it to the owner. Never
export the root or intermediate private keys.

Exporting the public root does not authorize importing it. Installing it into
`Cert:\LocalMachine\Root` or editing the Windows hosts file requires explicit
action-time owner approval and belongs to the later operator-trust phase.

## Rotation

The leaf certificate is renewed by the rack-local intermediate. The
intermediate renews six months before its three-year expiry and rotates its
private key. Monitor root, intermediate, and leaf expiration independently;
cert-manager does not prevent a leaf from outliving its issuer and changing a
CA Secret does not force existing leaves to reissue.

The root's automatic renewal is disabled. Root rotation uses a new versioned
root and an overlap period in which supported clients trust both public roots.
Do not replace active issuer material or trigger root rotation without explicit
action-time owner approval.

## Recovery

The live CA Secrets are replicated by three-member embedded etcd. The k3s
servers write snapshots twice daily and retain five local snapshots per node.
That provides rack-local restart, single-node-loss, and snapshot evidence; it
does not provide off-rack disaster recovery.

The Longhorn BackupTarget is currently unavailable, and Longhorn does not back
up Kubernetes Secrets. Do not claim it protects issuer material. Restoring an
etcd snapshot, rebuilding a server, or reissuing the root is destructive or
trust-changing work and requires explicit action-time owner approval after the
exact source snapshot, target node, timestamp, size, and rollback are reviewed.

A normal cold boot should restore the CA Secrets from etcd and use locally
cached cert-manager images without WAN, public DNS, lab OpenBAO, or the lab
registry. Only an actual owner-approved disconnected cold boot proves that
claim.

## Rollback

Before any DroneOps leaf or ingress uses the issuer, rollback is a reviewed Git
revert of the PKI Application or cert-manager Application. Do not delete CA
Secrets, CRDs, or namespaces as a routine rollback. cert-manager CRD deletion
can cascade-delete Certificate and Issuer resources.

After a leaf exists, leave the PKI in place during an application rollback.
Restore only the previous DroneOps ingress/configuration through its owning
repository. Removing client trust, deleting issuer material, restoring etcd,
or rebooting rack nodes are separate owner-approved actions.

