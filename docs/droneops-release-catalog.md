# DroneOps release catalog

## Scope and custody

Platform issue #1087 owns this explicitly selected connected update service.
The catalog is planned on `lab-gha-runner-01` (`192.168.1.48`), using
`https://releases.droneops.home.arpa:8443/releases/catalog.json`. The BS01
updater uses a managed hosts entry for this name. Catalog access is outbound
from BS01 and is not required for operation of an installed release. Physical
isolation and cold boot are separately owned by #670.

Use `automation/droneops/releases/catalog_config.py` with the approved BS01
certificate's SHA-1 fingerprint to render nginx configuration. This fingerprint
is an exact identity allowlist, not a signature algorithm. TLS verifies the
certificate chain against a dedicated client CA before checking the allowlist.
Only that individual BS01 certificate can retrieve files. No-certificate and
other valid-client requests fail closed; uploads and directory listings are
disabled. The catalog is static and has no administrative endpoint.

The nginx process runs as `droneops-catalog`, without capabilities, with a
read-only filesystem and bounded CPU/memory. Root owns the configuration,
credentials and release tree. Public bundles are readable by the service;
its TLS key is root-owned, group-readable only by `droneops-catalog`, mode
0640. No signing key or client private key belongs on the catalog host.

OpenBao custody uses dedicated paths under the `secret` KV v2 mount:

- `homelab/droneops/releases/authority`: release signer and separate catalog
  server/client CA private keys and public certificates.
- `homelab/droneops/releases/catalog`: server certificate and private key.
- `homelab/droneops/releases/devices/bs01`: unique client certificate and
  private key, catalog CA certificate and release verification public key.

Signing uses protected operator-side memory or temporary private files,
outside BS01 and the catalog/CI runner. BS01 receives only public release
verification trust plus its own private client credential. Never put secret
values in repository files, manifests, bundles, catalog JSON or logs.

## Installation and publication

Install nginx from Ubuntu's package source. Preserve any existing nginx
service/configuration; this unit uses its own config and unprivileged port.
Create the service account without a shell and create these root-owned paths:

- `/etc/droneops/catalog/nginx.conf`
- `/etc/droneops/catalog/tls/{server.pem,server.key,client-ca.pem}`
- `/srv/droneops/releases/`
- `/etc/systemd/system/droneops-release-catalog.service`

Install the versioned unit from `automation/droneops/releases/`, validate with
`nginx -t` as the service account, and enable only this dedicated service.
Before publishing, require at least 5 GiB free after publication and a maximum
12 GiB of published release files. Recheck the host's actual free space and
bundle sizes; do not delete unrelated runner caches or files to satisfy the
limit. Keep current and previous approved releases; remove older files only
after confirming neither BS01's current/previous custody nor recovery needs
them. Publish immutable bundle names first, verify SHA-256 and byte counts,
then atomically replace `catalog.json`. Never overwrite a versioned bundle.

Catalog schema and client verification are defined by platform
`scripts/bs01_release_catalog.py`. Each version has a same-origin HTTPS URL,
exact SHA-256 and byte count. A signed bundle remains independently verified
by BS01 even if the catalog host is compromised. No automatic latest-version
selection or unattended activation is enabled.

## Verification, rotation and recovery

Run `python3 -m unittest automation.droneops.releases.tests.test_catalog` on
Linux with nginx and openssl. It makes real TLS requests, accepts the approved
identity, rejects a second certificate from the same CA and an anonymous
client, and rejects PUT, key-path access and directory listing.

After deployment, repeat authentication tests against the real endpoint from
BS01 without printing credentials, and download/verify a selected actual
signed bundle. Record the public certificate fingerprint/expiry, service
state, source revision, bundle hashes/sizes and test outcomes separately.
Rotate leaf credentials before their expiry by issuing a replacement through
OpenBao, installing the device identity, and updating the exact allowlist in
one supervised window. Retire the old certificate from nginx immediately;
the allowlist makes it unusable even while its CA remains trusted. Root
rotation requires independently approved trust distribution; never download
new trust automatically from the catalog being verified.

Rollback stops/disables only `droneops-release-catalog.service` and restores
its protected previous config/credentials. BS01 keeps operating from local
approved bundles. Rebuild this static service from Git, OpenBao and retained
signed artifacts; it holds no unique field operational data.

## Evidence boundary

Lab PRs #41-#43 are merged. On 2026-10-09 the dedicated nginx service is active
on the documented runner, with protected TLS files and the BS01 certificate
allowlist. A real BS01 client request succeeds and an anonymous request is
rejected. Signing custody remains off BS01 and off the catalog host. Device
access, pinned SSH and the fixed read-only Flyway probe are installed; direct
Secret reads, pod exec, PVC deletion and unrelated sudo commands are denied.

The service is recorded as NetBox service 2 on VM `lab-gha-runner-01` and at
[Wiki.js](https://wikijs.192.168.1.80.sslip.io/en/services/droneops-release-catalog),
with API readback verification. The platform issue separately tracks signed
bundle consumption, all-node imports, ownership handoff, upgrade and rollback.
Catalog installation alone does not establish those results or physical
isolation/cold boot, which remain under platform #670.
