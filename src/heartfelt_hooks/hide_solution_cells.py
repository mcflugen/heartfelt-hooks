from __future__ import annotations

import logging
import os
import pathlib
import sys
from difflib import unified_diff

import nbformat
import rich_click as click

from ._logging import VERBOSITY, logger


@click.command()
@click.version_option()
@click.option("-s", "--silent", is_flag=True, help="Suppress status status messages.")
@click.option(
    "-v", "--verbose", count=True, help="Also emit status messages to stderr."
)
@click.option("-W", "--warning-is-error", is_flag=True, help="Treat warnings as errors")
@click.option("--tags", multiple=True, help="Hide cells with this tag.")
@click.option("--output-suffix", help="New suffix to use when writing output.")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def nb_hide_cells(
    silent,
    verbose,
    warning_is_error,
    tags,
    output_suffix,
    files,
) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    tags_to_hide = set(tags)

    warning_is_error and logger.info("treating warnings as errors")
    files or logger.warning("no notebooks to check")
    tags_to_hide or logger.warning("no solution cell tags provided")

    logger.debug(
        f"hiding code cells with tags: {sorted(tags_to_hide)!r}\n"
        f"{NotebookCellHider.HIDDEN_CODE_CELL_FORMAT}"
    )

    hide_cells = NotebookCellHider(tags_to_hide=tags_to_hide)

    error_count = 0
    for src_path in files:
        logger.info(f"{src_path}")

        hidden_notebook = hide_cells(src_path)

        hidden_notebook["metadata"]["kernelspec"] = {
            "display_name": "CSDMS",
            "language": "python",
            "name": "csdms-2023",
        }
        hidden_notebook["metadata"].pop("celltoolbar", None)

        if output_suffix:
            with open(_replace_suffix(src_path, with_suffix=output_suffix), "w") as fp:
                nbformat.write(hidden_notebook, fp)
        else:
            nbformat.write(hidden_notebook, sys.stdout)

    if len(files) and not silent:
        logger.info("❤️") if not error_count else logger.error("💔")

    sys.exit(error_count)


def _replace_suffix(filepath, with_suffix=""):
    return pathlib.Path(filepath).with_suffix("").with_suffix(with_suffix)


class NotebookCellHider:
    HIDDEN_CODE_CELL_FORMAT = """
<details>
    <summary>👉 <b>click to see solution</b></summary>

```python
{source}
```
</details>
    """.strip()

    def __init__(self, tags_to_hide=None):
        self._tags_to_hide = set([] if tags_to_hide is None else tags_to_hide)

    def __call__(self, filepath, outfile=None, check=False):
        nb = nbformat.read(filepath, as_version=4)
        NotebookCellHider._hide_cells(nb.cells, tags_to_hide=self._tags_to_hide)

        return nb

    @staticmethod
    def _hide_cells(cells, tags_to_hide=None):
        tags_to_hide = set([] if tags_to_hide is None else tags_to_hide)

        tagged_cells = []
        for cell in cells:
            tags = set(cell.get("metadata", {}).get("tags", []))
            if tags & tags_to_hide:
                tagged_cells.append(NotebookCellHider._hide_cell(cell))

        return tagged_cells

    @staticmethod
    def _hide_cell(cell):
        if cell["cell_type"] == "code":
            cell["cell_type"] = "markdown"
            cell.pop("execution_count", None)
            cell.pop("outputs", None)

            cell["source"] = NotebookCellHider.HIDDEN_CODE_CELL_FORMAT.format(**cell)
        return cell

    @staticmethod
    def compare_notebooks(a, b, **kwds):
        return list(
            unified_diff(
                os.linesep.join([cell["source"] for cell in a.cells]).splitlines(
                    keepends=True
                ),
                os.linesep.join([cell["source"] for cell in b.cells]).splitlines(
                    keepends=True
                ),
                **kwds,
            )
        )
