from __future__ import annotations

import contextlib
import logging
import sys
from collections import defaultdict
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
    """Print heartfelt-hooks log messages."""
    count = defaultdict(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = defaultdict(int)

    def emit(self, record: logging.LogRecord) -> None:
        """Print a log message.

        Parameters
        ----------
        record : LogRecord
            The log to print.
        """
        self.count[record.levelname] += 1

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
def logging_handler() -> Generator[None, None, None]:
    """Change, temporarily, the current logger."""
    handler = LoggingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield
    finally:
        logger.removeHandler(handler)


handler = LoggingHandler()
logger = logging.getLogger("heartfelt-hooks")
logger.addHandler(handler)
