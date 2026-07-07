---
name: openbao-secrets
description: Read, write, validate, and troubleshoot OpenBAO/OpenBao secrets for Adam's lab. Use when Codex, Helios, Hermes, or a Kanban worker needs credentials, API keys, webhooks, private keys, ExternalSecrets, OpenBAO KV v2 paths, the ai-workstation sudo password, provider keys such as DeepSeek, service runtime secrets, or safe guidance for storing and consuming secrets without leaking values.
---

# OpenBAO Secrets

## Core Rules

- Never print secret values. Report only key names, path names, presence, status, policy errors, or redacted summaries.
- Prefer OpenBAO first. Treat `.env` as a gitignored bootstrap/fallback source, not the durable integration pattern.
- Use repo helpers instead of adding new ad hoc `.env` parsing in scripts.
- Do not write tokens, passwords, webhook URLs, private keys, or API keys to Git, Wiki.js, Discord, Kanban comments, command logs, or Markdown.
- When validating a value exists, use exit codes, key listings, or hashes derived only inside the secret system. Do not echo the value.

## Lab Defaults

- OpenBAO host: `lab-secrets01` at `192.168.1.25`
- API URL: `http://192.168.1.25:8200`
- KV v2 mount: `secret`
- Bootstrap snapshot path: `secret/homelab/bootstrap/env`
- OpenBAO binary on the secret host: `bao`
- OpenBAO service on the secret host: `openbao`
- Storage backend on the secret host: `/opt/openbao/data`
- Existing curated paths:
  - `secret/homelab/services/n8n`
  - `secret/homelab/services/netbox`
  - `secret/homelab/services/unifi`
  - `secret/homelab/registry/lab-registry01`
  - `secret/homelab/vms/spt02`
  - `secret/homelab/services/kalshi-research-agent`
  - `secret/homelab/services/kalshi-research-bot`
  - `secret/lab/runtime/*` for legacy runtime secrets used by some k3s services

Read `ai-baseline-context.md` for current service-specific paths before changing anything.

## Use Repo Helpers

PowerShell automation should import:

```powershell
Import-Module .\automation\common\SecretResolver.psm1 -Force
$envMap = Get-LabEnvMap -Path .\.env
$value = Resolve-LabSecret -Key "NETBOX_ADMIN_API_TOKEN" -EnvMap $envMap
```

Supported helper functions:

- `Get-LabEnvMap`
- `Get-OpenBaoConfig`
- `Get-OpenBaoKvV2Secret`
- `Invoke-OpenBaoWriteKvV2`
- `Resolve-LabSecret`

To sync bootstrap `.env` values and curated service secrets into OpenBAO:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation\secrets\scripts\sync-env-to-openbao.ps1
```

Use `-SkipServicePaths` only when intentionally writing the bootstrap snapshot without curated service path updates.

## Add Or Update A Secret

Prefer a service-specific path for new services or providers. Keep field names stable and lower snake_case unless an existing consumer requires an environment-style name.

Examples:

- DeepSeek provider key: `secret/homelab/providers/deepseek`, field `api_key`
- Service webhook: `secret/homelab/services/<service-name>`, field `discord_webhook_url`
- Database URL: `secret/homelab/services/<service-name>`, field `database_url`

If the secret must be exposed as an environment variable to a legacy tool, either:

1. Store it in the curated path and teach the consumer to read that path, or
2. Add an explicit mapping in `.env` with `LAB_SECRET_PATH__<KEY>` and `LAB_SECRET_FIELD__<KEY>`, then sync with `sync-env-to-openbao.ps1`.

Do not use the broad bootstrap env snapshot as the first choice for new runtime integrations.

## ai-workstation Access

On `ai-workstation-evox2` (`helios@192.168.1.123`), bootstrap fields are read with:

```bash
openbao-env-get FIELD_NAME >/dev/null && echo OK
```

The workstation sudo password field is `AI_WORKSTATION_PASSWORD` at `secret/homelab/bootstrap/env`. Hermes service sudo support expects `SUDO_PASSWORD` injected by `/home/helios/.local/bin/hermes-openbao-sudo-env`; do not put the password in Hermes config.

Hermes user service drop-ins carry the OpenBAO connection details:

- `~/.config/systemd/user/hermes-gateway.service.d/20-openbao.conf`
- `~/.config/systemd/user/hermes-dashboard.service.d/20-openbao.conf`
- `~/.config/systemd/user/hermes-gateway.service.d/30-sudo-password-openbao.conf`
- `~/.config/systemd/user/hermes-dashboard.service.d/30-sudo-password-openbao.conf`

If `openbao-env-get` returns `403`, report the policy/path mismatch and fall back only to existing local bootstrap mechanisms already documented in the lab repo. Do not invent a new token source.

## Direct OpenBAO CLI/API Pattern

Use `bao kv get`/`bao kv put` only when the helper module cannot cover the task. Set environment variables without echoing token values:

```bash
export BAO_ADDR=http://192.168.1.25:8200
export BAO_TOKEN=...
bao kv get -mount=secret homelab/services/netbox
bao kv put -mount=secret homelab/providers/deepseek api_key=...
```

When validating a write, check metadata/key presence, not values:

```bash
bao kv get -mount=secret -format=json homelab/providers/deepseek \
  | jq '.data.data | keys'
```

PowerShell direct API writes should use `Invoke-OpenBaoWriteKvV2` from `automation/common/SecretResolver.psm1`, not handcrafted URL strings, unless debugging the helper itself.

## Kubernetes External Secrets

External Secrets Operator reads OpenBAO through:

- `ClusterSecretStore/openbao-store`
- token secret: `external-secrets/openbao-eso-token`
- manifest: `k8s/manifests/external-secrets/openbao/store-and-sample.yaml`

For new k3s services, prefer `ExternalSecret` manifests that read from OpenBAO instead of committing Kubernetes `Secret` values.

ExternalSecret `remoteRef.key` values are relative to the `secret/` mount. For example, `secret/lab/runtime/wikijs` is referenced as:

```yaml
remoteRef:
  key: lab/runtime/wikijs
  property: db_password
```

After changing OpenBAO-backed Kubernetes secrets, verify:

```bash
kubectl --kubeconfig .kubeconfig-192.168.1.80.yaml get clustersecretstore openbao-store
kubectl --kubeconfig .kubeconfig-192.168.1.80.yaml get externalsecret -A
```

## Recovery Checks

If OpenBAO is unreachable:

1. Check whether `lab-secrets01` (`192.168.1.25`) is powered on and reachable.
2. Check `openbao` service status on the host.
3. Check seal state with `bao status` without printing unseal keys.
4. If sealed, tell the user an unseal key is required; do not guess or search chat history for key material.
5. After recovery, verify External Secrets return to `SecretSynced`.

## Reporting Pattern

Good status report:

```text
OpenBAO reachable. Path secret/homelab/providers/deepseek exists and contains field api_key. I did not print the value.
```

Bad status report:

```text
The DeepSeek key is sk-...
```
