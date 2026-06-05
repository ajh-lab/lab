# Homelab GitHub Actions Runner

Private infrastructure repository for the lab GitHub Actions self-hosted runner image and ARC deployment.

## Purpose

This repo builds and deploys an ARM64 GitHub Actions runner for the home lab k3s cluster, which runs on Raspberry Pi 5 nodes. The runner is managed by GitHub Actions Runner Controller (ARC) using the modern runner scale set charts.

The primary shared runner target is:

```yaml
runs-on: lab-org-arm64-dind
```

## Architecture

- Runner image: `192.168.1.15:5000/lab/github-actions-runner:0.1.0`
- Registry: internal Docker Registry v2 at `192.168.1.15:5000`
- Kubernetes cluster: lab k3s on Raspberry Pi 5 nodes (`linux/arm64`)
- Controller namespace: `arc-systems`
- Runner namespace: `arc-runners`
- Runner mode: ARC runner scale set with Docker-in-Docker sidecar
- GitHub scope: organization-scoped runner for `ajh-lab`
- GitHub runner group: `Private Lab Runners`
- ArgoCD applications:
  - `arc-controller`
  - `arc-ajh-lab-arm64-dind`
- ARC controller service account: `arc-systems/arc-gha-rs-controller`

## Why Docker-in-Docker

The runner needs to build and push container images from GitHub Actions workflows. The ARC runner pod runs:

- a `runner` container using this custom image
- a privileged `docker:29-dind` sidecar container
- shared `/var/run/docker.sock`
- shared `/home/runner/_work`

The upstream ARC chart documents a restartable-init-container sidecar pattern for DinD. This lab currently runs k3s v1.28, so the applied values use a regular sidecar container without a per-container `restartPolicy`.

The DinD daemon is configured with:

```text
--insecure-registry=192.168.1.15:5000
```

That is required because the lab registry currently serves HTTP on the LAN.

## Runner Image Contents

The image extends `ghcr.io/actions/actions-runner:latest` and adds common CI tools:

- Docker CLI and Buildx plugin
- GitHub CLI
- kubectl
- Helm
- jq and yq
- Python 3 and pip
- make, curl, wget, unzip, rsync, SSH client, and network diagnostics

The Dockerfile pins kubectl and copies Helm from a pinned `alpine/helm` image so builds are repeatable on the ARM64 k3s runner nodes. Tools available from Ubuntu's ARM64 repositories, including `gh` and `yq`, are installed from apt to avoid GitHub release-asset timeouts during in-cluster builds.

## Labels

The shared scale set is named `lab-org-arm64-dind`. It also records these labels:

- `lab`
- `k3s`
- `rpi5`
- `arm64`
- `dind`
- `docker`
- `arc`
- `org`

For ARC runner scale sets, use the scale set name as the workflow `runs-on` value.

The scale set is assigned to the `Private Lab Runners` GitHub runner group. Org-level registry secrets are configured with private-repository visibility.

## Build Locally

From this repository:

```powershell
.\scripts\build-and-push-local.ps1
```

The local build script uses `buildkitd.toml` so BuildKit pushes to the lab registry over HTTP.

The script builds `linux/arm64` and pushes:

- `192.168.1.15:5000/lab/github-actions-runner:0.1.0`
- `192.168.1.15:5000/lab/github-actions-runner:latest`

Registry credentials must come from OpenBao or the local lab secret resolver; do not put credentials in this repo.

## Build In GitHub Actions

The workflow at `.github/workflows/build-runner-image.yml` uses:

```yaml
runs-on: lab-org-arm64-dind
```

Required GitHub organization or repository secrets:

- `LAB_REGISTRY_USERNAME`
- `LAB_REGISTRY_PASSWORD`

The workflow builds and pushes the same ARM64 runner image back to the lab registry.

## Deploy With ArgoCD

Apply the ArgoCD application manifests:

```powershell
$env:KUBECONFIG = "c:\Users\adamj\SourceControl\lab\.kubeconfig-192.168.1.80.yaml"
kubectl apply -f argocd/applications/arc-controller.yaml
kubectl apply -f argocd/applications/arc-ajh-lab-arm64-dind-runner-scale-set.yaml
```

Secrets must exist before the runner scale set can become healthy:

- `arc-runners/arc-github-org-config`
- `arc-runners/lab-registry-pull`

The runner and DinD externals init container use `imagePullPolicy: Always` so fresh ephemeral pods pull the current lab registry image for the pinned tag.

## Repository Fallback Runner

The repo still includes a repository-scoped fallback runner at `lab-k3s-arm64-dind` for `ajh-lab/homelab-gha-runner`. It is useful for bootstrap or recovery, but workflows that should run across multiple organization repositories should use `lab-org-arm64-dind`.

## Organization Shared Runner

The repo defines an organization-scoped ARC runner scale set for the `ajh-lab` GitHub organization:

- values: `arc/values/ajh-lab-arm64-dind.yaml`
- ArgoCD app: `argocd/applications/arc-ajh-lab-arm64-dind-runner-scale-set.yaml`
- workflow target: `lab-org-arm64-dind`

That app requires an org-capable ARC credential in `arc-runners/arc-github-org-config`. See `docs/org-shared-runner.md`.

## Security Notes

- Runner pods execute arbitrary workflow code from the configured repository.
- Docker-in-Docker requires a privileged sidecar.
- Restrict this runner to trusted private organization repositories unless repository workflow policy has been reviewed.
- Do not expose the lab registry outside the LAN without TLS and authentication review.
- Do not commit GitHub tokens, registry credentials, kubeconfigs, or OpenBao tokens.

## References

- GitHub ARC runner scale set docs: <https://docs.github.com/en/actions/how-tos/manage-runners/use-actions-runner-controller/deploy-runner-scale-sets>
- ARC charts: <https://github.com/actions/actions-runner-controller>
