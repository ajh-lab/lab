# Phase 1 Agent To-Do (LAB)

Last updated: 2026-04-29 13:56 (America/Chicago)

Machine-readable queue files:

- `phase1-agent-queue.yaml`
- `phase1-agent-queue.json`

## Objective

Build a durable internal control plane where AI agents can safely read context, execute work, update documentation, and eventually process tickets from a queue.

## Scope Notes

- `Hermes-Test` is temporary for agent behavior validation.
- The `lab` repo is the long-term system-of-record for backlog, architecture decisions, and runbooks.

## Execution Rules

- Every completed task must update:
  - `ai-baseline-context.md`
  - `network_devices.csv` (if infra changed)
  - relevant `k8s/` or `automation/` paths
- Secrets stay in secret management; do not store secret values in Markdown/CSV.
- Infrastructure changes require rollback notes in the same PR.

## Backlog (Phase 1)

| ID | Priority | Status | Task | Definition of Done |
|---|---|---|---|---|
| P1-001 | P0 | Done | Stand up internal Wiki.js knowledge system | Wiki.js is deployed with auth enabled, backed by PostgreSQL, reachable internally over HTTPS, and has initial documentation index/pages seeded (services directory + linked service docs). |
| P1-002 | P0 | Done | Provision internal PostgreSQL service host | Linux VM provisioned on ESXi, PostgreSQL hardened (non-default creds, backups, firewall), and documented connection details (no secrets) for Wiki.js and future internal apps. |
| P1-003 | P0 | Done | Replace OpenBao dev mode with persistent configuration | OpenBao VM service (`lab-secrets01`) is persistent and active, secrets migrated to KV v2, and ESO now reads from VM OpenBao via scoped token (`external-secrets/openbao-eso-token`). |
| P1-004 | P0 | Todo | Wire agents to controlled context sources | Agent runtime can read from NetBox API + Wiki API + `lab` repo, with explicit read/write boundaries documented. |
| P1-005 | P0 | Todo | Define agent change-write policy for wiki updates | Agent only writes to approved wiki paths (for example `Ops/Auto-Updates/*`) and appends timestamped change log entries with rollback note. |
| P1-006 | P1 | Todo | Introduce ticketing queue for agent work intake | Create Jira project (or interim queue file), define statuses (`Todo`, `Ready`, `In Progress`, `Blocked`, `Done`), and map required fields for agent execution. |
| P1-007 | P1 | Todo | Add agent ticket poller workflow | n8n or service workflow polls queue, executes only `Ready` tasks, posts progress updates, and returns completion/blocked status automatically. |
| P1-008 | P1 | Todo | Deploy self-hosted GitHub Actions runners | Runner host(s) deployed internally with labels, locked repo/org scope, and documented lifecycle update process. |
| P1-009 | P1 | Todo | Deploy internal image registry | Harbor (recommended) or equivalent deployed with TLS, auth, retention policies, vulnerability scanning baseline, and integration path documented for k3s workloads. |
| P1-010 | P1 | Todo | Add supply-chain controls for internal images | Enforce pull from internal registry for managed workloads, define image provenance/signing approach, and document exception handling. |
| P1-011 | P2 | Todo | Establish nightly agent operation runbook | Runbook includes start/stop procedures, failure budget handling, incident escalation, and evidence artifact expectations. |
| P1-012 | P2 | Todo | Build source-of-truth sync automation | Scheduled sync verifies consistency across `network_devices.csv`, NetBox, and wiki inventory pages, then creates drift report. |
| P1-013 | P1 | Todo | Expand Prometheus + Grafana monitoring coverage | Monitoring stack captures k3s, node/system metrics, and core service health with baseline dashboards and alerting rules. |
| P1-014 | P1 | Done | Install OpenClaw on AI workstation (side-by-side) | OpenClaw installed/validated on `ai-workstation-evox2` without breaking Hermes, with docs for start/status/update and secure runtime boundaries. |

## Ticketing Path (Planned)

### Immediate

- Continue using this file as the authoritative backlog queue.

### Next

- Move execution queue into Jira and keep this file as architecture + governance reference.

### Jira Free Plan Note

- Jira Cloud Free remains available for small teams.
- Typical current limits include up to 10 users and reduced admin/security customization compared with paid tiers.
- Re-verify plan limits before production adoption because Atlassian plan details can change.

## Ready Queue Seed (Suggested First Work Items)

1. P1-009 Internal image registry deployment (Harbor preferred).
2. P1-008 Self-hosted GitHub runner deployment.
3. P1-006 Jira project setup for agent queue intake.
