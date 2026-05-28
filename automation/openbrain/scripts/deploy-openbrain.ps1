param(
  [string]$EnvPath = "",
  [string]$KubeconfigPath = "",
  [string]$ImageTag = "0.1.0",
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
$registryImage = "ttl.sh/lab-openbrain-20260501:24h"

Write-Host "Ensuring Ollama embedding model exists on AI workstation..."
$pullBody = @{ model = 'nomic-embed-text'; stream = $false } | ConvertTo-Json
Invoke-RestMethod -Uri ("http://{0}:11434/api/pull" -f $envMap['AI_WORKSTATION_IP']) -Method Post -ContentType "application/json" -Body $pullBody -TimeoutSec 1800 | Out-Null

Write-Host "Bootstrapping OpenBrain secrets in OpenBao..."
& (Join-Path $PSScriptRoot "bootstrap-openbrain-secrets.ps1") -EnvPath $EnvPath

if (-not $SkipBuildLoad) {
  Write-Host "Building OpenBrain MCP image: $image"
  docker build -t $image (Join-Path $repoRoot "k8s\openbrain\server")
  Assert-LastExit "docker build"

  Write-Host "Publishing image to ttl.sh for cluster pull..."
  docker tag $image $registryImage
  Assert-LastExit "docker tag"
  docker push $registryImage
  Assert-LastExit "docker push"
}

if (-not $SkipApply) {
  $env:KUBECONFIG = $KubeconfigPath
  Write-Host "Applying OpenBrain manifests..."
  kubectl apply -k (Join-Path $repoRoot "k8s\manifests\openbrain")
  Assert-LastExit "kubectl apply"

  Write-Host "Waiting for OpenBrain rollout..."
  kubectl rollout status statefulset/openbrain-db -n openbrain --timeout=300s
  Assert-LastExit "kubectl rollout statefulset/openbrain-db"
  kubectl rollout status deployment/openbrain-mcp -n openbrain --timeout=300s
  Assert-LastExit "kubectl rollout deployment/openbrain-mcp"

  Write-Host "OpenBrain deployed."
  kubectl get pods -n openbrain
  kubectl get ingress -n openbrain
}

Write-Host "Done. OpenBrain URL: https://openbrain.192.168.1.80.sslip.io"
