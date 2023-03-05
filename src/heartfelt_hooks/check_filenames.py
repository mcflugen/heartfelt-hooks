from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any
from typing import Sequence

from rich.text import Text
from rich import print


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to check.')
    args = parser.parse_args(argv)

    error_count = 0
    for filename in (str(Path(f).name) for f in args.filenames):
        text = Text(filename)
        if text.highlight_regex(r"\s+", style="white on red"):
            error_count += 1
            print(text + ": contains whitespace")

    return error_count


if __name__ == '__main__':
    raise SystemExit(main())
