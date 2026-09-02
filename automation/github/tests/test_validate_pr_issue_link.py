import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "validate-pr-issue-link.py"
REPO_ROOT = Path(__file__).parents[3]
SPEC = spec_from_file_location("validate_pr_issue_link", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PullRequestIssueLinkTests(unittest.TestCase):
    def test_accepts_phase_and_final_references(self) -> None:
        for line in (
            "Refs #12",
            "Closes #12",
            "Fixes ajh-lab/droneops-platform#750",
            "Resolves ajh-lab/droneops-gateway#106",
        ):
            with self.subTest(line=line):
                body = f"## Owning Issue\n<!-- guidance -->\n{line}\n"
                self.assertGreater(MODULE.parse_owning_issue(body).number, 0)

    def test_rejects_missing_placeholder_ambiguous_or_unowned_references(self) -> None:
        invalid = (
            "## Description\nNo owner",
            "## Owning Issue\nCloses #",
            "## Owning Issue\nRefs #0",
            "## Owning Issue\nRefs #1\nRefs #2",
            "## Owning Issue\nRefs other-org/repo#1",
            "## Owning Issue\nRefs #1\n\n## Owning Issue\nRefs #1",
        )
        for body in invalid:
            with self.subTest(body=body):
                with self.assertRaises(MODULE.IssueLinkError):
                    MODULE.parse_owning_issue(body)

    def test_template_and_workflow_enforce_the_owning_issue_contract(self) -> None:
        template = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
        workflow = (REPO_ROOT / ".github" / "workflows" / "pr-checks.yml").read_text(encoding="utf-8")

        self.assertIn("## Owning Issue", template)
        self.assertIn("Refs ajh-lab/", template)
        self.assertIn("Closes #", template)
        self.assertIn("validate-pr-issue-link.py", workflow)


if __name__ == "__main__":
    unittest.main()
