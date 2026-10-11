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

ER605 WAN1 currently obtains 192.168.1.139 by DHCP, MAC 18:69:45:b2:da:d6.
An upstream reservation is still required before treating this URL as durable.
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

These are controlled VIP-owner failovers, not physical node power-loss tests.
Fleet-coordination, mission-control, NATS and raster still have singleton
deployments; several use RWO volumes. Full application continuity requires
separate backend/storage recovery validation. The router, switch and data host
also remain single points of failure. Do not claim whole-application HA.
