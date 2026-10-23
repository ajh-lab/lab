# ESXi SSA Diagnostics - 2026-10-23

Owning issue: [lab #70](https://github.com/ajh-lab/lab/issues/70).

## Authorization and Package

Adam authorized installing SSA for read-only cache diagnostics, accepted the HPE
download license, and separately approved graceful shutdown of the five running
VMs, an ESXi reboot, and restoration of their services. This does not authorize
RAID/cache policy changes, hardware replacement, firmware updates, password
changes, or clearing hardware logs.

Target: `lab-vm-host` / `OMAESXMGT01`, `192.168.1.49`, HPE ProLiant DL360p Gen8,
ESXi 6.7 Update 2 build 13006603. Existing SSH identity was verified before
credentials from OpenBao were sent.

The [official HPE 2019.03.01 ESXi 6.7 utility package](https://support.hpe.com/connect/s/softwaredetails?collectionId=MTX-53bb40aec8a14ed0&softwareId=MTX_5dfd7416d42447eda62b8f0433)
was downloaded and its published SHA-256 verified. Only
`ssacli-3.40.3.0-6.7.0.vib` was extracted from the nested utilities bundle.

| Artifact | SHA-256 |
| --- | --- |
| `cp037190.zip` | `7ad45d929ed944cc42c3d0fe39283292719dfaebd5717fafcd36ad909e330cd3` |
| SSA VIB | `36ef31a897c571608a3f93b15490379cf06a9e461a66b9d7519a2cdc69f64b41` |

The transferred VIB hash matched. Native ESXi dry-run checks passed without
force, signature bypass, dependency override, or acceptance-level reduction.
Only `HPE_bootbank_ssacli_3.40.3.0-6.7.0.7535516` was installed; no VIB was
removed. ESXi required a reboot for activation.

## Maintenance Evidence

Before shutdown, all five guest preflight checks passed and the GitHub runner
was idle. A new VM power/service baseline was saved separately from the October
21 record. Recovery credentials were retained in process memory before taking
OpenBao offline; no secret values were written to the evidence files.

All five running VMs accepted guest-OS shutdown and reached powered off without
forced power operations. The four already stopped VMs were left stopped.

ESXi reboot was verified from its fresh uptime. The first SSH connection arrived
before its command services were ready; the initial recovery check stopped, and
a retry restored the VMs without another reboot or reset. Maintenance mode is
off, all five formerly running VMs are on, and the four formerly stopped VMs
remain off. Both datastores are mounted.

Post-reboot verification:

- PostgreSQL 16 is running and accepts connections through `pg_isready`.
- OpenBao is initialized, unsealed through the existing recovery key, and its
  service is active. No token policy or credential was changed.
- Registry Docker container is running; an authenticated `/v2/` request returned
  HTTP 200 using the existing OpenBao registry record.
- All three static GitHub runner services and the release-catalog service are
  active. GitHub's organization runner API reports all three runners online.
  Docker on the runner became active as startup completed.
- Prometheus readiness returned HTTP 200 and its runtime API reports a new
  October 23 startup time. Its early HTTP 503 cleared after startup. Its existing
  SSH trust mismatch was not bypassed; this is API readiness evidence, not an
  SSH inspection of that VM.
- No failed systemd units were reported on the four SSH-verified guests. The
  previously active `fwupd`/`upower` services were not unnecessarily started.
- CIM is running, HPONCFG still reads iLO 4 firmware 2.77, and DroneOps home-LAN
  HTTPS returned HTTP 200 with ordinary certificate validation.

## SSA Findings and Replacement Recommendation

SSA CLI executes successfully as version `3.40.3.0`. Read-only `show status`,
controller/configuration detail, logical-drive detail, and physical-drive detail
commands returned successfully.

| Controller field | Observed value |
| --- | --- |
| Controller | Smart Array P420i, embedded slot 0 |
| Controller Status | OK |
| Cache Board Present | True |
| Cache Status | Permanently Disabled |
| Cache Status Details | Cache disabled; backup to flash memory failed |
| Cache Disable Reason | Permanent disable condition after FBWC backup failure |
| Cache Backup Power Source | Capacitors |
| Battery/Capacitor Count | 1 |
| Battery/Capacitor Status | OK |
| Drive Write Cache | Disabled |
| No-Battery Write Cache | Disabled |
| Firmware | 4.68-0, unchanged |

Both RAID-5 logical drives report OK, no unrecoverable media errors reported,
parity initialization completed, and caching/acceleration disabled. All eight
physical drives report OK. No exhaustive media test or application consistency
test was performed.

**The cache module is the evidence-supported replacement target, not a
capacitor-only repair.** This supersedes the earlier capacitor-first hypothesis
based only on historical POST 1705. The current capacitor reports OK while the
FBWC module is permanently disabled following a flash backup failure. Software
telemetry cannot establish which individual chip failed or guarantee that an
aging capacitor will never fail, but there is no current capacitor failure or
controller-core failure reported.

The [HPE-authored DL360p Gen8 service guide, printed page 22](https://forpro.ru/wp-content/uploads/manuals/HPE_c03242811_HPE-ProLiant-DL360p-Gen8-Server-Maintenance-and-Service-Guide.pdf)
lists the matching 512 MB FBWC spare as **633540-001**. Confirm the existing
physical label and supplier compatibility before ordering. The 36-inch capacitor
assembly is separately listed under kit 671353-001; it is not the primary
replacement recommendation from the current SSA results. Replacing the entire
controller/system board or healthy disks is not supported by these findings.

The attempted read-only ADU export returned an explicit ESXi limitation:
`diag` cannot create the report locally and requires remote SSADUESXI. No ADU
archive was produced. The preserved evidence consists of the successful SSA
CLI text/status outputs, not a full ADU export or component bench test.

## Remaining Repair Gates

Before physical replacement, verify off-host backups and the restore/consistency
plan, inspect the cache/capacitor connectors and labels during an approved
powered-down maintenance window, and preserve old components for any retained
data investigation. Never force-enable unprotected write-back cache. After
repair, verify cache/capacitor health, both arrays, all drives, application
consistency, and service recovery. Issue #70 remains open for those gates and
the separate Fan 8 finding.

## Historical Faults and Limits

Before this maintenance, iLO reported P420i core status OK, aggregate Degraded,
and the 512 MB cache Failed. Both RAID-5 logical drives and all eight physical
drives reported OK. This does not establish media or application consistency.

The IML includes a March 19, 2025 POST 1705 requesting replacement of the cache
supercapacitor, followed by October 2026 cache-data-loss and backup/restore/read
failure messages. These records do not establish that the same capacitor is
still installed, repeated new losses, or which data was affected. REST reporting
the backup power source as Present does not establish capacitor charge health.

Fan 8 degradation remains a separate hardware finding. No hardware repair or
physical inspection was performed during the software installation.
