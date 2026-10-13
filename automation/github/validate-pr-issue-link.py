#!/usr/bin/env python3
"""Validate the single owning-issue declaration in a pull request body."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass

SECTION_HEADING = re.compile(r"^##[ \t]+Owning Issue[ \t]*$", re.IGNORECASE | re.MULTILINE)
NEXT_SECTION = re.compile(r"^##[ \t]+", re.MULTILINE)
HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")
REFERENCE = re.compile(
    r"(?P<keyword>Refs|Closes|Fixes|Resolves)[ \t]+"
    r"(?:(?P<owner>[A-Za-z0-9-]+)/(?P<repo>[A-Za-z0-9_.-]+))?"
    r"#(?P<number>[1-9][0-9]*)",
    re.IGNORECASE,
)


class IssueLinkError(ValueError):
    """Raised when a PR body does not declare one valid owning issue."""


@dataclass(frozen=True)
class OwningIssue:
    keyword: str
    owner: str | None
    repository: str | None
    number: int

    @property
    def target(self) -> str:
        prefix = f"{self.owner}/{self.repository}" if self.owner else ""
        return f"{prefix}#{self.number}"


def parse_owning_issue(body: str, *, allowed_owner: str = "ajh-lab") -> OwningIssue:
    headings = list(SECTION_HEADING.finditer(body or ""))
    if len(headings) != 1:
        raise IssueLinkError("PR body must contain exactly one '## Owning Issue' section")

    start = headings[0].end()
    next_heading = NEXT_SECTION.search(body, start)
    end = next_heading.start() if next_heading else len(body)
    content = HTML_COMMENT.sub("", body[start:end]).strip()
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) != 1:
        raise IssueLinkError("Owning Issue must contain exactly one reference line")

    match = REFERENCE.fullmatch(lines[0])
    if match is None:
        raise IssueLinkError(
            "use 'Refs #123' for a phase or 'Closes #123' for the final PR; "
            "cross-repository references require OWNER/REPOSITORY#123"
        )

    owner = match.group("owner")
    repository = match.group("repo")
    if (owner is None) != (repository is None):
        raise IssueLinkError("cross-repository references require owner and repository")
    if owner is not None and owner.casefold() != allowed_owner.casefold():
        raise IssueLinkError(f"owning issue must belong to {allowed_owner}")

    return OwningIssue(
        keyword=match.group("keyword").capitalize(),
        owner=owner,
        repository=repository,
        number=int(match.group("number")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body-env", default="PR_BODY")
    parser.add_argument("--allowed-owner", default="ajh-lab")
    args = parser.parse_args(argv)

    try:
        reference = parse_owning_issue(
            os.environ.get(args.body_env, ""), allowed_owner=args.allowed_owner
        )
    except IssueLinkError as exc:
        print(f"::error title=Owning issue validation failed::{exc}", file=sys.stderr)
        return 1

    print(f"Owning issue reference validated: {reference.keyword} {reference.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
