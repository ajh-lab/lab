# BS01 ingress HA and home access

## Observed state, 2026-10-11

The ER605 separates the home 192.168.1.0/24 network from rack 192.168.0.0/24.
Its rack gateway is 192.168.0.1. Hosts are gateway .2, data .3, workers .4/.5/.6.
Gateway Wi-Fi remains 192.168.1.108 for maintenance; application traffic does
not depend on that Wi-Fi link.

Keepalived on the three workers owns floating ingress address 192.168.0.10.
Traefik and droneops-web have three replicas spread over the workers. The
K3s ServiceLB exposes Traefik on each worker's TCP 80/443. VRRP uses unicast
peers, router ID 51, priorities 150/140/130, and non-preemptive recovery.
The health script verifies K3s is active and the node's HTTPS ingress serves
the console with CA and hostname validation. This is not a backend health test.

Home URL: https://droneops.192.168.1.139.sslip.io/
Rack URL: https://droneops.192.168.0.10.sslip.io/

ER605 WAN1 obtains 192.168.1.139 by DHCP, MAC 18:69:45:b2:da:d6.
An upstream UniFi reservation was saved and read back on 2026-10-11 after
checking active clients and existing reservations for conflicts.
No upstream Internet port forward was added. sslip.io resolution also depends
on DNS availability; this is not disconnected-field DNS acceptance.

## Router configuration

- IP address BS01_HOME_NET: 192.168.1.0/24; group BS01_HOME contains it.
- IP address BS01_INGRESS_VIP: 192.168.0.10/32; group BS01_WEB contains it.
- Service BS01_HTTPS: TCP source 0-65535, destination 443-443.
- ACL BS01_HTTPS_HOME_ONLY: Block, IPv4, WAN1 IN, source !BS01_HOME,
  destination IPGROUP_ANY, service BS01_HTTPS, time Any.
- Virtual server DroneOps_HTTPS_HA: WAN1 TCP external 443 ->
  192.168.0.10:443, enabled.

The ACL deliberately restricts source before enabling forwarding. It was
read back from the router; an actual non-home-source denial test is pending.
DHCP pool 192.168.0.100-199 excludes node addresses and the VIP.

## Installation and ownership

These are operational overlays, not a new signed appliance release. Argo's
DroneOps skip-reconcile remains enabled. Carry web replica/spread and hostname
settings into the next signed platform release before replacing these overlays.
Do not rewrite historical signed bundles or Helm release records.

1. Back up existing Traefik/web configuration and ingress/certificate specs.
2. Merge traefik-config.yaml into any existing HelmChartConfig before applying;
   the current cluster previously had none. Apply web-patch.json as a merge
   patch to deployment droneops-web in namespace droneops.
3. Ensure both new URL hostnames are present on all four DroneOps ingress
   rules/TLS hosts and certificate droneops-console-tls SANs. Keep canonical
   console.bs01.droneops.home.arpa. Runtime changes are already applied.
4. Install Ubuntu keepalived and iputils-arping on each worker. Verify the VIP
   is unused with duplicate-address detection before enabling the first owner.
5. Install the public console CA at /etc/keepalived/bs01-console-ca.crt.
   Copy install-keepalived.sh with LF endings and run as root with that worker's
   address (.4, .5 or .6). It refuses to replace an existing configuration.
6. Verify one and only one VIP owner, three healthy ingress/web replicas,
   and HTTPS through both the VIP and home URL.

Runtime backups are root-only on wknd01 under /root/bs01-ingress-ha-backup.
For rollback, disable the router forward first if required, restore reviewed
deployment/ingress/certificate specs, and stop/disable Keepalived on each worker.
Removing the HelmChartConfig reverts chart overrides; review other settings
before doing so. Do not apply full exported Kubernetes objects blindly.

## Evidence and remaining gates

- Three Ready Traefik replicas and three Ready web replicas, one per worker.
- Initial VIP owner wknd01; stopping only its Keepalived elected wknd02.
  VIP HTTPS remained reachable after election; service restored in finally.
- Second test stopped wknd02 Keepalived and elected wknd01. Windows on the
  home LAN received HTTP 200 for / and 401 for the unauthenticated session
  endpoint via the ER605. All Keepalived services restored.
- Windows curl used --ssl-revoke-best-effort because the private CA lacks
  revocation endpoints; certificate chain and hostname checking remained on.
- Edge loaded the sign-in page without a certificate interstitial. The page
  reports base station access code unavailable; authenticated login was not
  tested and no credentials were changed.

The initial checks above are controlled VIP-owner failovers, not physical node
power-loss tests. The runtime-loss tests below extend this evidence, but are
still not physical power cuts. Fleet-coordination, mission-control, NATS and
raster remain singletons; several use RWO volumes. The router, switch and data
host remain single points of failure. Do not claim whole-application HA.

## Automatic recovery follow-up

The owner accepts a brief interruption followed by automatic recovery; zero
downtime is not the requirement. Do not claim authenticated workflows have been
tested based on HTTP 401 alone. The disabled access-code control is an intentional
placeholder in apps/web/src/App.tsx, not evidence of a session outage.

