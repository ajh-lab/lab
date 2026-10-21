# PulseTrader service

Paper-runtime checkpoint verified 2026-10-21 UTC. Product requirements, issue acceptance and the current
continuation belong to the [PulseTrader checkpoint](https://github.com/ajh-lab/PulseTrader/blob/main/docs/context/project-status.md).
This Lab page records service integration, not strategy acceptance.

## Access and ownership

- UI and same-origin API: https://pulsetrader.192.168.1.80.sslip.io/
- Canonical private repository: https://github.com/ajh-lab/PulseTrader
- Namespace `pulsetrader`; Argo Application `argocd/pulsetrader`, canonical
  repository, branch `main`, path `deploy/k8s`.
- Separate API, UI and outbound worker Deployments. API Service port8080,
  UI Service port80; the worker has no Service. Traefik HTTPS ingress routes
  to the UI, which proxies `/api` to the API. Browsers do not access PostgreSQL,
  model providers or exchange execution.
- NetBox models the shared ingress endpoint at `192.168.1.80:443/tcp` against
  the existing control-plane device/IP. That association does not assert that
  all three application pods run on the control plane.
- Wiki.js runbook target: `/en/services/pulsetrader`.

Historical documentation readbacks passed 2026-10-20 at23:55:11Z: Wiki.js page20 had the exact
then-published observer runbook content, and NetBox service3 records TCP443, existing IP84
and existing device6. No device, IP assignment or physical inventory changed.
Wiki publication used a loopback-only Kubernetes service tunnel after its
normal workstation HTTPS request failed; no TLS bypass or trust-store change.
Dated documentation verification at `2026-10-21T05:08:18Z`: Wiki.js page20
(`services/pulsetrader`) exactly matched the accepted Lab PR #66 service content.
The initial write response was uncertain; a fresh read confirmed success without
a blind rewrite. Access used the existing loopback-only Kubernetes service
tunnel, with no TLS bypass or trust change. Read-only NetBox service3 verification
matched TCP443, ingress IP84 and device6; no inventory or NetBox write occurred.
This records that source/readback checkpoint, not an assertion that every later
Git revision is already published externally. Inventory and ingress association
are unchanged.

## Verified active paper rollout

[Performance release PR #21](https://github.com/ajh-lab/PulseTrader/pull/21)
merged at `2026-10-21T04:48:12Z` as
`26b1c594fb9d1336ba5c350b16c82c44fe4336f3`, after required
[PR CI39543515671](https://github.com/ajh-lab/PulseTrader/actions/runs/39543515671)
passed at 04:47:09Z (26m23s). Separate
[main CI39546030242](https://github.com/ajh-lab/PulseTrader/actions/runs/39546030242)
passed at 05:02:53Z on that exact revision (14m36s), including full validation
and browser checks. Actual 04:51:47Z
verification showed Argo Synced/Healthy at that accepted revision. API
`pulsetrader-api-6794685d85-p55rh` and worker
`pulsetrader-worker-78df7cb8fb-blddp` were Ready/zero restarts on wknd02;
the retained UI pod remains on wknd03.

| Image repository | Deployed manifest digest |
| --- | --- |
| `192.168.1.15:5000/lab/pulsetrader-api` | `sha256:f9c78ede779fe0001bf71731fc24cbace8fe945656ef1eee1a7f0e6bdfc1502d` |
| `192.168.1.15:5000/lab/pulsetrader-ui` | `sha256:3143fb089bc1a6063733fd6012404cbed4f2365ec4f655da3a48549d4c4c6151` |
| `192.168.1.15:5000/lab/pulsetrader-worker` | `sha256:d54b7e73173edf1f01116d6adf84ad3d89fb74fe2bbe03fd35a4048640e2ed8a` |

API/worker/report OCI source is `2a02e0436fb248c9b40279372c592497b2c64c8c`;
UI retains `e47f67a383707dca164a327ab91546ce76247440`. Mode is paper/live false,
inference/execution enabled, one worker/Recreate. A completed cycle after the
new worker's creation confirmed primary `local-903db5a75addb49a-memory`, its
paired no-memory cohort and unchanged $10/order/$25 exposure/$10 daily-loss caps.
Frozen model/prompt/feature/risk identity remains distinct from build provenance.

Weekly reports are enabled Monday 00:30 UTC, concurrency Forbid. First eligible
run is **2026-10-26T00:30Z** for the completed October 19–26 week; actual durable
numeric report/hash, local narrative or pending reason and report durability
remain future verification. No incomplete-week report or immediate backfill is
required.

Actual collection, official outcomes, cutoff-safe nonempty primary versus empty
baseline memory, normal HTTPS, owner API/browser authentication and populated
restore/replacement durability have separate accepted evidence. At frozen
`2026-10-21T02:49:00Z`, store/API/public browser agree on five primary forecasts,
four resolved/one unresolved, all SKIP, Brier 0.257625 (UI 0.25763), cash $100/net $0.
No simulated fill/fee, filled-settlement recovery, memory benefit or strategy
readiness is inferred. Earlier owner-entered browser sign-in passed with zero
agent acknowledgements; later expiry is normal, not perpetual-login evidence.

After the new API/worker rollout, the same eight-read/four-concurrent probe with
unchanged 15-second request deadlines passed in 0.735s with exact frozen hashes.
Settled actual Edge rendered that same 02:49 snapshot with counts 5/4,
Brier 0.25763/cash $100/net $0. Normal TLS served the exact approved leaf; fresh 04:49
owner API login/CSRF/logout/revocation passed, zero acknowledgements. This does
not claim a new owner reading or new authenticated-browser login.

Old failed concurrent/readiness evidence is retained. API/worker placement
changed wknd03→wknd02, so timing is an observed deployment comparison, not a
code-only causal claim. One new-worker probe-path sample measured import 2.239s
and round-trip 3.922s within the existing five-second probe; it does not prove
continuous health or fourteen-day capacity.

The first natural 05:00 pair from the new performance worker is now verified:
both SKIP with p_yes 0.355; primary supplied eight prior resolved examples,
no-memory baseline zero. Active current contract `KXBTC15M-26OCT210115-15`
was recorded at 05:00:13.965615Z before fixed cutoff 05:00:15Z; recursive
recorded/known-time source and memory lineage passed. Frozen
`2026-10-21T05:01:00Z` SQL/API reconciliation matches snapshot
`fb60dbbaa5c621b717438f873168c4d595e14e8016dd61e7bea2c58d7515b1e1`:
13 primary forecasts, 12 resolved/one unresolved, all 13 SKIP,
Brier 0.2326083333, cash $100/net $0, zero filled positions. Settled actual Edge
at that same 05:01 frozen snapshot matched full fb60 hash, counts 13/12/1,
all SKIP, cash $100/net $0 and rounded Brier 0.23261. The earlier 02:49 browser baseline
remains at its original cutoff. Neither capture proves population calibration,
memory benefit or filled execution. SKIP is valid evidence; never force an order.

Actual 05:02 sampling found both new pods Ready/zero restarts. The API had one
startup-probe connection-refused event at 04:49:24Z (count 1), no readiness/liveness
warnings; the new worker had zero warnings. This is startup-event classification,
not a readiness incident or continuous-health guarantee. Resources at that sample
were API 64Mi/5m CPU, worker 52Mi/74m and UI 4Mi/1m. ESO's sixteen consumers were
Ready, including all three product ExternalSecrets. Point-in-time readiness and
resource observations do not establish uninterrupted operation or 14-day capacity.
Explicit missing BRTI/macro data remain visible; spot is not official settlement.
No production fixtures were seeded.

[Bounded-history source PR #20](https://github.com/ajh-lab/PulseTrader/pull/20)
and exact-main CI39536710367 passed (03:33:15Z, 26m58s). Approved
[export39539284470](https://github.com/ajh-lab/PulseTrader/actions/runs/39539284470)
passed 04:03:24Z; artifact/revision/checksums, inside-Lab publication, registry
digests and inert pulls passed before promotion. Local/disposable profiles and
sampled runtime results do not prove universal deadlines or fourteen-day
capacity. The dated Wiki.js/NetBox verification above is separate from product
and strategy acceptance; inventory is unchanged.

## Credentials and TLS

OpenBao `secret/homelab/services/pulsetrader` fields are `database_url`,
`migrator_database_url`, `owner_password`, `session_secret`, `llm_api_key`.
Dedicated PostgreSQL database `pulsetrader` uses separate constrained runtime
and migration roles on `lab-pgsql01` (`192.168.1.216`). Runtime is append-only;
never substitute shared `lab_admin`. Credentials stay in OpenBao/ESO.

Scoped ExternalSecrets are `pulsetrader-paper-api`, `pulsetrader-paper-worker`
and `pulsetrader-registry-pull`; registry authority is
`secret/homelab/registry/lab-registry01`. No registry credential is sent to GitHub.
See [ESO maintenance](openbao-eso-maintenance.md) for manual token renewal:
Adam/operator first weekly checkOct27, intervene byNov17 before currentNov21 expiry.

Certificate `pulsetrader-tls` uses existing `ClusterIssuer/lab-selfsigned`,
sole hostname `pulsetrader.192.168.1.80.sslip.io`, valid through2027-01-18T21:51:04Z.
Normal Windows HTTPS verified the exact owner-approved public leaf SHA256
`64C82B1E562D12852DA47CFAAC4621D400C2DB5D2A1AFB555FFBC1FBB6EEBAEC`.
Its approved trust is confined to Windows CurrentUser Root. Future renewal
requires review of the new identity; no trust distribution is automatic.

## Verification and recovery

Use the main Lab kubeconfig explicitly:

```powershell
kubectl --kubeconfig .kubeconfig-192.168.1.80.yaml --request-timeout=15s -n argocd get application pulsetrader
kubectl --kubeconfig .kubeconfig-192.168.1.80.yaml --request-timeout=15s -n pulsetrader get deploy,pods,svc,ingress,externalsecrets
Invoke-RestMethod https://pulsetrader.192.168.1.80.sslip.io/api/v1/status
```

Do not bypass TLS validation, seed production, force a paper fill or acknowledge
wrong predictions for the owner. Keep Namespace, ServiceAccount/configs,
ExternalSecrets and target Secrets, TLS Certificate/Secret, evidence and ledgers
when rolling back workload settings. Do not restore a database over the active
experiment or revert the whole watched directory to the old bootstrap.
Follow the product's backup and rollback evidence. Shared API/ESO lease instability
is separate from product acceptance; no infrastructure maintenance is authorized
by this runbook.

Weekly analysis requires a completed UTC week; the first current cohort week
cannot complete before2026-10-26. Numeric analysis precedes local narrative.
500 unique resolved strategy forecasts, two stable weeks, calibration assessment,
positive after-cost paper results, 30 owner-read wrong cases and a subsequent
explicit live authorization remain independent gates. No readiness result enables live.
