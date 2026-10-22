# PulseTrader service

At `2026-10-22T04:42:51.775282Z` (October 21, 11:42:51 PM CDT), the scoped
pipeline's UI-only release was Argo Synced/Healthy at
`4f339bf4f8abcca94be4e471c7dffaa0913608a6`, with the verified UI digest Ready
and zero UI restarts. API/worker identity and experiment settings stayed intact.
Actual served desktop checks followed at 11:43 PM CDT. Earlier checkpoints
remain dated below; this page does not establish strategy acceptance.
Product requirements, issue acceptance and the current
continuation belong to the [PulseTrader checkpoint](https://github.com/ajh-lab/PulseTrader/blob/main/docs/context/project-status.md).
This Lab page records service integration, not strategy acceptance.

## Current scoped UI release (October 21, 11:42–11:43 PM CDT)

[Selection PR #42](https://github.com/ajh-lab/PulseTrader/pull/42) merged as
`4f339bf4f8abcca94be4e471c7dffaa0913608a6`. All five applicable PR checks
passed: 2m19s from CI creation, 2m22s from PR creation; deployment-only scope
required no new image build or application suite. Exact-main
[CI39723520555](https://github.com/ajh-lab/PulseTrader/actions/runs/39723520555)
passed in 1m03s. The complete deployment checks recorded 56 passes, with all
17 installed-server dry-run resources accepted; the focused release contract
contributed 15 checks. Historical selection receipts remain preserved.

At `04:42:51.775282Z`, actual UI image was
`192.168.1.15:5000/lab/pulsetrader-ui@sha256:6740b6fcfcbf3830fc90b219bfdcd5f7b4a7c93bbf2a9f225f0dbe6120c1acf0`,
one Ready UI pod with zero restarts. API and worker UIDs, creation times, image
IDs and restart counts matched their pre-rollout values. API remains
`4a12cc883bd4217f25bbfe7cd475e5c469110bb119b7e8267c16e900579da1cf`;
worker/report remains
`5ba6c6b2ec50818b5fae456a5529523e6821e4122ef2cee9ed6d5f1fa2b0a2b2`.
All four ExternalSecrets were Ready, runtime ConfigMap/environment references
were unchanged, and the matched62 cohort/risk/report identity was preserved.
The Argo operation was still Running at the initial sample, started
`04:41:46Z`. A separate terminal receipt observed at `04:44:10Z` records
Succeeded, finished `04:43:03Z`: 77s operation time, or 4m23s from the
`04:38:40Z` merge including reconciliation/normal-refresh wait. No manual
workload apply or restart occurred
(`runtime-after-v2-ui-03.json`, `runtime-v2-comparison.json`).
Terminal evidence is `argo-v2-terminal.json`; operation time and total
merge-to-terminal time remain distinct.

At `04:43:44.004Z` (11:43:44 PM CDT), actual desktop DOM showed current62,
blank as-of, loading false and a 22-row result set. Its first page showed
11:30:15 PM CDT SKIP/unresolved, then 11:15 Wrong, 11:00 Correct, 10:45 Correct
and 10:30 Wrong, each also SKIP/0. Computed styles remained yellow
`rgb(242, 199, 119)`, red `rgb(255, 173, 182)` and green `rgb(145, 226, 200)`;
both original 1254×1254 logo assets loaded. Snapshot was
`26480e5e9d2f5d6ea65c8878bdd87b0f9f67f0843687b307df3fa87d266af2b7`
(`served-v2-desktop.json` and screenshot). This public view created no owner
acknowledgements and does not claim continuous collection, fills, profitability,
completed-week analysis or strategy/live readiness.

## Scoped pipeline delivery and retained correction history

[Pipeline issue #35](https://github.com/ajh-lab/PulseTrader/issues/35) and
[source PR #36](https://github.com/ajh-lab/PulseTrader/pull/36) introduce scoped
x86 PR validation, exact merge-tree provenance, selected native ARM production
builds on main and immutable artifact reuse during protected export. Native core
production, scoped UI/export/publication and dated GitOps/runtime checks passed.
Registry credentials remain in Lab. Measurements below are individual observed
stages, not a universal latency guarantee.

PR #36 merged as `dd9161a87b81b51576a0b10f3b09acaa2d2eb649` after its required
PR checks passed. Its first main run `39711928318` **failed** the aggregate
because native image/candidate jobs were incorrectly skipped; it produced no
accepted candidate. Corrective [PR #37](https://github.com/ajh-lab/PulseTrader/pull/37)
merged as `027e92c49594bdc0e3b04b40d53ee1b3f9263cdc`. Its main run
`39713316542` started native production. Its images job naturally **failed** at
`2026-10-22T03:03:34Z` after reaching candidate creation; the workflow was then
**cancelled**, terminal at `03:03:47Z`. Read-only inspection independently found
shallow Git history without the required merge parents. That is consistent with
the first candidate topology guard, but the CLI sanitizes the underlying
exception, so the precise exception was not logged. Upload was skipped and no
artifact was credited (`main-027-image-terminal-cause.json`). Job failure and
workflow cancellation are both retained rather than classifying this as only
an interrupted build.
[PR #38](https://github.com/ajh-lab/PulseTrader/pull/38) merged as
`379890a05609bf1c091e602f378f8691f5f348d3` after all seven applicable PR checks
passed, adding complete history and early real provenance preflight. Main run
`39715786409` passed that preflight and native API/worker imports, then failed
candidate export with a sanitized BLOCKED message at `2026-10-22T03:24:14Z`;
the images job completed failed at `03:24:23Z`, with upload skipped and zero
artifacts. Actual accepted PR proof also passed a separate read-only shape check.
This did not establish a successful native candidate.

A real 2,253-byte Docker29 format fixture captured at `03:34:07Z` demonstrated
that inspected image ID identifies an OCI index while the archive's configuration
has a different digest. The former config-ID equality guard rejects that valid
shape. This is a concrete format incompatibility consistent with the production
failure; the production CLI did not expose its exact underlying exception.
[PR #39](https://github.com/ajh-lab/PulseTrader/pull/39), head `631d919`, adds
strict inspected-index → unique native manifest → actual configuration/layer
binding with digest/size/type checks, safe canonical archive paths, bounded
traversal and the legacy config-ID path retained. Candidate-v1 still records
the actual config digest; no identity check or attestation was disabled.
The real format fixture and 66 focused candidate/identity tests passed local
and independent review. At `03:35:09Z`, Podman5.8.4 loaded that same fixture
and passed exact publisher config-ID/platform/revision checks without ARM
execution or registry push; owned fixture resources were removed. These are
software/format interoperability proofs, not application or native production
acceptance by themselves. PR39 subsequently merged as
`379b91f3f41eea4bdd527d917e76525ef633ee58`. Its actual main
[CI39719291961](https://github.com/ajh-lab/PulseTrader/actions/runs/39719291961)
completed **successfully** at `2026-10-22T04:14:00Z` (October 21, 11:14 PM CDT).
All three selected native ARM runtime images passed their applicable import/HTTP
smokes, candidate creation passed, a separate uploaded-candidate job verified the
immutable artifact, and the required aggregate passed. Original candidate
artifact `12400784228` has 190,963,175 bytes and SHA-256
`39a48d34ac40224119b180416b631400fa1aebe92aba806a815a76565d295922`.
Its recorded expiry is `2026-10-23T04:10:19Z`; later consumption must freshly
verify availability, digest and producer binding.

This one recorded main run took 20m50s from creation to workflow completion.
Production build/smoke/export took 15m47s, upload 57s and post-job cache save
2m03s (`main-379b-summary.json`); these distinct intervals do not establish a
universal delivery time or isolate a speedup cause. This was candidate production
and verification only: no registry publication or runtime rollout occurred.
The real desktop-only PR #40 subsequently merged as source B
`d49991d67c881dd4439cc66101669286181d5b10`. Its actual PR checks passed 63 UI
unit cases, seven desktop browser cases and build; PR-created-to-green was
2m13s with a 1m11s UI job. Backend/deployment lanes and PR images were
deliberately skipped while classification/security/provenance/aggregate passed.
Its UI-only native main
`39721710614` passed at `2026-10-22T04:24:56Z`, 5m43s from run creation, with
independent uploaded-candidate verification. Artifact `12401945949` is
31,363,743 bytes, SHA-256
`1b455343f6f3edec516139008b1623741a0059bf51a034409dfceb4cdb5a0adc`,
recorded expiry `2026-10-23T04:23:18Z`. This scoped candidate contains only UI.
Docs/branding/receipts PR #41 then merged approved tip C
`4b9b984e122e96ab7808e5cfda140e10d9e9a1e7` at `04:29:30Z` after all four
applicable PR checks passed (1m05s PR-created-to-green). The subsequent protected
export independently required successful C-main checks, B producer/artifact,
ancestry and unchanged application/policy proofs; original candidate source and
OCI labels remained B.

Protected [export39722805110](https://github.com/ajh-lab/PulseTrader/actions/runs/39722805110)
approved exact C and explicitly reused source B. It passed at
`2026-10-22T04:31:42Z`, 45s after creation; its verify/reuse step took 10s,
without application test repetition or image rebuild. Export artifact
`12401548252` is 31,364,340 bytes, SHA-256
`684ea809acb405516fbc461730227c6fe2888e0e6a9c991f35786dfee17b7072`.
Independent download verified exact original candidate bytes and approval proof.
Lab-local publication from `04:32:48.603Z` to `04:32:55.716Z` took 7.113s,
publishing only UI. Fresh no-redirect registry HEAD at `04:33:02.158556Z`
returned HTTP200 and exact selected digest
`sha256:6740b6fcfcbf3830fc90b219bfdcd5f7b4a7c93bbf2a9f225f0dbe6120c1acf0`.
This is published-candidate evidence, not an observed replacement UI pod.

[UI-only selection PR #42](https://github.com/ajh-lab/PulseTrader/pull/42)
changes exactly one runtime image line. Fifteen deployment contracts passed
after an observed old-selection RED; all 17 installed-server dry-run resources
passed. Reversing that UI reference restores the accepted previous runtime
bytes. Eight committed public JSON receipts match their canonical LF index.
The later actual merge/Argo/new UI pod and served checks are recorded above;
API/worker/report, ConfigMaps, cohort pair, risk caps and weekly schedule retain
their prior bytes.
No worker/API restart or experiment change follows from the wide core candidate.

Desktop is the primary browser acceptance target; phone checks are incidental.
Earlier dated phone evidence below remains historical evidence rather than a
future release gate. The desktop-test phase produced and published a UI-only
candidate; its reviewed GitOps selection preserved API/worker/report images,
the runtime ConfigMap, 62-cohort pair, paper caps and live-disabled state.
Source, CI, export, publication, selection and dated runtime evidence remain
separate. See the product
[CI release contract](https://github.com/ajh-lab/PulseTrader/blob/main/docs/ci-release.md).

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

## Accepted UI-only release and dated served evidence

[Release PR #34](https://github.com/ajh-lab/PulseTrader/pull/34) merged at
`2026-10-22T01:35:41Z` as `ed2b3e901ea59706ed3ebffa335f8b1ea6a153bb`.
At `01:38:32.198384Z` (October 21, 8:38:32 PM CDT), Argo was Synced/Healthy
at that revision and actual UI image was
`192.168.1.15:5000/lab/pulsetrader-ui@sha256:a97bd75e380b9cf82e38fda6df738534d89fe1836e10769939bd63882ef09338`.
Public release receipts are retained in
[`20261021-accuracy-colors`](https://github.com/ajh-lab/PulseTrader/tree/ed2b3e901ea59706ed3ebffa335f8b1ea6a153bb/deploy/releases/20261021-accuracy-colors).
Before/after observations at `01:35:27Z` / `01:38:32Z` show API and worker pod
UIDs, restart counts and images unchanged. API remains `4a12cc…`, worker/report
`5ba6c6…`, runtime ConfigMap `pulsetrader-paper-runtime-4b8a9fb46f392166`,
matched62 primary/baseline, paper caps and live-disabled state unchanged
(`runtime-after-ui.json`, `runtime-ui-comparison.json`).

The selected UI contains PR #33's signed accuracy-delta colors, readable feature
units and explicit historical-cohort/current-cohort navigation. Formatting is
presentation-only: complete original audit values remain available, proposed
contracts are distinct from fills and untrusted rationale is escaped. Source
formatting tests and actual frozen-browser audit parity are separately recorded
below. At `01:59:55.114Z` (8:59:55 PM CDT), actual served historical
snapshot showed `+0.5 pp` in green `rgb(145, 226, 200)` with an accessible
increase label. At `02:01:48.171Z` (9:01:48 PM CDT), another served historical
snapshot showed `−0.7 pp` in red `rgb(255, 173, 182)` with a decrease label.
Both retained the separate historical-snapshot and historical-cohort notices
and explicit View current cohort control (`served-positive-delta.json`,
`served-negative-delta.json`). These are dated observations, not current
population accuracy claims.

Actual served raw-audit parity compared the same first 62-primary forecast and
as-of `2026-10-21T23:16:00.718682Z`: before-format capture at `23:23:43.336Z`
and after-format capture at `2026-10-22T01:53:19.853Z` both contained 37,974
characters with SHA-256
`87f8e70383ea0f0a3b1f6c16d39388daf84695c1b7a25e9046b5dc333cbd2630`;
the latter records exact original equality. Its initial `features: []` was a
selector limitation, not evidence that feature data disappeared. A separate
populated served capture at `02:04:29.490Z` (9:04:29 PM CDT) verified initially
collapsed audit and readable cards: spot `$84,382.69 USD`, BRTI `$84,396.52 USD`,
YES bid/ask `$0.42`/`$0.43 USD/contract`, return `-0.0134%`, 24-hour volume
`7,601.9261 BTC` and imbalance `-24.58% (YES − NO) / (YES + NO)`. Macro remained
Unavailable with its missing-source reason, and provenance times remained
Chicago/CDT. Receipts are `served-frozen-audit-before-format.json`,
`served-frozen-audit-after-format.json` and
`served-readable-features-after-format.json` under the BRTI release scratch.

At `2026-10-22T03:06:17.552Z` (October 21, 10:06:17 PM CDT), the served current
62-primary explorer displayed the 10:00:15 PM CDT forecast as SKIP/unresolved,
then descending 9:45/9:30/9:15/9:00 entries. Computed styles were yellow
Unresolved/tied `rgb(242, 199, 119)`, red Wrong `rgb(255, 173, 182)` and green
Correct `rgb(145, 226, 200)` (`served-current-2206.json`). At `03:07:04.421Z`,
the same frozen snapshot `e3c3611b…` (10:05:59 PM CDT) showed newest rolling
resolved row 9:45:15 PM CDT, n=15, win rate 40.0%, followed by earlier rows
(`served-rolling-2207.json`). The unresolved 10 PM forecast did not yet belong
in resolved rolling accuracy. These samples establish recent data and Chicago
display/correctness colors; they do not establish continuous collection,
profitability, a natural fill, completed-week analysis or strategy acceptance.

## Historical BRTI/UI checkpoint (October 21, 23:00 UTC)

[BRTI source PR #30](https://github.com/ajh-lab/PulseTrader/pull/30) and
[UI/API source PR #31](https://github.com/ajh-lab/PulseTrader/pull/31) are merged.
Combined source revision `c11fb06b991937ff5a3ce968590a91b513277187` passed
[exact-main native ARM CI39680009179](https://github.com/ajh-lab/PulseTrader/actions/runs/39680009179)
at `2026-10-21T21:51:02Z` (4:51:02 PM CDT). This is accepted source and CI
evidence; the separately observed runtime and browser checks below establish
the deployment checkpoint without implying strategy acceptance.

Published release candidates are recorded in
[`deploy/releases/20261021-brti-ui`](https://github.com/ajh-lab/PulseTrader/tree/beef70a704fd0d77f0b0e37adeef54c451a973ac/deploy/releases/20261021-brti-ui).
All three c11-source images were published to the Lab registry; authenticated
HEAD checks at `2026-10-21T22:09:51Z` returned HTTP200 with the exact selected
digests. The same digests were observed on Ready pods at 23:00:08Z:

| Component | Observed deployed digest |
| --- | --- |
| API (`192.168.1.15:5000/lab/pulsetrader-api`) | `sha256:4a12cc883bd4217f25bbfe7cd475e5c469110bb119b7e8267c16e900579da1cf` |
| UI (`192.168.1.15:5000/lab/pulsetrader-ui`) | `sha256:986736cc722dc16dc09437e1cdc3856b60be2045265cbdb694e56a3797c8e330` |
| Worker (report template shares image; `192.168.1.15:5000/lab/pulsetrader-worker`) | `sha256:5ba6c6b2ec50818b5fae456a5529523e6821e4122ef2cee9ed6d5f1fa2b0a2b2` |

Historical release [PR #32](https://github.com/ajh-lab/PulseTrader/pull/32) was deployed at
revision `beef70a704fd0d77f0b0e37adeef54c451a973ac`. At 23:00:08Z, Argo was
Synced/Healthy at that revision; API and UI on wknd01 and the single worker on
wknd02 were Ready with zero restarts. Runtime ConfigMap is
`pulsetrader-paper-runtime-4b8a9fb46f392166`. These are point-in-time observations,
not continuous-health evidence. The completed worker cycle at 23:00:07.304884Z
was 1.863209 seconds old against API envelope time, without applying a client
clock offset (`runtime-first.json`, `worker-first.json` in the local release
evidence).

At 23:08:13Z, all three current pods remained Ready with zero restarts. The
three retained NodeNotReady warning-event records belonged exclusively to
previous pods, with cumulative counts 7/3/7; none identified a current pod.
Sampled API/UI/worker use was 94/4/56Mi and 4/1/210m CPU respectively
(`readiness-after-initial.json`). This neither erases the old warnings nor
establishes uninterrupted readiness or long-term capacity.

The deployed selection uses feature version `cutoff-brti-v2` and the combined
source revision above: primary `local-62a04307fb214d52-memory`, paired baseline
`local-62a04307fb214d52-none`. Preserve the earlier
`local-903db5a75addb49a-memory` / `local-903db5a75addb49a-none` histories and
accounts separately; do not pool cohorts, delete gaps or backfill missed trades.
The new baseline must remain unfunded. Existing paper policy remains enabled
with live orders disabled, $10/order, $25 exposure and $10 daily gross settled
loss caps. Weekly reporting remains Monday 00:30 UTC, with the first completed
week due October 26 at 00:30 UTC (October 25 at 7:30 PM CDT).

The new input is the official authenticated Kalshi BRTI feed. The worker must
explicitly enable `KALSHI_BRTI_ENABLED=true` for the new feature version; disabled
legacy rendering remains available. Missing, disconnected, stale, invalid or
future observations remain explicit and fail eligibility rather than becoming
invented values. Source, receipt, ingestion and cutoff time guards remain in
force. Instantaneous BRTI is an input, not the contract's averaged settlement
value; only official Kalshi outcomes resolve forecasts. See the
[product BRTI runbook](https://github.com/ajh-lab/PulseTrader/blob/main/docs/brti-feed.md).

The served UI provides Chicago CDT/CST timestamps, green Correct/red
Wrong/yellow Unresolved or tied results, and five-row pagination for long tables.
Rolling history is ordered by actual timestamp newest first before pagination;
summary metrics and charts retain their full selected population. Current views
without an explicit cohort use the status API's authoritative paper primary;
explicit cohort and historical as-of selections remain intact. Decision detail
shows escaped rationale, feature provenance and missing reasons, supplied memory,
official correctness, proposed contracts separately from actual fills/fees, and
collapsed complete audit JSON. Selected-memory Brier is distinguished from
population Brier; unresolved is not a loss and SKIP is not a trade. Exact owner
acknowledgement identity and notes remain available. Forecast accuracy change
compares the same selected population before the latest officially known resolved
observation, with signed percentage points and explicit unavailable/tie handling.
The owner-supplied logo was loaded at its original 1254-square dimensions and
displayed without distortion in the header and sign-in area. Actual browser
checks at 23:07:18Z covered 1440px desktop and 390px phone views, five-row
Next/Previous paging and keyboard Next, authoritative current-cohort selection,
readable detail and collapsed/expanded complete audit data without page
overflow. The old-cohort rolling table's newest displayed resolved row was
5:30:15 PM CDT, followed by descending timestamps; its full selected history
had 82 rows. Correct/Wrong/Unresolved colors passed actual computed-style
checks (`served-browser-initial.json`). The accuracy change's signed +0.5 pp
text and accessible label were served, but its color was muted gray: separate
[PR #33](https://github.com/ajh-lab/PulseTrader/pull/33), final source head
`46234091a443ddfb35adeaf8ce0c9254a73685ec`, fixes CSS specificity, formats
feature values with readable units while preserving original audit values, and
adds a historical-cohort notice with an explicit View current cohort button.
Independent review, 63 UI tests, 13 browser fixtures and the build passed for
that head. Actual served green/red accuracy-delta colors and selected-image
deployment were pending at this 23:07 checkpoint; the later accepted PR #34
observations above supersede that pending stage.

At 23:31:56Z (6:31 PM CDT), public API evidence showed three new BRTI primary
forecasts at 6:00, 6:15 and 6:30 PM CDT; the retained old `903` primary's newest
forecast was 5:45 PM CDT. These are separate configurations and histories,
not a reason to restart the worker. At 6:32 PM CDT, an actual fresh root-URL
phone browser selected current `local-62a04307fb214d52-memory` automatically;
its rolling table showed resolved rows through 6:15 PM CDT. The 6:30 forecast
was still unresolved at that sample and properly absent from resolved rolling
accuracy until its official outcome. Read-only verification of that pair
confirmed cutoff-safe BRTI $84,221.45, identical features, both SKIP/p(YES) 0.365,
one prior resolved example in the primary and zero in the baseline; this proves
feedback lineage, not memory benefit. The worker's actual 23:30 sample was fresh
by API clock (2.3083 seconds), despite the receipt filename's `1834` suffix.
See local receipts `latest-cohorts-after-1830.json`, `worker-fresh-1834.json`,
`brti-current-1830-pair.json` and `served-current-default-1832.json`.

An explicit old cohort or historical as-of URL is intentionally preserved.
The owner's current Edge filter has not been observed, so these checks do not
identify that browser's selection. To view new forecasts in the currently
served UI, select the new BRTI primary above, clear As-of snapshot and Apply
filters, or open the root URL without cohort/as-of parameters. The later PR34
served View current cohort control performs that explicit switch and clears the
historical snapshot; Return to current alone clears as-of while keeping the
selected cohort. No worker restart is needed for a view change.

The observed credential boundary uses a dedicated ExternalSecret
`pulsetrader-kalshi-benchmark`, reading only
`secret/homelab/services/pulsetrader-kalshi-benchmark` fields `api_key_id` and
`private_key_pem`. Only the non-root worker mounts the projected files, read-only
at `/var/run/secrets/pulsetrader-brti`, with effective mode `0440`. File pointers
are `KALSHI_BRTI_API_KEY_ID_FILE=/var/run/secrets/pulsetrader-brti/api_key_id` and
`KALSHI_BRTI_PRIVATE_KEY_FILE=/var/run/secrets/pulsetrader-brti/private_key_pem`.
API, UI and report containers receive neither benchmark credentials nor the
collector. The minimum dedicated-path read append to existing policy
`eso-read-lab` has been applied and exactly read back, preserving every existing
entry and the token (`eso-policy-applied.json` in the release receipts records
`exact_single_read_path_append=true`, `token_rotation=false`). This applied
policy receipt is separate from runtime acceptance: at 23:00:08Z, all four
product ExternalSecrets were Ready, and actual worker and deployment-template
checks confirmed the worker-only non-root, read-only `0440` mount boundary,
exact fields and file pointers. API/UI actual pods and the report template had
no benchmark access. No Secret values were read for that public-resource check.
Existing service and registry secret authorities, ingress and approved TLS
identity remain unchanged by the source contract.

At 23:00:19Z, read-only runtime-role SQL verified separate old/new primary
accounts, each with exactly one simulated $100 opening and cash $100, zero open
cost basis and realized net P&L. Both exact baseline cohorts had zero ledger
events and no funding (`ledger-after.json`). Old-cohort frozen API detail and
legacy analytics at as-of 20:59:35.091546Z matched their preflight hashes and
envelopes; only the additive accuracy-change field was excluded from the
analytics comparison (`history-after.json`). Normal-TLS owner API login,
scoped secure cookie, CSRF/origin rejection, logout and replay revocation passed
at 23:00:37Z with zero owner reviews submitted (`owner-auth-after.json`). This
API authentication check does not establish a new authenticated-browser login.

The first natural 6:00 PM CDT pair used fixed cutoff 23:00:15Z. Both arms
returned SKIP, p(YES) 0.425 and proposed size 0; each supplied zero memory items
at this initial new-cohort checkpoint. Their common official BRTI input was
$84,396.52, with original source time 23:00:12Z, receipt 23:00:12.081235Z,
ingestion 23:00:13.200042Z and recording 23:00:13.200615Z, all before cutoff.
Read-only SQL verified exact input/request/provider/configuration correspondence
and recursive known times; the same-as-of public API matched both records
(`brti-pair-initial.json`, `brti-api-initial.json`). At as-of 23:00:47.162434Z,
official outcome association was **PENDING**, not failed, before the 23:15Z
(6:15 PM CDT) window close. That initial unresolved snapshot remains historical.
SKIP is a valid advisory, not proof of a fill or a blocked execution path, and
no trade was forced.

At as-of 23:16:00.718682Z (6:16 PM CDT), the read-only SQL verifier completed
20 queries and confirmed both exact official outcomes as NO, published at
23:15:09.050147Z. Baseline ingestion/recording was 23:15:12.367905Z /
23:15:12.368265Z; primary ingestion/recording was 23:15:12.473197Z /
23:15:12.473566Z. The source/request/configuration hashes and cutoff-safe BRTI
input remained identical to the initial pair. Official Kalshi source association
passed in SQL, and the public API matched both exact outcomes and original
forecasts at that same as-of under snapshot
`56e81f1a40f10a4ea34baae1175179cfb0af86ab5e62baaa7cd7d66adb300e17`
(`brti-official-outcome-01.json`, `brti-api-official-outcome-01.json`). Both
directional forecasts were correct; both actions remained SKIP with no implied
fill or profit. This establishes the first natural paired official-resolution
gate without rewriting the earlier pending snapshot.

The 7:00 PM CDT window is a separate operational gap, not another SKIP. At
fixed cutoff `2026-10-22T00:00:15Z`, both arms were scheduled and eligible.
The baseline claimed its inference attempt at 00:00:24.275118Z and recorded
`InvalidDecision` at 00:00:41.948910Z. The primary's current-BRTI-health guard
recorded a missed forecast at 00:00:44.585600Z before any primary attempt;
neither arm produced a forecast (`brti-1900-gap-narrow.json`, as-of
00:09:12.377407Z). Available persisted BRTI at cutoff and at the later receipt
does not establish live feed health at the primary guard's exact check; the
detailed cause remains unknown. This differs from the four valid prior SKIP
forecasts, and fresh completed worker cycles do not prove successful inference.
Coverage `failed=0` counts window statuses, not operational inference failures.
No uninterrupted or error-free inference is claimed. No restart, retry,
backfill, clock/cohort change or forced trade was performed for this diagnosis.
At 7:16:51 PM CDT, a fresh public API snapshot showed the next natural primary
forecast at 7:15 PM (SKIP, p(YES) 0.535, unresolved; five primary forecasts total),
preserving the 7 PM gap without proving its baseline, outcome or continuous
health (`latest-cohorts-1917.json`).

The later PR #34 UI selection and dated served colors are recorded above.
The scoped pipeline and subsequent UI-only publication were pending at that
historical gap checkpoint; the later accepted delivery is recorded above.
This checkpoint does not establish memory benefit,
filled execution, profitability or the strategy-readiness gates below.
Wiki.js/NetBox readbacks above remain dated historical evidence; this service
runbook update has not been published to either service.

## Historical verified paper rollout (October 21, 04:51–05:02 UTC)

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
