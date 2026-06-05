param(
  [string]$Image = "192.168.1.15:5000/lab/github-actions-runner",
  [string]$Tag = "0.1.0",
  [string]$Platform = "linux/arm64"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

docker buildx create --use --name homelab-gha-runner-builder --config .\buildkitd.toml 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  docker buildx use homelab-gha-runner-builder | Out-Null
}

docker buildx build `
  --platform $Platform `
  --tag "${Image}:${Tag}" `
  --tag "${Image}:latest" `
  --push `
  .
