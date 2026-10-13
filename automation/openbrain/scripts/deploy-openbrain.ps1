param(
  [string]$EnvPath = "",
  [string]$KubeconfigPath = "",
  [string]$ImageTag = "0.2.0",
  [switch]$SkipBuildLoad,
  [switch]$SkipApply
)

$ErrorActionPreference = "Stop"

function Assert-LastExit {
  param([string]$Step)
  if ($LASTEXITCODE -ne 0) {
    throw "$Step failed with exit code $LASTEXITCODE"
  }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
if ([string]::IsNullOrWhiteSpace($EnvPath)) {
  $EnvPath = Join-Path $repoRoot ".env"
}
if ([string]::IsNullOrWhiteSpace($KubeconfigPath)) {
  $KubeconfigPath = Join-Path $repoRoot ".kubeconfig-192.168.1.80.yaml"
}

$modulePath = Join-Path $repoRoot "automation\common\SecretResolver.psm1"
Import-Module $modulePath -Force
$envMap = Get-LabEnvMap -Path $EnvPath

$required = @(
  'AI_WORKSTATION_IP',
  'LAB_SECRETS01_OPENBAO_ADDR'
)
foreach ($k in $required) {
  if (-not $envMap.ContainsKey($k) -or [string]::IsNullOrWhiteSpace($envMap[$k])) {
    throw "Missing required .env key: $k"
  }
}

$image = "openbrain-mcp-server:$ImageTag"
$registryImage = "192.168.1.15:5000/openbrain-mcp-server:$ImageTag"

Write-Host "Ensuring Ollama embedding model exists on AI workstation..."
$pullBody = @{ model = 'nomic-embed-text'; stream = $false } | ConvertTo-Json
Invoke-RestMethod -Uri ("http://{0}:11434/api/pull" -f $envMap['AI_WORKSTATION_IP']) -Method Post -ContentType "application/json" -Body $pullBody -TimeoutSec 1800 | Out-Null

Write-Host "Bootstrapping OpenBrain secrets in OpenBao..."
& (Join-Path $PSScriptRoot "bootstrap-openbrain-secrets.ps1") -EnvPath $EnvPath

if (-not $SkipBuildLoad) {
  # Docker Desktop is not available on the Windows workstation; builds run
  # in-cluster on the arm64 Pis via the kaniko job manifest. Kaniko needs the
  # build context as a ConfigMap with subPath mounts (plain ConfigMap mounts are
  # symlinks and end up dangling in the pushed image).
  $serverDir = Join-Path $repoRoot "k8s\openbrain\server"
  Write-Host "Creating build-context ConfigMap..."
  kubectl --kubeconfig $KubeconfigPath -n openbrain create configmap openbrain-build-ctx `
    --from-file="$serverDir\Dockerfile" --from-file="$serverDir\deno.json" --from-file="$serverDir\index.ts" `
    --dry-run=client -o yaml | kubectl --kubeconfig $KubeconfigPath apply -f -
  Assert-LastExit "configmap create"

  Write-Host "Running kaniko build job (pushes $registryImage)..."
  kubectl --kubeconfig $KubeconfigPath delete job openbrain-build --ignore-not-found --wait=false
  kubectl --kubeconfig $KubeconfigPath apply -f (Join-Path $repoRoot "automation\openbrain\kaniko-build-job.yaml")
  Assert-LastExit "kaniko job apply"
  kubectl --kubeconfig $KubeconfigPath -n openbrain wait --for=condition=complete job/openbrain-build --timeout=900s
  Assert-LastExit "kaniko build job"
}

if (-not $SkipApply) {
  $env:KUBECONFIG = $KubeconfigPath
  Write-Host "Applying OpenBrain manifests..."
  kubectl apply -k (Join-Path $repoRoot "k8s\manifests\openbrain")
  Assert-LastExit "kubectl apply"

  # DB runs externally on lab-pgsql01; the in-namespace statefulset is vestigial.
  Write-Host "Waiting for OpenBrain rollout..."
  kubectl rollout status deployment/openbrain-mcp -n openbrain --timeout=300s
  Assert-LastExit "kubectl rollout deployment/openbrain-mcp"

  Write-Host "OpenBrain deployed."
  kubectl get pods -n openbrain
  kubectl get ingress -n openbrain
}

Write-Host "Done. OpenBrain URL: https://openbrain.192.168.1.80.sslip.io"
