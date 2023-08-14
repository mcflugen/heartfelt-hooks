from __future__ import annotations

import logging
import pathlib
import sys
from functools import partial

import nbformat
import rich_click as click
from rich import print
from rich.text import Text

from ._logging import VERBOSITY, logger
from .hide_solution_cells import NotebookCellHider

bold = partial(Text, style="bold")


@click.command()
@click.version_option()
@click.option("-s", "--silent", is_flag=True, help="Suppress status status messages.")
@click.option(
    "-v", "--verbose", count=True, help="Also emit status messages to stderr."
)
@click.option("--tags", multiple=True, help="Hide cells with this tag.")
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
    "--diff",
    is_flag=True,
    help="Print a diff for each file on stdout.",
)
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def nb_check_hidden_cells(
    silent,
    verbose,
    tags,
    solution_suffix,
    diff,
    files,
) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    tags_to_hide = set(tags)

    hide_cells = NotebookCellHider(tags_to_hide=tags_to_hide)

    dst_src_paths = []
    for dst_path in [pathlib.Path(f) for f in files]:
        src_path = _replace_suffix(dst_path, with_suffix=solution_suffix)

        if not src_path.is_file():
            logger.debug(f"{src_path!s}: source file not found.")
        elif dst_path.is_file() and dst_path.samefile(src_path):
            logger.debug(f"{dst_path!s}: source and destination file are the same.")
        else:
            dst_src_paths.append((dst_path, src_path))

    error_count = 0
    for dst_path, src_path in dst_src_paths:
        logger.info(
            f"checking: {dst_path}\n"
            f"solution-notebook: {src_path}\n"
            f"problem-notebook: {dst_path}"
        )

        hidden_notebook = hide_cells(src_path)

        differences = NotebookCellHider.compare_notebooks(
            nbformat.read(dst_path, as_version=4),
            hidden_notebook,
            fromfile=str(dst_path),
            tofile=str(src_path),
        )
        if differences:
            error_count += 1
            if diff:
                print(_highlight_diff("".join(differences)))
            else:
                print(bold(f"{dst_path!s}"))

    if len(dst_src_paths) and not silent:
        logger.info("❤️") if not error_count else logger.error("💔")

    sys.exit(error_count)


def _highlight_diff(text):
    from pygments import highlight
    from pygments.formatters import TerminalFormatter
    from pygments.lexers.diff import DiffLexer

    highlighted = highlight(text, DiffLexer(), TerminalFormatter())
    return Text.from_ansi(highlighted)


def _replace_suffix(filepath, with_suffix=""):
    return pathlib.Path(filepath).with_suffix("").with_suffix(with_suffix)