NATS was pinned to wknd02 to avoid NodePort source NAT conflicting with the
gateway-only NetworkPolicy. That pin is now removed. The gateway runs the
loopback-only HAProxy configuration in this directory, checking the NATS INFO
greeting on all three workers. Its DRONEOPS_NATS_URL is nats://127.0.0.1:30422.
The external nats-gateway Service uses externalTrafficPolicy Local, preserving
the gateway source IP. The NetworkPolicy permits only 192.168.0.2/32 on 4222
instead of the stale 192.168.1.108/32. No NATS authentication or role was changed.
Gateway env backup: /etc/droneops-gateway/gateway.env.before-ha (root-only).
HAProxy package-default backup: /etc/haproxy/haproxy.cfg.before-bs01.
Wait for backend health checks to settle before switching clients; HAProxy 2.8
initially treats servers as up and does not support the newer init-state option.

NATS moved from wknd02 to wknd03 during rollout. Longhorn reattached its volume,
the broker reported health ok, three streams and nine consumers, and connections
from the gateway's wired IP were observed after the move.

Longhorn nodeDownPodDeletionPolicy is now
delete-both-statefulset-and-deployment-pod, also recorded in its Argo values.
Deployment and StatefulSet not-ready/unreachable tolerations are 60 seconds.
This allows replacement after Kubernetes detects node failure; it is not an
instant failover or an assertion that network partitions are equivalent to
confirmed power loss. Physical fencing and partition testing remain separate.
Merge these tolerations with any existing workload-specific tolerations.

For rollback, restore the saved NATS StatefulSet/Service specs and gateway env
as a coordinated change, then remove the proxy after verifying direct access.
Restore Longhorn's do-nothing policy and original workload tolerations if
automatic failed-node pod cleanup must be disabled. Configuration backups live
under /root/bs01-ingress-ha-backup on wknd01. No PVC is deleted by this runbook.

Aircraft safety is tracked separately in ajh-lab/droneops-platform#1170:
independent pilot takeover, flight-controller link-loss behavior, valid home/RTH
prerequisites, and stale-command rejection. Never rely on the failed platform to
issue a return command. No aircraft settings were changed during this work.

## DNS and storage host prerequisites

Run ensure-dns-ha.sh on a control-plane host. CoreDNS's K3s-managed manifest
already spreads pods across hostnames but does not specify replicas; manage its
replica count as three without editing the generated manifest. Verify one Ready
DNS pod per worker after commissioning and K3s upgrades. Rollback is scaling to
the previously saved count (one), which restores the former DNS failure risk.

Install longhorn-multipath.conf at /etc/multipath/conf.d/bs01-longhorn.conf on
each worker, then validate with multipath -t and run multipathd reconfigure.
This excludes IET VIRTUAL-DISK devices used by the Longhorn v1 engine, not
physical disks or all multipath devices. Confirm the host has no unrelated IET
storage before applying. Never flush an in-use device mapping. During this
repair, reconfiguration itself released wknd03's unused mpatha mapping; the
subsequent guarded flush found no device and did not perform a removal.
Rollback removes this one drop-in and reconfigures multipath, but can reintroduce
the mounting conflict. No filesystem formatting or PVC deletion is involved.

The first wknd01 runtime-loss test exceeded the bounded recovery window. Its
singleton DNS delayed CSI detach, then host multipath claimed the GIS volume
on wknd03. Both defects were corrected before further tests. Restoring node
availability by the safety timer is not counted as failover success.

## Runtime-loss acceptance

Tests stop K3s and its containers on one worker with k3s-killall.sh, with a
nine-minute safety restore timer and a finally path that restores K3s. Tests
wait for healthy active Longhorn volumes before the next outage. No test
removes power or simulates an asymmetric network partition.

Success requires the victim still NotReady, all seven backend component types
Ready on other workers, at least two Ready web pods, home HTTPS 200, session
HTTP 401, and a NATS INFO greeting through the gateway proxy. This does not
prove authenticated user workflows or live aircraft continuity.

- Initial wknd03 test passed at 170 seconds before the DNS/multipath fixes.
- Initial wknd01 test failed its bounded window; restored and repaired above.
- Wknd02 passed at 229 seconds with NATS moved to wknd01. Victim restored Ready.
- Wknd01 retest passed at 239 seconds after the DNS/multipath fixes, with
  NATS moved off the unavailable node. Victim restored Ready.
- Wknd03 retest passed at 311 seconds with fleet/map volumes moved to wknd01
  without manual intervention. Victim restored Ready.

Elapsed times start at shutdown initiation, including orderly host-service and
storage-unmount delays; they are not an availability SLA or measured durations
of every individual endpoint's outage.

Known separate warning: ExternalSecret droneops-registry-pull reports that its
OpenBao SecretStore is not ready. These tests used images already present on
the workers; they do not prove fresh-node image pulls or disconnected bootstrap.
Keep signed-profile integration, authenticated workflow acceptance, non-home
ACL denial, and physical/partition validation open in lab#48 / platform#670.
