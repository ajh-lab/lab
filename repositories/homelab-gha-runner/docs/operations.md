# Operations

## Runner target

Use this runner scale set in workflows:

```yaml
runs-on: lab-org-arm64-dind
```

The primary scale set is organization-scoped to `ajh-lab`, so trusted repositories in that organization can share the same lab runner pool.

The scale set is assigned to the GitHub runner group `Private Lab Runners`.

## Labels

The runner scale set advertises these labels for inventory and future selection:

- `lab`
- `k3s`
- `rpi5`
- `arm64`
- `dind`
- `docker`
- `arc`
- `org`

For ARC runner scale sets, the scale-set name is the practical `runs-on` target.

## Secrets

Do not commit secrets to this repository.

Kubernetes secrets expected in `arc-runners`:

- `arc-github-org-config`: contains an org-capable `github_token` for ARC GitHub API registration.
- `arc-github-config`: contains a repo-capable fallback token for the bootstrap repository runner.
- `lab-registry-pull`: image pull secret for `192.168.1.15:5000`.

GitHub organization or repository secrets expected:

- `LAB_REGISTRY_USERNAME`
- `LAB_REGISTRY_PASSWORD`

The organization-level registry secrets should use private-repository visibility.

## Registry

Images are pushed to:

```text
192.168.1.15:5000/lab/github-actions-runner
```

The lab registry is HTTP/insecure inside the LAN. The runner scale set's Docker-in-Docker daemon includes:

```text
--insecure-registry=192.168.1.15:5000
```

## ArgoCD

The ArgoCD applications are:

- `arc-controller`
- `arc-ajh-lab-arm64-dind`

The controller deploys into `arc-systems`; the runner pods deploy into `arc-runners`.

## Repository fallback runner

The repository also contains a repo-scoped fallback runner scale set for bootstrap and recovery:

- values: `arc/values/lab-k3s-arm64-dind.yaml`
- ArgoCD app: `argocd/applications/lab-k3s-arm64-dind-runner-scale-set.yaml`
- workflow target: `lab-k3s-arm64-dind`

Prefer the org runner for normal CI once `arc-runners/arc-github-org-config` is in place. Use the fallback runner only for this runner-image repository when needed.
