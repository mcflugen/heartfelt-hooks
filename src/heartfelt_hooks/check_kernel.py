from __future__ import annotations

import json
import logging
import os
import pathlib
import sys
from functools import partial

import nbformat
import rich_click as click
import yaml
from rich import print
from rich.text import Text

from ._logging import VERBOSITY, logger


class NotebookLintError(Exception):
    def __init__(self, msg):
        self._msg = str(msg)

    def __str__(self):
        return self._msg


bold = partial(Text, style="bold")


@click.command()
@click.version_option()
@click.option("-s", "--silent", is_flag=True, help="Suppress status status messages.")
@click.option(
    "-v", "--verbose", count=True, help="Also emit status messages to stderr."
)
@click.option("-W", "--warning-is-error", is_flag=True, help="Treat warnings as errors")
@click.option("--kernel", help="The kernel spec as a json-formatted string.")
@click.option("--kernel-name", help="Name of the kernel.")
@click.option("--kernel-language", help="Language of the kernel.")
@click.option("--kernel-display-name", help="Display name of the kernel.")
@click.option("--fix", is_flag=True, help="Fix notebooks.")
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def nb_check_kernel(
    silent,
    verbose,
    warning_is_error,
    kernel,
    kernel_name,
    kernel_display_name,
    kernel_language,
    fix,
    files,
) -> None:
    logger.setLevel(VERBOSITY.get(verbose, logging.DEBUG))
    if silent:
        logger.setLevel(logging.ERROR)

    warning_is_error and logger.info("treating warnings as errors")
    files or logger.warning("no notebooks to check")

    kernel = json.loads(kernel) if kernel else {}
    if kernel_name:
        kernel["name"] = kernel_name
    if kernel_language:
        kernel["language"] = kernel_language
    if kernel_display_name:
        kernel["display_name"] = kernel_display_name

    # kernel = {
    #     "display_name": "CSDMS", "language": "python", "name": "csdms-2023"
    # }
    check_kernel = NotebookLintKernel(kernel=kernel)

    errors = {}
    for src_path in files:
        logger.info(f"{src_path}")

        try:
            check_kernel.check(src_path)
        except NotebookLintError as error:
            errors[src_path] = str(error)
            fix and check_kernel.fix(src_path, stream=src_path)
            # check_kernel.fix(src_path, stream=sys.stdout)

    for file_, error in sorted(errors.items()):
        print(bold(file_))
        if not silent:
            print(error)

    if len(files) and not silent:
        logger.info("❤️") if not errors else logger.error("💔")

    sys.exit(len(errors))


class NotebookLinter:
    def read(self, filepath):
        self._nb = nbformat.read(filepath, as_version=4)

    def check(self, filepath):
        pass

    def fix(self, filepath):
        pass


class NotebookLintKernel(NotebookLinter):
    def __init__(self, kernel=None):
        self._kernelspec = kernel

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

    def check(self, filepath):
        nb = nbformat.read(filepath, as_version=4)

        try:
            actual = nb["metadata"]["kernelspec"]
        except KeyError as error:
            raise NotebookLintError("notebook is missing a kernel spec") from error

        for k, v in self._kernelspec.items():
            if actual[k] != v:
                raise NotebookLintError(
                    yaml.dump({"actual": dict(actual), "expected": self._kernelspec})
                )

    def fix(self, filepath, stream=None):
        if stream is None:
            stream = sys.stdout

        nb = nbformat.read(filepath, as_version=4)

        for k, v in self._kernelspec.items():
            nb["metadata"]["kernelspec"][k] = v

        if isinstance(stream, (pathlib.Path, str)):
            with open(stream, "w") as fp:
                nbformat.write(nb, fp)
        else:
            nbformat.write(nb, stream)
