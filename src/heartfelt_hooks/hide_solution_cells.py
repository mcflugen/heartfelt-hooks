from __future__ import annotations

import logging
import os
import pathlib
import sys

import nbformat
import rich_click as click

from ._logging import VERBOSITY, handler, logger


@click.command()
@click.version_option()
@click.option("-s", "--silent", is_flag=True, help="Suppress status status messages.")
@click.option(
    "-v", "--verbose", count=True, help="Also emit status messages to stderr."
)
@click.option("-W", "--warning-is-error", is_flag=True, help="Treat warnings as errors")
@click.option("--tags-to-hide", multiple=True, help="Hide cells with this tag.")
@click.option("--file", help="Read files names from a file.", type=click.File("r"))
@click.option(
    "--solution-suffix",
    default=".ipynb",
    help=(
        "Suffix of the solution notebook."
        " The solution notebook is found by removing the problem"
        " notebook's suffix and replacing it with suffix for the"
        " solution. If the solution notebook can't be found or is"
        " the same as the problem notebook, the notebook is skipped."
    ),
)
@click.option(
    "--check",
    is_flag=True,
    help=(
        "Don't write the files back, just return the"
        " status. Return code 0 means nothing would"
        " change. Return code 1 means some files would"
        " be reformatted. Return code 123 means there"
        " was an internal error."
    ),
)
@click.option(
    "--diff",
    is_flag=True,
    help="Don't write the files back, just output a diff for each file on stdout.",
)
@click.argument("files", nargs=-1, type=click.Path())
# @click.argument("files", nargs=-1, type=click.Path(exists=True))
def hide_solution_cells(
    silent,
    verbose,
    warning_is_error,
    file,
    tags_to_hide,
    solution_suffix,
    check,
    diff,
    files,
) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())
    tags_to_hide = set(tags_to_hide)

    warning_is_error and logger.info("treating warnings as errors")
    files or logger.warning("no notebooks to check")
    tags_to_hide or logger.warning("no solution cell tags provided")

    logger.debug(
        f"hiding code cells with tags: {sorted(tags_to_hide)!r}\n"
        f"{NotebookCellHider.HIDDEN_CODE_CELL_FORMAT}"
    )

    hide_cells = NotebookCellHider(tags_to_hide=tags_to_hide)

    for filepath in [pathlib.Path(f) for f in files]:
        path_to_solution = _replace_suffix(filepath, with_suffix=solution_suffix)

        if path_to_solution.is_file() and (
            not filepath.is_file() or not path_to_solution.samefile(filepath)
        ):
            logger.info(
                f"{filepath}\n"
                f"solution-notebook: {path_to_solution}\n"
                f"problem-notebook: {filepath}"
            )

            hidden_notebook = hide_cells(path_to_solution)

            if check or diff:
                try:
                    differences = NotebookCellHider.compare_notebooks(
                        nbformat.read(filepath, as_version=4), hidden_notebook
                    )
                except FileNotFoundError:
                    logger.error(
                        f"{filepath}: file does not exist, so unable to run diff."
                    )
                else:
                    if differences:
                        logger.error(f"{filepath!s}: needs updating")
                        diff and print("".join(differences))
            else:
                nbformat.write(hidden_notebook, filepath)

    n_errors = handler.count["ERROR"] + (
        handler.count["WARNING"] if warning_is_error else 0
    )

    logger.info("❤️") if not n_errors else logger.error("💔")

    sys.exit(n_errors)


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
        cells = NotebookCellHider._hide_cells(nb.cells, tags_to_hide=self._tags_to_hide)

        # nbformat.write(nb, outfile)

        return nb
        # return len(cells)

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
    def compare_notebooks(a, b):
        from difflib import unified_diff

        return list(
            unified_diff(
                os.linesep.join([cell["source"] for cell in a.cells]).splitlines(
                    keepends=True
                ),
                os.linesep.join([cell["source"] for cell in b.cells]).splitlines(
                    keepends=True
                ),
                fromfile="before",
                tofile="after",
            )
        )
