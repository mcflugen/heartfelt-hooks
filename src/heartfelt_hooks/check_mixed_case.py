from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import rich_click as click
from rich import print
from rich.text import Text

from heartfelt_hooks._logging import VERBOSITY
from heartfelt_hooks._logging import logger


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
def check_mixed_case(silent, verbose, file, files) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
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

    summary = os.linesep.join(
        [
            "Summary:",
            f"checked {len(files)} filename{'s' if len(files) != 1 else ''}",
            f"found {error_count} bad filename{'s' if error_count != 1 else ''}",
        ]
    )

    if error_count:
        logger.warning(summary)
        logger.error("💔")
    else:
        logger.info(summary)
        logger.info("❤️")

    sys.exit(error_count)
