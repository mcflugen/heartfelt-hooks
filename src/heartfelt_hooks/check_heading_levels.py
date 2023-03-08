from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import mistletoe
import nbformat
import rich_click as click
from rich import print
from rich.text import Text

from ._logging import VERBOSITY, logger


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
    "--check-indent/--no-check-indent", default=True, help="Check for indent errors"
)
@click.option(
    "--check-dedent/--no-check-dedent", default=True, help="Check for dedent errors"
)
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def check_heading_levels(
    silent, verbose, file, files, check_indent, check_dedent
) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    if file:
        files += tuple(file.read().splitlines())

    validators = []
    if check_indent:
        validators.append(IndentValidator)
    if check_dedent:
        validators.append(DedentValidator)

    if not validators:
        sys.exit(0)

    error_count = 0
    for filepath in (Path(f) for f in files):
        logger.info(f"checking: {filepath}")

        for validator in (cls(filepath) for cls in validators):
            validator.validate()

            for log, info in zip(validator.log(), validator.info()):
                print(Text(log, style="bold"))
                logger.warning(info)

        error_count += validator.error_count

    if error_count:
        logger.error("💔")
    else:
        logger.info("❤️")

    sys.exit(error_count)


@dataclass
class Heading:
    level: int
    text: str


class NotebookHeadings:
    def __init__(self, filepath, cells_to_ignore=None):
        self._filepath = filepath
        self._cells_to_ignore = cells_to_ignore
        self._nb = nbformat.read(filepath, as_version=4)

        self._headings = self.extract(self._nb, cells_to_ignore=self._cells_to_ignore)

    @property
    def nb(self):
        return self._nb

    @property
    def first_level(self):
        return self._headings[0][1].level

    @property
    def min_level(self):
        return min(level for level, _ in self)

    def __iter__(self):
        for _, heading in self._headings:
            yield heading.level, heading.text

    def __str__(self):
        min_level = self.min_level
        toc = []
        for level, text in self:
            toc.append(
                f"{'  '*(level - min_level)}* [{text}](#{text.replace(' ', '-')})"
            )
        return os.linesep.join(toc)

    @staticmethod
    def extract(nb, cells_to_ignore=None):
        cells_to_ignore = cells_to_ignore if cells_to_ignore else []

        headings = []
        for count, cell in enumerate(nb.cells):
            tags = set(cell.get("metadata", {}).get("tags", []))
            if tags.isdisjoint(cells_to_ignore) and cell["cell_type"] == "markdown":
                headings_in_cell = NotebookHeadings._extract_headings_from_source(
                    cell["source"]
                )

                for h in headings_in_cell:
                    headings.append((count, h))

        return headings

    @staticmethod
    def _extract_headings_from_source(source):
        doc = mistletoe.Document(source)

        headings = []
        for child in doc.children:
            if isinstance(child, mistletoe.block_token.Heading):
                headings.append(
                    Heading(level=child.level, text=_get_content(child))
                )

        return headings


def _get_content(token):
    try:
        child = token.children[0]
    except (AttributeError, IndexError):
        return token.content
    else:
        return _get_content(child)


class NotebookHeadingValidator:
    def __init__(self, filepath):
        self._filepath = filepath
        nb = nbformat.read(filepath, as_version=4)

        self._headings = NotebookHeadings.extract(nb)
        self._errors = []

    @property
    def error_count(self):
        return len(self._errors)

    def validate(self):
        pass

    def log(self):
        entries = []

        for prev, next_ in self._errors:
            parts = [
                f"{self._filepath!s}",
                f"level={prev[1].level}(cell={prev[0]})",
                f"level={next_[1].level}(cell={next_[0]})",
            ]
            entries.append(":".join(parts))

        return entries

    def info(self):
        entries = []

        for prev, next_ in self._errors:
            parts = [
                f"{self._filepath!s}",
                f"{prev[0]}: #{'#' * prev[1].level} {prev[1].text}",
                f"{next_[0]}: #{'#' * next_[1].level} {next_[1].text}",
            ]
            entries.append(os.linesep.join(parts))

        return entries

    @staticmethod
    def _extract_headings(nb):
        headings = []
        for count, cell in enumerate(nb.cells):
            if cell["cell_type"] == "markdown":
                headings += [
                    (count, heading)
                    for heading in NotebookHeadingValidator._extract_headings_from_source(
                        cell["source"]
                    )
                ]

        return headings

    @staticmethod
    def _extract_headings_from_source(source):
        doc = mistletoe.Document(source)

        headings = []
        for heading in [
            h for h in doc.children if isinstance(h, mistletoe.block_token.Heading)
        ]:
            headings.append(Heading(level=heading.level, text=heading.content))

        return headings


class IndentValidator(NotebookHeadingValidator):
    def validate(self):
        errors = []
        for prev, next_ in pairwise(self._headings):
            if next_[1].level - prev[1].level > 1:
                errors.append((prev, next_))
        self._errors = errors
        return len(errors)


class DedentValidator(NotebookHeadingValidator):
    def validate(self):
        errors = []

        if len(self._headings) < 2:
            return []

        first_heading = self._headings[0]
        for cell, heading in self._headings[1:]:
            if heading.level < first_heading[1].level:
                errors.append((first_heading, (cell, heading)))
        self._errors = errors
        return errors
