# Wiki.js Helm Values

This values file deploys Wiki.js to the `wikijs` namespace, points it to the external PostgreSQL VM (`lab-pgsql01`), and enables HTTPS ingress via Traefik + cert-manager.

Deploy command:

```powershell
helm upgrade --install wikijs requarks/wiki `
  --namespace wikijs `
  --create-namespace `
  -f k8s/helm/wikijs/values.yaml
```

Prerequisite issuer:

```powershell
kubectl apply -f k8s/manifests/cert-manager/clusterissuer-lab-selfsigned.yaml
```

Current HTTPS URL:

- `https://wikijs.192.168.1.80.sslip.io`
