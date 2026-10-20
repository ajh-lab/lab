# External Secrets Operator Deployment

Chart: `external-secrets/external-secrets`
Version: `0.10.7`
Namespace: `external-secrets`

## Why This Version

Newer chart versions worked poorly on this k3s baseline (`v1.28.x`) due CRD validation and push-secret related issues.

## Key Settings

- `installCRDs: true`
- `crds.createPushSecret: false`
- `processPushSecret: false`

## Included OpenBao Integration Manifest

- `k8s/manifests/external-secrets/openbao/store-and-sample.yaml`
  - `ClusterSecretStore` -> dedicated OpenBao host `http://192.168.1.25:8200`
  - demo `ExternalSecret` -> `default/demo-from-openbao`
- [Approved recovery and manual token maintenance](../../../docs/openbao-eso-maintenance.md)
  records the 2026-10-20 scoped ESO recovery and separate controller/API
  stability gate. This release is standalone Helm-managed; no ESO Argo
  Application was found at that observation.
- `k8s/manifests/external-secrets/openbao/pulsetrader-read.hcl` is an additive
  public policy fragment, not a complete policy. Never write it alone over the
  shared `eso-read-lab` policy; preserve all existing rules.

## Deploy

```bash
helm upgrade --install external-secrets external-secrets/external-secrets \
  --version 0.10.7 \
  -n external-secrets --create-namespace \
  -f k8s/helm/external-secrets/values.yaml
```
