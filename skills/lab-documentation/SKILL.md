---
name: lab-documentation
description: Update and verify lab documentation systems. Use when Codex needs to update ai-baseline-context.md, Wiki.js service/runbook pages, NetBox inventory/service records, network_devices.csv, or post-deployment documentation after lab infrastructure or service changes.
---

# Lab Documentation

## Documentation Targets

Keep these in sync after service or infrastructure changes:

- `ai-baseline-context.md`: AI-ingestable source of truth.
- `network_devices.csv`: canonical inventory and device metadata.
- Wiki.js: human-readable service/runbook pages.
- NetBox: IPAM, devices, VMs, interfaces, and primary IP relationships.

Do not document raw secrets. Use OpenBAO path and field names only.

## Baseline Context

Update `ai-baseline-context.md` with durable operational facts:

- service name, repo, owner/workstream
- URLs and ingress hosts
- namespace and ArgoCD application
- OpenBAO secret paths and field names
- registry image coordinates
- Wiki.js page path
- NetBox modeling notes
- verification commands and current status

Keep transient debugging output in `tmp/<task-or-topic>/`, not the repo root.

## Wiki.js

Preferred automation lives in `automation/wikijs/scripts/`.

Existing examples:

- `upsert-registry-page.ps1`
- `upsert-github-actions-runner-page.ps1`
- `upsert-spt-fika-page.ps1`

Use `automation/common/SecretResolver.psm1` and `Resolve-LabSecret` for `WIKIJS_ADMIN_API_KEY` in new scripts. Older scripts may still read `.env` directly; avoid copying that pattern.

Wiki.js URL:

```text
https://wikijs.192.168.1.80.sslip.io/graphql
```

## NetBox

Preferred automation:

```powershell
.\automation\netbox\scripts\sync-network-devices-to-netbox.ps1 -WhatIf
.\automation\netbox\scripts\sync-netbox-assets-from-csv.ps1 -IncludeHostnameOnly
```

For UniFi-derived inventory:

```powershell
.\automation\unifi\scripts\fetch-unifi-inventory.ps1
.\automation\unifi\scripts\sync-unifi-to-netbox.ps1 -FetchFresh
```

Resolve `NETBOX_ADMIN_API_TOKEN` through OpenBAO-aware helpers in new automation.

## Inventory Edits

When manually editing `network_devices.csv`:

- Preserve headers and existing conventions.
- Update `LastUpdated`.
- Store credential references, not credential values.
- After meaningful inventory edits, run NetBox sync scripts and report created/updated/skipped counts.

## Completion Checklist

For new services, documentation is not done until:

- baseline context updated
- Wiki.js service/runbook page created or updated
- NetBox entry updated when the service maps to an asset/IP/application
- OpenBAO path and fields documented without values
- ArgoCD/namespace/URL/registry image documented
