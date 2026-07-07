---
name: lab-gitops
description: Deploy, verify, and troubleshoot lab k3s GitOps services. Use for k3s, kubectl, Helm, ArgoCD, External Secrets Operator, OpenBAO-backed Kubernetes secrets, lab container registry images, CI/CD, GitHub Actions self-hosted runners, and service deployment status.
---

# Lab GitOps

## Cluster Defaults

- k3s control plane: `oma01rpicls01mstr01` at `192.168.1.80`
- kubeconfig in repo: `.kubeconfig-192.168.1.80.yaml`
- ArgoCD URL: `http://192.168.1.80:32090`
- Internal registry: `http://192.168.1.15:5000`
- Ingress pattern: `*.192.168.1.80.sslip.io`

Use explicit kubeconfig from the repo:

```powershell
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml get nodes -o wide
```

## Before Disruptive Changes

Check cluster and webhook health:

```powershell
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml get nodes
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n cattle-system get deploy rancher-webhook
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n argocd get applications
```

## GitOps Layout

- Helm values: `k8s/helm/*/values.yaml`
- Bootstrap manifests: `k8s/manifests/*`
- ArgoCD app manifests usually live in target repos under `deploy/argocd/` or `argocd/`.
- External Secrets manifests should read OpenBAO through `ClusterSecretStore/openbao-store`.

Keep manifests in Git aligned with runtime state. If a live fix is made with `kubectl`, follow up with a repo change.

## ArgoCD

ArgoCD chart reference:

- `k8s/helm/argocd/README.md`
- namespace: `argocd`
- server service: `argocd-server` NodePort `32090`

Useful checks:

```powershell
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n argocd get application <app> -o wide
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n argocd describe application <app>
```

## External Secrets

ESO chart version is pinned for this k3s baseline:

- chart: `external-secrets/external-secrets`
- version: `0.10.7`
- namespace: `external-secrets`
- values: `k8s/helm/external-secrets/values.yaml`
- store manifest: `k8s/manifests/external-secrets/openbao/store-and-sample.yaml`

Verify OpenBAO sync:

```powershell
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml get clustersecretstore openbao-store
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml get externalsecret -A
```

## CI/CD And Registry

For new services, expect:

- GitHub Actions PR checks: tests, lint/type checks where applicable, image build validation.
- Self-hosted runner label: lab k3s arm64 DinD runner, documented in `automation/wikijs/scripts/upsert-github-actions-runner-page.ps1`.
- Image push target: `192.168.1.15:5000/<repo>/<image>:<tag>`.
- ArgoCD Application deploys the image into k3s.
- Runtime secrets come from OpenBAO via External Secrets, not committed Kubernetes Secret values.

After deployment, document the URL, namespace, ArgoCD app, secret paths, and registry image.
