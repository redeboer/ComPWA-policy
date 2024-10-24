"""Check the configuration for `Prettier <https://prettier.io>`_."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from compwa_policy.errors import PrecommitError
from compwa_policy.utilities import CONFIG_PATH, vscode
from compwa_policy.utilities.executor import Executor
from compwa_policy.utilities.readme import add_badge, remove_badge

if TYPE_CHECKING:
    from collections.abc import Iterable

    from compwa_policy.utilities.precommit import ModifiablePrecommit

# cspell:ignore esbenp rettier
__VSCODE_EXTENSION_NAME = "esbenp.prettier-vscode"
__BADGE = """
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier)
""".strip()
__BADGE_PATTERN = r"\[\!\[[Pp]rettier.*\]\(.*prettier.*\)\]\(.*prettier.*\)\n?"


def main(precommit: ModifiablePrecommit) -> None:
    if precommit.find_repo(r".*/(mirrors-)?prettier(-pre-commit)?$") is None:
        _remove_configuration()
    else:
        with Executor() as do:
            do(add_badge, __BADGE)
            do(vscode.add_extension_recommendation, __VSCODE_EXTENSION_NAME)
            do(_update_prettier_hook, precommit)
            do(_update_prettier_ignore)


def _remove_configuration() -> None:
    old_config_files = [
        ".prettierrc.json",
        ".prettierrc.json5",
        ".prettierrc.toml",
        ".prettierrc.yaml",
        ".prettierrc.yml",
        ".prettierrc",
    ]
    removed_paths = []
    for path in old_config_files:
        if os.path.exists(path):
            os.remove(path)
            removed_paths.append(path)
    if removed_paths:
        removed_paths_str = ", ".join(removed_paths)
        msg = f"Removed redundant configuration files: {removed_paths_str}"
        raise PrecommitError(msg)
    remove_badge(__BADGE_PATTERN)
    vscode.remove_extension_recommendation(__VSCODE_EXTENSION_NAME)


def _update_prettier_hook(precommit: ModifiablePrecommit) -> None:
    repo = precommit.find_repo(r".*/(mirrors-)?prettier$")
    if repo is None:
        return
    repo["repo"] = "https://github.com/ComPWA/prettier-pre-commit"
    precommit.changelog.append("Updated URL for Prettier pre-commit hook")


def _update_prettier_ignore() -> None:
    __remove_forbidden_paths()
    __insert_expected_paths()


def __remove_forbidden_paths() -> None:
    if not os.path.exists(CONFIG_PATH.prettier_ignore):
        return
    existing = __get_existing_lines()
    forbidden = {
        ".cspell.json",
        "cspell.config.yaml",
        "cspell.json",
    }
    expected = [
        s for s in existing if s.split("#", maxsplit=1)[0].strip() not in forbidden
    ]
    if existing != expected:
        __write_lines(expected)
        msg = f"Removed forbidden paths from {CONFIG_PATH.prettier_ignore}"
        raise PrecommitError(msg)


def __insert_expected_paths() -> None:
    existing = __get_existing_lines()
    obligatory = [
        "LICENSE",
    ]
    obligatory = [p for p in obligatory if os.path.exists(p)]
    expected = [*sorted(set(existing + obligatory) - {""}), ""]
    if expected == [""] and os.path.exists(CONFIG_PATH.prettier_ignore):
        os.remove(CONFIG_PATH.prettier_ignore)
        msg = f"{CONFIG_PATH.prettier_ignore} is not needed"
        raise PrecommitError(msg)
    if existing != expected:
        __write_lines(expected)
        msg = f"Added paths to {CONFIG_PATH.prettier_ignore}"
        raise PrecommitError(msg)


def __get_existing_lines() -> list[str]:
    if not os.path.exists(CONFIG_PATH.prettier_ignore):
        return [""]
    with open(CONFIG_PATH.prettier_ignore) as f:
        return f.read().split("\n")


def __write_lines(lines: Iterable[str]) -> None:
    content = "\n".join(sorted(set(lines) - {""})) + "\n"
    with open(CONFIG_PATH.prettier_ignore, "w") as f:
        f.write(content)
