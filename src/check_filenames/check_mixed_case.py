from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any
from typing import Sequence

from rich.text import Text
from rich import print
import rich_click as click

from ._logging import LoggingHandler


logger = logging.getLogger("check-mixed-case")
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
def check_mixed_case(silent, verbose, file, files) -> None:

    if verbose:
        logger.setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())

    error_count = 0
    for filepath in (Path(f) for f in files):
        logger.info(f"checking: {filepath}")

        stem = filepath.stem

        if stem != stem.upper() and stem != stem.lower():
            error_count += 1
            print(Text(str(filepath), style="bold"))

            if verbose:
                logger.warning(filepath)

    summary = os.linesep.join([
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
