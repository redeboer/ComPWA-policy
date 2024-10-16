"""Set nbformat minor version to 4.

nbformat adds random cell ids since version 5.x. This is annoying for git
diffs. The solution is to set the version to v4 and removes those cell ids.
"""

from __future__ import annotations

import argparse
import sys
from textwrap import dedent
from typing import TYPE_CHECKING

import nbformat

from compwa_policy.errors import PrecommitError
from compwa_policy.utilities.executor import Executor
from compwa_policy.utilities.notebook import load_notebook

if TYPE_CHECKING:
    from collections.abc import Sequence

BINARY_CELL_OUTPUT = [
    "image/jpeg",
    "image/png",
    "image/svg+xml",
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("filenames", nargs="*", help="Filenames to fix.")
    args = parser.parse_args(argv)
    with Executor(raise_exception=False) as do:
        for filename in args.filenames:
            do(set_nbformat_version, filename)
            do(remove_cell_ids, filename)
            do(check_svg_output_cells, filename)
    return 1 if do.error_messages else 0


def set_nbformat_version(filename: str) -> None:
    notebook = load_notebook(filename)
    if notebook["nbformat_minor"] != 4:  # noqa: PLR2004
        notebook["nbformat_minor"] = 4
        nbformat.write(notebook, filename)


def remove_cell_ids(filename: str) -> None:
    notebook = load_notebook(filename)
    for cell in notebook["cells"]:
        if "id" in cell:
            del cell["id"]
    nbformat.write(notebook, filename)


def check_svg_output_cells(filename: str) -> None:
    notebook = load_notebook(filename)
    for i, cell in enumerate(notebook["cells"]):
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            for binary in BINARY_CELL_OUTPUT:
                if binary in data:
                    error_message = f"""
                    Cell {i} in {filename} contains {binary} output. Please
                    store it somewhere outside this repository and render it
                    through an external link. See for instance
                    https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files
                    """
                    raise PrecommitError(
                        dedent(error_message).strip().replace("\n", " ")
                    )


if __name__ == "__main__":
    sys.exit(main())
