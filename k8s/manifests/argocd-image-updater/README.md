# ArgoCD Image Updater

This manifest set repairs and source-controls the lab ArgoCD Image Updater deployment in the `argocd` namespace.

It is configured for:

- ArgoCD namespace: `argocd`
- Lab registry: `192.168.1.15:5000`
- Registry credentials: OpenBAO path `secret/homelab/registry/lab-registry01`, synced with External Secrets Operator
- Git write-back: configured per ArgoCD `Application` using repository credentials already stored in ArgoCD
- Runtime node: `oma01rpicls01mstr01`

Apply or reconcile manually:

```powershell
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml apply -k .\k8s\manifests\argocd-image-updater
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n argocd rollout status deploy/argocd-image-updater
```

Verify:

```powershell
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n argocd get pod -l app.kubernetes.io/name=argocd-image-updater -o wide
kubectl --kubeconfig .\.kubeconfig-192.168.1.80.yaml -n argocd logs deploy/argocd-image-updater --tail=100
```

Do not commit raw registry, GitHub, or ArgoCD credentials. Keep runtime secrets in OpenBAO and expose them through External Secrets Operator.
