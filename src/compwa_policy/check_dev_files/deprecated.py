"""Remove deprecated linters and formatters."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from compwa_policy.errors import PrecommitError
from compwa_policy.utilities import remove_configs, vscode
from compwa_policy.utilities.executor import Executor

if TYPE_CHECKING:
    from compwa_policy.utilities.file import LineEditor
    from compwa_policy.utilities.precommit import ModifiablePrecommit


def remove_deprecated_tools(
    gitignore: LineEditor, precommit: ModifiablePrecommit, *, keep_issue_templates: bool
) -> None:
    with Executor() as do:
        if not keep_issue_templates:
            do(_remove_github_issue_templates)
        do(_remove_markdownlint, gitignore, precommit)
        for directory in ["docs", "doc"]:
            do(_remove_relink_references, directory)


def _remove_github_issue_templates() -> None:
    remove_configs([
        ".github/ISSUE_TEMPLATE",
        ".github/pull_request_template.md",
    ])


def _remove_markdownlint(gitignore: LineEditor, precommit: ModifiablePrecommit) -> None:
    with Executor() as do:
        do(remove_configs, [".markdownlint.json", ".markdownlint.yaml"])
        do(gitignore.remove, ".markdownlint.json")
        do(
            vscode.remove_extension_recommendation,
            # cspell:ignore davidanson markdownlint
            extension_name="davidanson.vscode-markdownlint",
            unwanted=True,
        )
        do(precommit.remove_hook, "markdownlint")


def _remove_relink_references(directory: str) -> None:
    path = f"{directory}/_relink_references.py"
    if not os.path.exists(path):
        return
    msg = (
        f"Please remove {path!r} and use https://pypi.org/project/sphinx-api-relink"
        " instead."
    )
    raise PrecommitError(msg)
