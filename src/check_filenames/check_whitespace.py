from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import rich_click as click
from rich import print
from rich.text import Text

from ._logging import LoggingHandler

logger = logging.getLogger("check-whitespace")
logger.addHandler(LoggingHandler())


@click.command()
@click.version_option()
@click.option(
    "-s",
    "--silent",
    is_flag=True,
    help="Suppress status status messages, including the progress bar.",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Also emit status messages to stderr."
)
@click.option("--file", help="Read files names from a file.", type=click.File("r"))
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def check_whitespace(silent, verbose, file, files) -> None:
    if verbose:
        logger.setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())

    error_count = 0
    for filepath in (Path(f) for f in files):
        logger.info(f"checking: {filepath}")

        text = Text(filepath.name)
        if text.highlight_regex(r"\s+", style="white on red"):
            error_count += 1
            print(Text(str(filepath.parent) + os.sep) + text)

            if verbose:
                logger.warning(filepath)

    summary = os.linesep.join(
        [
            "Summary:",
            f"checked {len(files)} filename{'s' if len(files)!=1 else ''}",
            f"found {error_count} bad filename{'s' if error_count!=1 else ''}",
        ]
    )
    if error_count and verbose:
        logger.warning(summary)
    else:
        logger.info(summary)

    sys.exit(error_count)
