# PulseTrader service

Verified 2026-10-20. Product requirements, issue acceptance and the current
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

Documentation readbacks passed at23:55:11Z: Wiki.js page20 has the exact
published runbook content, and NetBox service3 records TCP443, existing IP84
and existing device6. No device, IP assignment or physical inventory changed.
Wiki publication used a loopback-only Kubernetes service tunnel after its
normal workstation HTTPS request failed; no TLS bypass or trust-store change.

## Verified observer rollout

Argo Synced/Healthy at `5fe46dbe029a26364e4a0cf32b1da8776400f25a`;
post-replacement verification at23:46:23Z confirmed all three expected immutable
image IDs and Ready pods on `oma01rpicls01wknd03`:

| Image repository | Deployed manifest digest |
| --- | --- |
| `192.168.1.15:5000/lab/pulsetrader-api` | `sha256:75564674afb5846b8d85bd2602dc6a017704ee541403fc95fcf8d1bbeb45a707` |
| `192.168.1.15:5000/lab/pulsetrader-ui` | `sha256:3143fb089bc1a6063733fd6012404cbed4f2365ec4f655da3a48549d4c4c6151` |
| `192.168.1.15:5000/lab/pulsetrader-worker` | `sha256:fb9b2594ef0988281e14f746a3bcbc0cc555792591fb2c8db215f339445965a1` |

Images retain tested source `e47f67a383707dca164a327ab91546ce76247440`.
Mode is `paper`, live false. This initial observer release has inference and
paper execution disabled, one worker with Recreate, and weekly reports suspended.
See the product checkpoint for any subsequent reviewed activation; this dated
snapshot does not establish future settings.

Actual public Kalshi collection, retained rules, an official finalized outcome,
same-cutoff database/API/browser agreement, owner API login/CSRF/logout,
populated consistent backup/restore and API/worker projection durability passed.
These prove their respective software/storage paths. They do not prove a real
forecast, simulated fill, fee, settlement, profitability, calibration or live readiness.
The product retains explicit missing BRTI/macro data and never substitutes spot
for official settlement. No fixture data was seeded into the Lab database.

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
