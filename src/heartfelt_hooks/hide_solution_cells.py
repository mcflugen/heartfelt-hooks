from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

import nbformat
import rich_click as click
from rich import print
from rich.text import Text

# from ._logging import LoggingHandler, VERBOSITY
from ._logging import VERBOSITY, logger

HIDDEN_CODE_CELL_FORMAT = """
<details>
    <summary>👉 <b>click to see solution</b></summary>

```python
{source}
```
</details>
""".strip()


class Success:
    def __init__(self, filepath, cells):
        self._summary = f"{filepath!s}: {len(cells)} cells were hidden"

    def __str__(self):
        return self._summary


class Failure:
    def __init__(self, filepath, error=None):
        summary = str(filepath)
        if error:
            summary += f": {error}"
        self._summary = summary

    def __str__(self):
        return self._summary


class MissingTaggedCellError(Exception):
    def __init__(self, tags):
        if isinstance(tags, str):
            tags = [tags]
        self._tags = sorted(tags)

    def __str__(self):
        return f"missing tags: {' '.join(self._tags)}"


@click.command()
@click.version_option()
@click.option(
    "-s",
    "--silent",
    is_flag=True,
    help="Suppress status status messages, including the progress bar.",
)
@click.option(
    "-v", "--verbose", count=True, help="Also emit status messages to stderr."
)
@click.option("--tags-to-hide", multiple=True, help="Hide cells with this tag.")
@click.option("--file", help="Read files names from a file.", type=click.File("r"))
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def hide_solution_cells(silent, verbose, file, tags_to_hide, files) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())
    tags_to_hide = set(tags_to_hide)

    if not tags_to_hide or not files:
        logger.info("nothing to do")
        sys.exit(0)

    logger.info(
        os.linesep.join(
            [
                f"hiding code cells with tags: {', '.join(tags_to_hide)}",
                HIDDEN_CODE_CELL_FORMAT,
            ]
        )
    )
    error_count = 0
    for filepath in files:
        logger.info(f"checking: {filepath}")

        nb = nbformat.read(filepath, as_version=4)

        try:
            cells = _hide_cells(nb.cells, tags_to_hide=tags_to_hide)
        except MissingTaggedCellError as error:
            status = Failure(filepath, error=str(error))
            success = False
        else:
            status = Success(filepath, cells)
            success = True

        if success:
            logger.info(status)
        else:
            logger.warning(status)
            error_count += 1

        nbformat.write(nb, sys.stdout)

    if error_count:
        logger.error("💔")
    else:
        logger.info("❤️")

    sys.exit(error_count)


def _hide_cells(cells, tags_to_hide=("solution",)):
    tags_to_hide = set(tags_to_hide)
    tagged_cells = []
    for cell in cells:
        tags = set(cell.get("metadata", {}).get("tags", []))
        if tags & tags_to_hide:
            tagged_cells.append(_hide_cell(cell))

    if not tagged_cells:
        raise MissingTaggedCellError(tags_to_hide)

    return tagged_cells


def _hide_cell(cell):
    if cell["cell_type"] == "code":
        cell["cell_type"] = "markdown"
        cell.pop("execution_count", None)
        cell.pop("outputs", None)

        cell["source"] = HIDDEN_CODE_CELL_FORMAT.format(**cell)
    return cell
