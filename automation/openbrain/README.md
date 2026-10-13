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
Images are built in-cluster on the arm64 Pis via the kaniko job manifest
(`automation/openbrain/kaniko-build-job.yaml`; see the header comment for the
ConfigMap build-context and kaniko subPath-mount gotcha) and pushed to the lab
registry `192.168.1.15:5000/openbrain-mcp-server`. Docker Desktop is not
available on the Windows workstation, so `docker build` is no longer the build
path from here.

## Prerequisites

- `kubectl` installed on this machine
- Network connectivity to k3s cluster
- Lab `.env` contains at least:
  - `AI_WORKSTATION_IP`
  - `LAB_SECRETS01_OPENBAO_ADDR`
  - `LAB_SECRETS01_OPENBAO_ROOT_TOKEN` (or deploy/context token with write access)

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

MCP requests require one of these keys in the `x-brain-key` header:

- Per-harness key from OpenBao path `secret/lab/runtime/openbrain` field
  `mcp_keys_json` (JSON map: key -> `{ harness, scopes[], default_scope? }`;
  `"*"` in scopes means all scopes). Capture defaults to the key's default
  scope; search/list/stats can filter with `scopes` and are restricted to the
  key's allowed scopes.
- `mcp_access_key` (same OpenBao path) remains the legacy all-scope key.

Schema: `thoughts.scope` column (migration
`automation/openbrain/migrations/002_scope.sql`, default `global`) plus
provenance (`captured`/`human`) and harness name in metadata. Scope isolation
is enforced server-side per key.

## Harness Client Wiring (DSH desktop)

`svc/openbrain-mcp-lan` (manifest `service-nodeport.yaml`, NodePort `32100`)
fronts the same pods as the ClusterIP service on plain HTTP. It exists because
the DSH MCP client has no insecure-TLS option, and its process does not trust
the `lab-selfsigned` CA; the ingress and its certificate are left unchanged for
existing consumers. The client connects to `http://192.168.1.80:32100/`.

The harness entry lives in the DSH profile patch
`~/.dsh/profiles/desktop/cordis.patch.yml` as an `insert` of
`@deepseek-ai/dsh-mcp-client` (`serverName: openbrain`,
`transport: streamable-http`). `serverName` namespaces the tools, so they
register as `mcp__openbrain__*`. The `x-brain-key` header carries the
`dsh-windows` harness credential (scopes `lab`, `global`; default `lab`) from
`mcp_keys_json`. The patch layer is read at process start, so **adding or
changing this entry requires a DSH restart**; a brand-new session is then
needed, because MCP servers attach at `session/new`.

Rollback: delete `svc/openbrain-mcp-lan` (`kubectl delete -n openbrain
service/openbrain-mcp-lan`) and restore the patch from the timestamped
`.bak-*` copy kept beside it.

