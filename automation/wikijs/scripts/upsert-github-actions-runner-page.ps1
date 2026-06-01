param(
  [string]$EnvPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
  throw "Missing env file: $EnvPath"
}

$envMap = @{}
Get-Content -LiteralPath $EnvPath | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k, $v = $_ -split '=', 2
  $envMap[$k.Trim()] = $v.Trim().Trim('"')
}

$apiKey = $envMap["WIKIJS_ADMIN_API_KEY"]
if ([string]::IsNullOrWhiteSpace($apiKey)) {
  throw "WIKIJS_ADMIN_API_KEY missing in .env"
}

$uri = "https://wikijs.192.168.1.80.sslip.io/graphql"
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

function Invoke-WikiGql {
  param(
    [Parameter(Mandatory = $true)][string]$Query,
    [hashtable]$Variables
  )

  $body = @{ query = $Query; variables = $Variables } | ConvertTo-Json -Depth 20
  try {
    $resp = Invoke-RestMethod -Method POST -Uri $uri -Headers @{ Authorization = "Bearer $apiKey" } -ContentType "application/json" -Body $body
  } catch {
    if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream()) {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $raw = $reader.ReadToEnd()
      throw "Wiki GraphQL HTTP error. Payload: $raw"
    }
    throw
  }
  if ($resp.errors) {
    throw ($resp.errors | ConvertTo-Json -Depth 20)
  }
  return $resp.data
}

$path = "services/github-actions-runner"
$locale = "en"
$tags = @("services", "infrastructure", "github-actions", "arc", "k3s")
$title = "GitHub Actions Runner"
$description = "Lab self-hosted GitHub Actions runner image and ARC deployment"
$content = @'
# GitHub Actions Runner

## Overview
- Repository: `ajh-lab/homelab-gha-runner`
- Runner image: `192.168.1.15:5000/lab/github-actions-runner:0.1.0`
- Registry: internal Docker Registry v2 at `192.168.1.15:5000`
- Kubernetes cluster: lab k3s on Raspberry Pi 5 nodes (`linux/arm64`)
- ARC controller namespace: `arc-systems`
- Runner namespace: `arc-runners`
- Runner mode: ARC runner scale set with Docker-in-Docker sidecar

## Runner Targets
- Primary shared target: `lab-org-arm64-dind`
- Bootstrap/fallback repo target: `lab-k3s-arm64-dind`

Use the shared target in trusted `ajh-lab` organization repositories:

```yaml
runs-on: lab-org-arm64-dind
```

Use the fallback target only for bootstrap or recovery of `ajh-lab/homelab-gha-runner`:

```yaml
runs-on: lab-k3s-arm64-dind
```

## Labels
- `lab`
- `k3s`
- `rpi5`
- `arm64`
- `dind`
- `docker`
- `arc`
- `org` on the organization-scoped scale set

## Docker-in-Docker
The runner pod uses a custom runner container plus a privileged `docker:29-dind` sidecar. The sidecar exposes `/var/run/docker.sock` to the runner and is configured with:

```text
--insecure-registry=192.168.1.15:5000
```

That is required because the lab registry serves HTTP on the LAN.

## ArgoCD Applications
- `arc-controller`: deployed and healthy
- `arc-lab-k3s-arm64-dind`: repo-scoped fallback runner, deployed and healthy
- `arc-ajh-lab-arm64-dind`: org-scoped shared runner, defined in Git but not applied until the org runner credential is available

## Required Secrets
Kubernetes secrets in `arc-runners`:

- `lab-registry-pull`: image pull secret for `192.168.1.15:5000`
- `arc-github-config`: repo-scoped fallback ARC token
- `arc-github-org-config`: org-scoped ARC token for `ajh-lab`

GitHub Actions secrets:

- `LAB_REGISTRY_USERNAME`
- `LAB_REGISTRY_PASSWORD`

## Current Credential Requirement
The available GitHub token currently has `gist`, `read:org`, `repo`, and `workflow` scopes. GitHub rejects organization runner APIs and organization Actions secrets with HTTP 403 until an org-capable credential is provided.

For a classic PAT, refresh or create a token with `admin:org` in addition to the existing repo/workflow scopes. For a fine-grained token or GitHub App, grant organization self-hosted runner read/write permission and the organization settings permissions GitHub requires for ARC registration.

After the credential is available, create or update:

```powershell
kubectl create secret generic arc-github-org-config `
  --namespace arc-runners `
  --from-literal=github_token="<org-capable-token>" `
  --dry-run=client `
  -o yaml | kubectl apply -f -
```

Then apply the org runner ArgoCD application:

```powershell
kubectl apply --server-side -f argocd/applications/arc-ajh-lab-arm64-dind-runner-scale-set.yaml
```

## Verification
```powershell
kubectl get application.argoproj.io -n argocd
kubectl get autoscalingrunnersets.actions.github.com -n arc-runners -o wide
kubectl get pods -n arc-systems
kubectl get pods -n arc-runners
gh api orgs/ajh-lab/actions/runners --jq '.runners[]? | {id,name,status,busy}'
```

## Safety Notes
- Restrict the org runner to trusted private repositories unless workflow policy has been reviewed.
- Docker-in-Docker requires a privileged sidecar.
- Do not commit GitHub tokens, registry credentials, kubeconfigs, or OpenBao tokens.
- Do not expose the lab registry outside the LAN without TLS and authentication review.
'@

$searchExistingQuery = @'
query ($query: String!, $locale: String!) {
  pages {
    search(query: $query, locale: $locale, path: "") {
      results { id path title }
    }
  }
}
'@
$existingSearch = Invoke-WikiGql -Query $searchExistingQuery -Variables @{ query = "github actions runner arc"; locale = $locale }
$match = @($existingSearch.pages.search.results) | Where-Object { $_.path -eq $path } | Select-Object -First 1
if ($null -eq $match) {
  $match = @($existingSearch.pages.search.results) | Where-Object { $_.title -eq $title } | Select-Object -First 1
}

if ($null -ne $match -and $match.id) {
  $updateQuery = @'
mutation ($id: Int!, $content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    update(id: $id, content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded errorCode message slug }
      page { id path title }
    }
  }
}
'@

  $result = Invoke-WikiGql -Query $updateQuery -Variables @{
    id = [int]$match.id
    content = $content
    description = $description
    editor = "markdown"
    isPublished = $true
    isPrivate = $false
    locale = $locale
    path = $path
    tags = $tags
    title = $title
  }

  if (-not $result.pages.update.responseResult.succeeded) {
    throw "Wiki update failed: $($result.pages.update.responseResult.message)"
  }

  Write-Host ("wiki_action=updated path=/en/{0}" -f $result.pages.update.page.path)
} else {
  $createQuery = @'
mutation ($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded errorCode message slug }
      page { id path title }
    }
  }
}
'@

  $result = Invoke-WikiGql -Query $createQuery -Variables @{
    content = $content
    description = $description
    editor = "markdown"
    isPublished = $true
    isPrivate = $false
    locale = $locale
    path = $path
    tags = $tags
    title = $title
  }

  if (-not $result.pages.create.responseResult.succeeded) {
    throw "Wiki create failed: $($result.pages.create.responseResult.message)"
  }

  Write-Host ("wiki_action=created path=/en/{0}" -f $result.pages.create.page.path)
}
