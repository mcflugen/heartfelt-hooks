from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import rich_click as click
from rich import print
from rich.text import Text

from ._logging import LoggingHandler, VERBOSITY

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
    "--sausage/--no-sausage", default=True, help="Allow sausage case."
)
@click.option(
    "--snake/--no-snake", default=True, help="Allow snake case."
)
@click.option("--file", help="Read files names from a file.", type=click.File("r"))
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def check_snake_case(silent, verbose, file, files, sausage, snake) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())

    error_count = 0
    for filepath in (Path(f) for f in files):
        logger.info(f"checking: {filepath}")

        stem = filepath.stem

        if (
            (not sausage and _is_sausage(stem))
            or (not snake and _is_snake(stem))
            or _is_sausage_snake(stem)
        ):
            error_count += 1
            print(Text(str(filepath), style="bold"))

            logger.warning(filepath)

    summary = os.linesep.join(
        [
            "Summary:",
            f"checked {len(files)} filename{'s' if len(files)!=1 else ''}",
            f"found {error_count} bad filename{'s' if error_count!=1 else ''}",
        ]
    )
    if error_count:
        logger.warning(summary)
    else:
        logger.info(summary)

    sys.exit(error_count)


def _is_sausage(name):
    return "-" in name and "_" not in name


def _is_snake(name):
    return "_" in name and "-" not in name


def _is_sausage_snake(name):
    return "_" in name and "-" in name
