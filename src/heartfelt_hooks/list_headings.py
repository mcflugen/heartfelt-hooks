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

from ._logging import VERBOSITY, logger
from .check_heading_levels import NotebookHeadings


class MissingTOCError(Exception):
    def __str__(self):
        return "missing toc cell: notebook is unchanged"


class Success:
    def __init__(self, filepath, cell_no=None, contents=None):
        summary = f"{filepath!s}: inserted table of contents into cell"
        if cell_no:
            summary += f" {cell_no}"
        self._summary = [summary] + [contents] if contents else []

    def __str__(self):
        return os.linesep.join(self._summary)


class Failure:
    def __init__(self, filepath, error=None):
        summary = str(filepath)
        if error:
            summary += f": {error}"
        self._summary = summary

    def __str__(self):
        return self._summary


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
@click.option("--file", help="Read files names from a file.", type=click.File("r"))
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def list_headings(silent, verbose, file, files) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())

    for filepath in (Path(f) for f in files):
        logger.info(f"checking: {filepath}")

        headings = NotebookHeadings(filepath)

        print(headings)

    logger.info("❤️")

    sys.exit(0)


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
@click.option("--file", help="Read files names from a file.", type=click.File("r"))
@click.option(
    "--in-place",
    is_flag=True,
    help="Overwrite the existing notebook",
)
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def insert_toc(silent, verbose, file, in_place, files) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())

    error_count = 0
    for filepath in files:
        logger.info(f"checking: {filepath}")

        headings = NotebookHeadings(filepath)

        try:
            cell_no, cell = _insert_toc(headings.nb.cells, str(headings))
        except MissingTOCError as error:
            status = Failure(filepath, error=str(error))
            success = False
        else:
            status = Success(filepath, cell_no=cell_no, contents=cell["source"])
            success = True

        if success:
            logger.info(status)
        else:
            logger.warning(status)
            error_count += 1

        if in_place:
            if success:
                logger.info("f{filepath!s}: overwriting")
                nbformat.write(headings.nb, filepath)
        else:
            nbformat.write(headings.nb, sys.stdout)

    if error_count:
        logger.error("💔")
    else:
        logger.info("❤️")

    sys.exit(error_count)


def _insert_toc(cells, toc):
    count, cell = _find_toc_cell(cells)

    cell["source"] = os.linesep.join(["# Table of Contents", toc])

    return count, cell


def _find_toc_cell(cells):
    for count, cell in enumerate(cells):
        tags = cell.get("metadata", {}).get("tags", [])
        if "toc" in tags:
            return count, cell
    else:
        raise MissingTOCError()
