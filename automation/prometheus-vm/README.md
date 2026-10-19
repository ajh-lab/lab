# Dedicated Prometheus VM

`lab-prometheus01` (`192.168.1.50`) is the long-retention query server. The Pi
k3s Prometheus remains a lightweight agent for in-cluster discovery and
scraping; it forwards new samples to the VM. Grafana and OpenCost query the VM.
The VM's Prometheus config and systemd unit are in this directory. The cluster
Helm values are under `k8s/helm/{prometheus,grafana,opencost}/values.yaml`.

## Deployment record

- Ubuntu Server 24.04.2 LTS; hostname corrected from `lab-promethous01`.
- Prometheus 3.13.0 official Linux amd64 binary, verified against the release's
  SHA-256 sums, installed at `/opt/prometheus/3.13.0` with a `current` symlink.
  The original snap installation is disabled, not removed.
- Data directory: `/var/lib/prometheus`; retention: 90 days and 48 GB, whichever
  limit is reached first. The VM has an approximately 98 GB root filesystem.
- VM receives remote write on port 9090. UFW denies other inbound traffic;
  port 9090 is allowed from `192.168.1.49`, `.80-.84`, and `.181` (the
  administrator workstation at migration time). SSH is allowed only from
  `192.168.1.0/24`; root login and X11 forwarding are disabled using
  `90-lab-prometheus.conf`; fail2ban is enabled. Password SSH remains enabled
  until a tested key-based login is established. Revisit the `.181` rule if
  that workstation's address changes. Temporary transfer port 49091 was
  removed after the copy.
- VM credentials are in OpenBao KV v2 at
  `secret/homelab/vms/lab-prometheus01` (`host`, `username`, `password`). Never
  put values in Git or logs.
- Grafana's `initChownData` is disabled: its existing local-path volume has
  directories that reject `chown` and caused a restart CrashLoop. Preserve the
  Grafana PVC. Validate writes after any Grafana image or UID change.

## Migration evidence (2026-10-06 UTC)

- The Pi server's 12-block admin snapshot
  `20261006T180630Z-44b3e67c2ae76dd9` was transferred over a temporary
  Pi-only LAN port, checked as a complete tar archive, and imported into the
  VM. At 18:00 UTC, `count(up)` returned 45 on both the Pi and VM.
- The verified transfer archive is retained at
  `/var/backups/prometheus/20261006-pi-snapshot.tar` (root-only, 6,245,579,264
  bytes). The VM's small pre-import TSDB is preserved at
  `/var/lib/prometheus-preimport-20261006`. The old Pi TSDB and snapshot remain
  on its PVC. Do not remove these until a separate retention decision.
- Live remote write began around 19:03 UTC. The VM's Kubernetes-node series
  has a visible gap at minute resolution from approximately 18:12 to 19:03
  UTC. The source Pi TSDB retained that interval; it was not backfilled into
  the VM. The gap is longer than intended because the historical transfer and
  cluster API writes were slow.
- Prometheus Helm release 9 runs `--agent` with `/data/agent` WAL and no
  server-only TSDB flags. Grafana release 3 and OpenCost release 2 query the
  VM. The Grafana datasource UID remained `PBFA97CFB590B2093`; its health
  test returned `OK`. The agent pod was ready with zero restarts, and VM
  Kubernetes-node samples were less than a minute old at verification.
- Grafana briefly failed during cutover: its prior `init-chown-data` could
  not chown three existing PVC directories, and SQLite reported database
  locks while the Pi was under load. With the init step disabled and the Pi
  running agent mode, Grafana's database health and datasource API recovered.

## Verify

1. Check `systemctl status prometheus` and `journalctl -u prometheus` on the VM.
2. Check `http://192.168.1.50:9090/-/ready` from the LAN and from a k3s pod.
3. Query `up{job="prometheus-vm"}` and representative Pi-discovered series on
   the VM. Check the Pi agent's targets and remote-write status.
4. Confirm Grafana's Prometheus datasource and OpenCost point to the VM. Check
   recent and historical dashboard ranges after migration.
5. Watch VM disk use, memory, remote-write lag, and k3s agent restarts.

## Rollback

The pre-cutover Pi PVC and Helm release values must be retained until history
and live ingestion have been verified. The `rollback/` directory contains
overrides for the Pi's former server mode and the former Grafana and OpenCost
endpoints. Apply the Pi override with the prior Helm values first. Confirm the
Pi server is ready and answering queries before changing client endpoints.
Do not delete either TSDB as part of a rollback. The VM can remain stopped or
isolated while investigating.

The owner accepted a short metrics gap during cutover. The observed gap above
was longer than intended; do not represent the migrated history as gapless.
