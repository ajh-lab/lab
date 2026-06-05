# Organization Shared Runner

This repo includes an ARC runner scale set for the GitHub organization named `ajh-lab`.

Shared runners across multiple personal repositories require moving those repositories under an organization or enterprise runner scope. The `ajh-lab` organization is the shared scope for this lab.

## Target

- Organization: `ajh-lab`
- Runner scale set: `lab-org-arm64-dind`
- Runner group: `Private Lab Runners`
- ArgoCD application: `arc-ajh-lab-arm64-dind`
- Kubernetes namespace: `arc-runners`
- GitHub config URL: `https://github.com/ajh-lab`
- Kubernetes auth secret: `arc-runners/arc-github-org-config`

Use this in organization repositories:

```yaml
runs-on: lab-org-arm64-dind
```

## Credential Requirement

The organization-level ARC credential must exist before the ArgoCD application can become healthy. Applying the org runner app without `arc-runners/arc-github-org-config` or with a token that lacks org runner permissions will leave the app unhealthy.

GitHub documents organization creation as a web/settings flow:

- <https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/creating-a-new-organization-from-scratch>

GitHub documents ARC runner scale sets as supporting repository, organization, or enterprise `githubConfigUrl` values:

- <https://docs.github.com/en/actions/tutorials/use-actions-runner-controller/get-started>
- <https://docs.github.com/en/actions/tutorials/actions-runner-controller/authenticating-arc-to-the-github-api>

## Manual Prerequisites

1. Confirm the GitHub organization `ajh-lab` exists.
2. Create an ARC credential for organization runners.

Preferred auth is a GitHub App owned by the organization. A fine-grained PAT can also work if it has:

- Organization Administration: read
- Organization Self-hosted runners: read and write

For a classic PAT, GitHub's ARC docs call for `repo` and `admin:org` scopes for organization runners.

## Create The Kubernetes Secret

For a PAT-based setup:

```powershell
$env:KUBECONFIG = "c:\Users\adamj\SourceControl\lab\.kubeconfig-192.168.1.80.yaml"
$env:GITHUB_ORG_RUNNER_PAT = "<token value>"

kubectl create secret generic arc-github-org-config `
  --namespace arc-runners `
  --from-literal=github_token="$env:GITHUB_ORG_RUNNER_PAT" `
  --dry-run=client `
  -o yaml | kubectl apply -f -
```

Do not commit this token, place it in the repo, or put it in Wiki.js.

## Deploy The Org Runner

After the organization and secret exist:

```powershell
$env:KUBECONFIG = "c:\Users\adamj\SourceControl\lab\.kubeconfig-192.168.1.80.yaml"
kubectl apply --server-side -f .\argocd\applications\arc-ajh-lab-arm64-dind-runner-scale-set.yaml
```

Then verify:

```powershell
kubectl get application.argoproj.io -n argocd arc-ajh-lab-arm64-dind -o wide
kubectl get autoscalingrunnersets,ephemeralrunners -n arc-runners -o wide
gh api orgs/ajh-lab/actions/runners --jq '.runners[]? | {id,name,status,busy}'
```

## Repository Migration

After the org runner is online, move selected private repositories into `ajh-lab` and update workflows to use:

```yaml
runs-on: lab-org-arm64-dind
```

Keep public repositories off this runner unless their workflows are locked down. Self-hosted runners can execute workflow code from the repositories they are allowed to serve.
