from __future__ import annotations

import contextlib
import logging
import sys
from collections.abc import Generator

from rich import print
from rich.text import Text

VERBOSITY = {0: logging.ERROR, 1: logging.WARNING, 2: logging.INFO}


LOG_LEVEL_STYLES: dict[str, str] = {
    "DEBUG": "bold dim",
    "INFO": "bold dim green",
    "WARNING": "magenta",
    "ERROR": "bold red",
    "CRITICAL": "bold red",
}

MULTILINE_STYLE = "dim italic"


class LoggingHandler(logging.Handler):
    """Print rollcall log messages."""

    def emit(self, record: logging.LogRecord) -> None:
        """Print a log message.

        Parameters
        ----------
        record : LogRecord
            The log to print.
        """
        level_msg = Text(
            f"[{record.levelname}]", style=LOG_LEVEL_STYLES[record.levelname]
        )
        lines = record.getMessage().splitlines()
        if len(lines) == 0:
            lines = [""]

        print(level_msg, file=sys.stderr, end="")
        if lines[0]:
            print(f" {lines[0]}", file=sys.stderr)
        else:
            print("")

        if len(lines) > 1:
            for line in lines[1:]:
                print(Text(f"+ {line}", style="dim italic"), file=sys.stderr)


@contextlib.contextmanager
def logging_handler() -> Generator[None]:
    """Change, temporarily, the current logger."""
    handler = LoggingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield
    finally:
        logger.removeHandler(handler)


logger = logging.getLogger("heartfelt-hooks")
logger.addHandler(LoggingHandler())
