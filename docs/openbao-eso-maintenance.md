# OpenBao ESO recovery and manual maintenance

Observed 2026-10-20 UTC under owner-approved PulseTrader paper delivery,
owning [PulseTrader #3](https://github.com/ajh-lab/PulseTrader/issues/3).
Lab owns shared identity/maintenance; product and rollout evidence belongs in
the [PulseTrader checkpoint](https://github.com/ajh-lab/PulseTrader/blob/main/docs/context/project-status.md).
This document and the public policy fragment apply no infrastructure changes.

## Authority and exact scope

- OpenBao: `http://192.168.1.25:8200`, KV v2 mount `secret`.
- Store: `ClusterSecretStore/openbao-store`.
- Static credential reference: `external-secrets/openbao-eso-token`, field
  `data.token`; policy **only `eso-read-lab`**, no default/root policy.
- Authoritative bootstrap: `secret/homelab/bootstrap/env`, existing field
  `LAB_SECRETS01_OPENBAO_ESO_TOKEN`. The ignored Lab `.env` has the same named
  fallback field. Kubernetes/bootstrap/fallback equality was verified in memory
  after recovery; bootstrap version was 677.
- Current identity: orphan service token, periodic **768h / 2764800s**, renewable,
  unlimited uses (`num_uses=0`), no explicit maximum TTL. Created
  **2026-10-20 22:11:22Z**; observed expiry **2026-11-21 22:11:22Z**. These are
  public lifecycle metadata, not a token ID/accessor/value.

The old credential was invalid: root-authenticated lookup returned `bad token`.
Its former expiry/revocation cause was not established. Renewal of that invalid
credential was not a recovery option.

Owner approval covered one replacement plus only this additive ACL rule:

```hcl
path "secret/data/homelab/services/pulsetrader" {
  capabilities = ["read"]
}
```

The public fragment is
[pulsetrader-read.hcl](../k8s/manifests/external-secrets/openbao/pulsetrader-read.hcl).
It is **not a complete policy**: writing it alone would remove existing consumer
permissions. Compare the live shared policy against the reviewed baseline,
append only this exact data-read path and preserve every existing rule. Existing
registry-path read access was retained; no wildcard, metadata/list, write,
renewal, credential-issuance or root permission was added to ESO.

## Verified recovery and bounded deviation

The accepted public record verified the exact policy addition, constrained token
properties, and equal credential values at all three existing locations. The
bootstrap was updated through a fresh read/merge with KV version CAS; only its
ESO field and the existing local fallback field were reconciled. No broad
bootstrap synchronization, shared password change, workload restart, or extra
token file occurred.

Store Ready/Valid was observed **22:14:29Z**. All 13 pre-existing ExternalSecret
consumers freshly reported SecretSynced **22:14:29-35Z**. PulseTrader's
`pulsetrader-paper-api`, `pulsetrader-paper-worker`, and
`pulsetrader-registry-pull` synced **22:20:59-22:21:00Z**. Sync status proves
those reconciliations, not that applications reloaded credentials or are healthy.

The Kubernetes Secret update used resourceVersion-guarded `kubectl replace`.
Kubectl also rewrote its existing last-applied annotation. The helper stopped
at the strict metadata comparison; no automatic retry/token reissue followed.
In-memory parsing confirmed the annotation matched the intended replacement
data/identity/type, but its original bytes were not retained. **Do not claim
unchanged metadata or restored original annotation bytes.** Annotation contents
can contain credentials and must never be printed or copied into evidence.

Future reviewed helper corrections use stdin raw PUT, which bypasses kubectl's
annotation rewriting, with a fresh resourceVersion and verification that only
the approved field changes. Do not use `--force`, delete/recreate, or assume
`--save-config=false` prevents updates to an existing annotation. The future
correction was not rerun as part of this recovery.

## Manual renewal responsibility

**Owner: Adam/operator. No automation has been created.** Inspect and renew
weekly, first **2026-10-27**; intervene **by 2026-11-17** before the observed
November 21 expiry. After each successful renewal, record the actual inspected
expiry and next weekly check; these initial dates do not prove later renewal.
ESO v0.10.7's static-token path reads the Kubernetes Secret; automatic renewal
must not be assumed. A periodic token still expires unless explicitly renewed.

Use the existing approved privileged OpenBao operator route, resolved through
`automation/common/SecretResolver.psm1`; hold the current ESO credential only in
memory. Do not add the root token as an ESO consumer or grant ESO extra token
ACLs. Inspect the existing credential through privileged token lookup first and
whitelist only policies/type/orphan/TTL/period/renewable/use-limit metadata.

For the same approved identity, the manual renewal API is **POST
`/v1/auth/token/renew`**, with JSON `token` and requested `increment: "768h"` held
only in process memory and privileged authentication in an in-memory header.
The periodic token's configured period governs its renewed lifetime; verify
the returned actual metadata rather than assuming the requested increment.
Never pass token values in argv, files, logs, transcripts or raw responses.
No renewal command is executed by reading this runbook, and no renewal job or
reminder is implied.

After renewal, verify self-lookup succeeds with only `eso-read-lab`, period
2764800s, renewable true, unlimited uses, no root/default policy or explicit max
TTL, and a renewed actual expiry. Verify store and fresh consumer sync status;
an unchanged credential should still match all three locations in memory.
If already invalid/expired, stop renewal: replacement needs its own exact owner
approval, scope review and narrow three-location reconciliation. Do not run a
broad env-to-OpenBao sync or resurrect the invalid old credential.

## Remaining controller/API stability gate

Recovery of authentication did not resolve a historical core-controller crash
loop: 10609 restarts, lease/resource-lock deadline failures on wknd01. The
cert-controller/webhook were ready. Core is one replica, ESO 0.10.7, leader
election enabled, CPU request/limit 50m/300m, memory 128Mi/256Mi, with no placement
constraint or health probes. A brief Ready state is not stability acceptance.

Intermittent API timeouts also occurred from the workstation, so this was not
established as a wknd01-only network fault. Root's bounded 15-minute journal
classification found 623 SQL operations taking at least one second, two lock
errors and 40 context deadlines. Slow SQL counts are not error counts. No kernel
OOM/I/O/reset errors were found; free disk/memory remained sufficient. A later
sample showed load 9.17 and zero blocked tasks; pressure and Kine endpoint
metrics were unavailable. These observations do not identify a maintenance fix.

K3s v1.28.15+k3s1 pins Kine v0.13.2. Its SQLite default already uses WAL/shared
cache/a 30-second busy timeout, and its own compaction invokes a FULL checkpoint.
Do not add manual checkpoint, vacuum, row deletion, tuning, datastore migration
or restart as a diagnostic. No such maintenance/restart was performed here.
Keep evidence collection bounded and sanitize SQL classes/durations, not SQL
arguments or object payloads. Any later maintenance requires a separate reviewed
plan and recoverable datastore/server-token backup; never copy just `state.db`
and discard the WAL or expose the protected server token.

The paper coordinator separately passed fresh pinned node pulls and 16 rollout
server dry-run checks. At that checkpoint no immutable product application
deployment had occurred. Follow PulseTrader's canonical checkpoint for later
rollout evidence; no strategy denominator, calibration, profit, stability or
manual-reading acceptance follows from ESO recovery.

## Primary implementation references

- [ESO v0.10.7 static-token handling](https://github.com/external-secrets/external-secrets/blob/v0.10.7/pkg/provider/vault/auth_token.go)
- [OpenBao v2.5.3 token API](https://github.com/openbao/openbao/blob/v2.5.3/website/content/api-docs/auth/token.mdx)
- [Kubectl annotation updates](https://github.com/kubernetes/kubectl/blob/v0.35.0/pkg/util/apply.go)
- [Kubectl raw replacement path](https://github.com/kubernetes/kubectl/blob/v0.35.0/pkg/cmd/replace/replace.go)
- [Kine v0.13.2 SQL threshold/metrics](https://github.com/k3s-io/kine/blob/v0.13.2/pkg/metrics/metrics.go)
- [Kine SQLite driver](https://github.com/k3s-io/kine/blob/v0.13.2/pkg/drivers/sqlite/sqlite.go)
- [K3s backup/restore requirements](https://docs.k3s.io/datastore/backup-restore)
