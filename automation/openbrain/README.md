# OpenBrain Automation

This automation bootstraps and deploys a self-hosted OpenBrain memory service into the k3s cluster.

## What Gets Deployed

- Namespace: `openbrain`
- External PostgreSQL + pgvector (hosted on `lab-pgsql01`)
- OpenBrain MCP server (`openbrain-mcp` Deployment)
- Ingress: `https://openbrain.192.168.1.80.sslip.io`
- ExternalSecret that reads credentials from OpenBao path `secret/lab/runtime/openbrain`

## Runtime Model Provider

By default this deployment uses:

- Embeddings: `nomic-embed-text`
- Chat metadata extraction: `qwen3-coder:latest`
- Database: `lab-pgsql01` (`openbrain` database)

The script ensures `nomic-embed-text` exists on the workstation before deployment.
It builds the MCP image locally and publishes it to `ttl.sh` for cluster pulls.

## Prerequisites

- `kubectl` installed on this machine
- `docker` installed on this machine
- Network connectivity to k3s cluster
- Lab `.env` contains at least:
  - `AI_WORKSTATION_IP`
  - `LAB_SECRETS01_OPENBAO_ADDR`
  - `LAB_SECRETS01_OPENBAO_ROOT_TOKEN` (or deploy/context token with write access)

Note: `ttl.sh` tags are temporary (24h). For long-term use, move this image to your internal registry after k3s insecure-registry config is enabled.

## Deploy

```powershell
Set-Location C:\Users\adamj\SourceControl\lab
./automation/openbrain/scripts/deploy-openbrain.ps1
```

## Verification

```powershell
$env:KUBECONFIG = "C:\Users\adamj\SourceControl\lab\.kubeconfig-192.168.1.80.yaml"
kubectl get pods -n openbrain
kubectl get ingress -n openbrain
```

## MCP Client Header

MCP requests require header:

- `x-brain-key: <OPENBRAIN_MCP_ACCESS_KEY>`

Fetch the key from OpenBao path `secret/lab/runtime/openbrain` field `mcp_access_key`.
