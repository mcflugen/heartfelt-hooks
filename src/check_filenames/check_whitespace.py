from __future__ import annotations

import argparse
import logging
import os
import re
from pathlib import Path
from typing import Any
from typing import Sequence

from rich.text import Text
from rich import print

import rich_click as click

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
@click.option(
    "--file", help="Read files names from a file.", type=click.File("r")
)
@click.argument('files', nargs=-1, type=click.Path(exists=True))
def check_whitespace(silent, verbose, file, files) -> int:
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
            print(str(filepath.parent) + os.sep, end="")
            print(text)

    logger.info(f"checked {len(files)} filename{'s' if len(files) else ''}")
    if error_count:
        logger.info(f"found {error_count} bad filename{'s' if error_count else ''}")
    else:
        logger.info(f"all files passed")

    return error_count


if __name__ == '__main__':
    raise SystemExit(main())
