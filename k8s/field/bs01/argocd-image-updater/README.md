# BS01 ArgoCD Image Updater

This overlay deploys ArgoCD Image Updater into the BS01 field cluster by reusing
the shared lab manifest at `k8s/manifests/argocd-image-updater`.

The shared manifest pins the updater to the main lab Raspberry Pi control-plane
node. This BS01 overlay removes that node selector so the updater can schedule
on the BS01 k3s nodes.

## Purpose

The DroneOps BS01 ArgoCD application tracks immutable image tags such as
`sha-<commit>` through ArgoCD Image Updater annotations. The updater watches the
lab registry at `192.168.1.15:5000` and writes selected tags back to the
DroneOps Helm values file using the ArgoCD repository credential secret.

This avoids relying on mutable `sha-latest` images after service builds finish.

## Apply

```powershell
kubectl --kubeconfig .\.kubeconfig-bs01-field.yaml apply -k .\k8s\field\bs01\argocd-image-updater
kubectl --kubeconfig .\.kubeconfig-bs01-field.yaml -n argocd rollout status deploy/argocd-image-updater
```

## Verify

```powershell
kubectl --kubeconfig .\.kubeconfig-bs01-field.yaml -n argocd get pod -l app.kubernetes.io/name=argocd-image-updater -o wide
kubectl --kubeconfig .\.kubeconfig-bs01-field.yaml -n argocd logs deploy/argocd-image-updater --tail=100
```

Do not commit raw registry, GitHub, or ArgoCD credentials. Runtime credentials
must come from OpenBAO/External Secrets Operator or the existing ArgoCD
repository credential secret.
