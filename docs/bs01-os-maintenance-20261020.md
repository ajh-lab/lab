# BS01 Ubuntu Maintenance - 2026-10-20

Owning issue: [lab #59](https://github.com/ajh-lab/lab/issues/59).
The owner requested OS package updates, then explicitly approved rolling
reboots after package completion. This superseded the initial no-reboot hold.

## Scope and Results

Ubuntu 24.04 package maintenance completed sequentially across all five hosts.
Reviewed installed versions matched each plan; dpkg audit and apt consistency
checks passed. No distro release, K3s, PostgreSQL major version, application
image or database schema upgrade was performed. Existing conffiles and network
identities were preserved; no autoremove or hardware firmware flashing occurred.

| Host | Packages updated | Reboot and postflight |
| --- | ---: | --- |
| bs01-wknd01 | 55 | Changed boot ID; K3s active; Longhorn mounted |
| bs01-wknd02 | 51 | Changed boot ID; K3s active; Longhorn mounted |
| bs01-wknd03 | 52 | Changed boot ID; K3s active; Longhorn mounted |
| bs01-data | 52 | Changed boot ID; PostgreSQL ready on local socket |
| bs01-gw | 52 | Changed boot ID; gateway, HAProxy and Wi-Fi active |

Total: 262 package updates. All five post-reboot checks reported no failed
systemd units, no needrestart service candidates and no reboot-required flag.
The running kernel remains `6.8.0-147-generic`; K3s remains `v1.36.3+k3s1`.
This is evidence for the reviewed package set, not a promise that future
repositories will have no newer packages or that every optional package was
upgraded.

## Recovery and Execution

Each worker saved a K3s etcd snapshot named `pre-os-updates-20261020` before
package changes. The data server saved an online custom-format PostgreSQL dump
at `/root/bs01-os-updates-20261020/droneops-before-os.dump` (16,088,020 bytes).
Its archive catalog was validated and contained table data. A restore rehearsal
was not performed for this maintenance backup; catalog validity is not proof
of tested restoration.

Root-owned per-host recovery directories `/root/bs01-os-updates-20261020`
retain reviewed preflight, prior package metadata, transaction log, atomic job
state, package postflight and before/after reboot markers. Independently
supervised systemd jobs prevented an SSH timeout from interrupting dpkg.
Credentials were resolved in memory and are not part of this record.

Workers drained one at a time using normal eviction and disruption budgets,
then rebooted and were uncordoned after host checks. Longhorn rebuilding and
replacement application readiness were allowed to finish before the next host.
No force or disruption-budget bypass was used. The data server followed the
workers; gateway was last, after verifying the dual-connected FWSLT01 recovery
path. No router or laptop reboot was performed.

Gateway direct Wi-Fi SSH returned automatically after its warm reboot. Its
supplicant is persistently enabled, gateway and HAProxy services are active,
and rack Ethernet remains preferred. This additionally verifies the startup
repair tracked by [platform #1231](https://github.com/ajh-lab/droneops-platform/issues/1231),
whose source merged through [the Wi-Fi repair PR](https://github.com/ajh-lab/droneops-platform/pull/1232).

## Final Live Acceptance

- All three cluster nodes Ready and schedulable; all ten active DroneOps Pods
  Ready; all namespace deployment/statefulset/daemonset controllers ready.
- All attached Longhorn volumes healthy after each worker recovery. The
  pre-existing detached/unknown volume is excluded from that attached-volume
  gate and was not deleted, reformatted or otherwise repaired in this task.
- Home-network DroneOps HTTPS returned 200 with CA and hostname verification.
- Anonymous protected API access returned 401; login and authenticated reads
  of component types, catalog, instances and aircraft drafts returned 200.
- A CSRF-less empty catalog request was rejected with 403 without changing
  inventory; authenticated access survived the rejection. Logout returned 200
  and subsequent protected access returned 401.

These are live OS, network, storage and read-only application observations.
Warm reboots do not prove power-loss cold boot, physical USB hot-plug, flight
failsafes or hardware/HIL acceptance. No production inventory was created.
Deployment automation and receiving-schema delivery remain separate platform
work; this maintenance does not complete either item.
