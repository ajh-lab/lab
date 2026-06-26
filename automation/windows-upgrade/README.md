# Windows Upgrade Remediation

This folder contains one-off Windows upgrade remediation helpers that were
originally created during the May 2026 Windows upgrade troubleshooting work.
They are preserved because they document useful recovery steps for Hyper-V,
VMware, and VirtualBox upgrade blockers.

Scripts live under `scripts/`. New script output is written to
`tmp/windows-upgrade/` so generated logs do not clutter the repository root.

Historical outputs from the original troubleshooting run are archived under:

```text
docs/windows-upgrade/2026-05-28/
```

Run these scripts only from an elevated PowerShell session when intentionally
working on Windows feature upgrade blockers.
