# Preparing cached BS01 release images

## Source and conversion boundary

Platform #1087's bundle verifier requires one complete Linux/amd64 OCI image
per archive. Real K3s caches include Docker schema-2 manifests and multiarch
indexes. The build-side helper `automation/droneops/releases/oci_archive.py`
selects exactly one Linux/amd64 child from an independently recorded source
digest, validates the descriptor sizes and SHA-256 content closure, and
rewrites only Docker manifest media-type metadata to OCI. It preserves config
and layer bytes, including build metadata. Existing OCI manifest bytes retain
their digest. A converted Docker manifest has a new digest that must be used
in the signed release inventory; never label it as the old digest.

The source digest binds the index before architecture selection. Missing,
ambiguous or wrong-architecture content, path traversal, links, duplicate
paths/JSON keys, remote blob URLs, corrupt payloads and unsupported media
types fail before publication. The converter does not extract, execute,
download, sign or import anything. It refuses output replacement. It is a
build preparation tool; the independent platform release verifier remains
mandatory before signing and every device activation.

## Procedure

1. Record the running and chart-hook inventory, plus infrastructure images
   needed for restart (including the K3s pod sandbox image). Confirm the
   exact source reference/digest in a Ready local content inventory.
2. Export each source through pinned administrative SSH using
   `k3s ctr -n k8s.io images export --local --platform linux/amd64
   --skip-manifest-json OUTPUT SOURCE`. Use a bounded task-owned temporary
   file, copy over SSH and compare the remote/local SHA-256. No registry pull
   is required for this path. Do not delete or retag the source.
3. Run `python -m automation.droneops.releases.oci_archive SOURCE OUTPUT
   --source-digest sha256:RECORDED_DIGEST`. Retain the returned source,
   selected-source, converted-manifest, config and layer identities.
4. Run the platform's complete OCI/bundle verifier on the result. Bind each
   converted manifest digest to its original image repository in the signed
   inventory. Review that configuration/layer digests match the selected
   original image. Only after verification, remove task-owned raw exports.

The archive's `appliance` tag is a packaging label; the updater's `--local`,
`--digests` and `--base-name` import makes the signed immutable reference available. A
cached immutable reference does not by itself prove an existing infrastructure
tag is available or that every Pod uses `Never`/`IfNotPresent`. Audit those
separately before claiming restart independence. Do not silently modify
infrastructure tags or manifests as a side effect of artifact preparation.

## Kubelet credential verification

On K3s 1.36.3, the live default `NeverVerifyPreloadedImages` policy still
requires matching credentials for an image previously pulled by kubelet.
Containerd and CRI can report that image present while a Pod without those
credentials fails with `ErrImageNeverPull`. This was observed in the first
BS01 baseline migration hook; Helm was interrupted before application rollout,
and the pending hook was removed. The failed Helm revision remains recorded.

The appliance profile supplies
`k8s/field/bs01/updater/90-droneops-offline-images.conf` as a root-owned kubelet
drop-in. It selects `NeverVerifyAllowlistedImages` with exactly 35 repository
names from the reviewed application and infrastructure inventory. There are
no registry-wide wildcards. Other repositories require credential verification.
The allowlist granularity is a repository, not a tag or digest: any Pod allowed
onto the node can use a locally present image from those repositories. Signed
bundle verification and the restricted importer remain the artifact admission
boundary; this kubelet setting is not a substitute for signature verification
or Kubernetes workload authorization. Do not disable the feature gate, use
`NeverVerify`, or delete kubelet credential records as a shortcut.

After the separate operational approval and a current recovery point, install
the reviewed file as root:root mode 0644 into
`/var/lib/rancher/k3s/agent/etc/kubelet.conf.d/`. Restart the `k3s` service on
one server at a time. Require three Ready nodes before each restart, then
verify that node's API readiness, effective `/configz` policy and all workload
health before proceeding. This is a service restart, not a physical cold boot.
If readiness or policy verification fails, restore only the prior task-owned
drop-in (or remove the newly introduced file), restart that same service and
reverify quorum and workloads. Preserve other kubelet configuration files.

K3s documents this [drop-in directory](https://docs.k3s.io/installation/configuration).
The pinned Kubernetes 1.36.3
[policy implementation](https://github.com/kubernetes/kubernetes/blob/v1.36.3/pkg/kubelet/images/pullmanager/image_pull_policies.go)
matches allowlisted repository names independently of prior pull records.
Live success after applying this policy must be recorded separately; the
configuration test only checks its scope and selected policy.

On 2026-10-09, merged lab #45 (`a563c9d`) was installed on all three BS01
servers. Sequential K3s service restarts completed with three Ready nodes,
effective policy and all seven platform deployments plus NATS checked after
each server. A disposable migration-image Pod using `Never`, no pull secret
and no mounted Secret succeeded; it was removed. No OS reboot or physical
cold boot ran. The policy must be restored explicitly after recovery from
the tested pre-handoff K3s snapshot, which predates this configuration.

The reviewed importer verified all 35 signed immutable references ready and
unpacked on all three nodes. The separate 25-reference infrastructure audit
also passed on every node after creating 16 previously absent aliases from
approved content without overwriting existing references. Helm baseline
revision 2 and the subsequent sequential cleanup of legacy pull-secret
references left eight ready workloads with digest images, `Never`, and no
`imagePullSecrets`. Native Secret identities and content hashes were unchanged.
See platform `docs/context/issue-1087-acceptance.md` for final updater outcomes.

## Verification

Run `python -m unittest automation.droneops.releases.tests.test_oci_archive`.
Fixtures prove deterministic payload-preserving conversion, native OCI digest
preservation and fail-closed malformed input. During 2026-10-09 production
preparation, ordinary skopeo conversion changed Docker config/build metadata,
so it was not accepted for the exact-payload path. This helper's CSI-attacher
output preserved config/layers and passed the platform OCI verifier locally.
This is artifact evidence, not a live import, workload change or cold boot.
