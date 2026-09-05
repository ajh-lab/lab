"""Contract checks for BS01 cert-manager and rack-local PKI GitOps."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FIELD_ROOT = ROOT / "k8s" / "field" / "bs01"
ARGO_ROOT = FIELD_ROOT / "argocd"
PKI_ROOT = FIELD_ROOT / "pki"
RUNBOOK = ROOT / "docs" / "bs01-pki-runbook.md"
FIELD_DOC = ROOT / "docs" / "bs01-field-rack.md"


class Bs01PkiManifestTests(unittest.TestCase):
    def test_cert_manager_application_is_pinned_ha_and_offline_cache_safe(self) -> None:
        content = (ARGO_ROOT / "cert-manager-application.yaml").read_text(encoding="utf-8")

        self.assertIn("chart: cert-manager", content)
        self.assertIn("targetRevision: v1.19.6", content)
        self.assertIn("crds:\n          enabled: true", content)
        self.assertGreaterEqual(content.count("replicaCount: 3"), 3)
        self.assertGreaterEqual(content.count("pullPolicy: IfNotPresent"), 4)
        self.assertGreaterEqual(content.count("podDisruptionBudget:"), 3)
        self.assertGreaterEqual(content.count("topologySpreadConstraints:"), 3)
        self.assertIn("topologyKey: kubernetes.io/hostname", content)
        self.assertIn("whenUnsatisfiable: DoNotSchedule", content)
        self.assertIn("CreateNamespace=true", content)

    def test_pki_application_tracks_the_public_lab_gitops_path(self) -> None:
        content = (ARGO_ROOT / "bs01-pki-application.yaml").read_text(encoding="utf-8")

        self.assertIn("repoURL: https://github.com/ajh-lab/lab.git", content)
        self.assertIn("targetRevision: main", content)
        self.assertIn("path: k8s/field/bs01/pki", content)
        self.assertIn("namespace: cert-manager", content)
        self.assertIn("prune: true", content)
        self.assertIn("selfHeal: true", content)

    def test_pki_resources_match_the_versioned_hierarchy(self) -> None:
        manifests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(PKI_ROOT.glob("*.yaml"))
        )

        for name in (
            "bs01-root-selfsigned-2026",
            "bs01-root-ca-2026",
            "bs01-ingress-ca-2026",
        ):
            self.assertIn(f"name: {name}", manifests)
        self.assertIn("duration: 87600h", manifests)
        self.assertIn("policy: Disabled", manifests)
        self.assertIn("duration: 26280h", manifests)
        self.assertIn("renewBefore: 4380h", manifests)
        self.assertIn("algorithm: ECDSA", manifests)
        self.assertIn("size: 256", manifests)
        self.assertIn("rotationPolicy: Always", manifests)
        self.assertNotRegex(manifests, r"(?m)^kind:\s*Secret\s*$")
        self.assertNotRegex(manifests, r"(?m)^(data|stringData):\s*$")

    def test_pki_kustomization_contains_only_declarative_non_secret_resources(self) -> None:
        content = (PKI_ROOT / "kustomization.yaml").read_text(encoding="utf-8")

        self.assertIn("root-ca.yaml", content)
        self.assertIn("ingress-ca.yaml", content)
        self.assertNotIn("secret", content.lower())

    def test_runbook_covers_ordered_delivery_validation_and_owner_boundaries(self) -> None:
        content = RUNBOOK.read_text(encoding="utf-8")
        normalized = " ".join(content.split()).lower()

        for heading in (
            "## Prerequisites",
            "## GitOps Installation",
            "## Validation",
            "## Public Trust Artifact",
            "## Rotation",
            "## Recovery",
            "## Rollback",
        ):
            self.assertIn(heading, content)
        self.assertIn(".kubeconfig-bs01-field.yaml", content)
        self.assertIn("private keys", normalized)
        self.assertIn("never print", normalized)
        self.assertIn("explicit action-time owner approval", normalized)
        self.assertIn("cold boot", normalized)
        self.assertIn("twice daily", normalized)
        self.assertIn("five", normalized)
        self.assertIn("longhorn backuptarget", normalized)
        self.assertIn("bs01-pki-runbook.md", FIELD_DOC.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
