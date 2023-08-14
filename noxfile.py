import os
import pathlib
import shutil

import nox

ROOT = pathlib.Path(__file__).parent


@nox.session
def test(session: nox.Session) -> None:
    """Run the tests."""
    session.install("-r", "requirements-testing.txt")
    session.install(".")

    args = [
        "-n",
        "auto",
        "--cov",
        "check_filenames",
        "-vvv",
    ] + session.posargs

    if "CI" in os.environ:
        args.append(f"--cov-report=xml:{ROOT.absolute()!s}/coverage.xml")
    session.run("pytest", *args)

    if "CI" not in os.environ:
        session.run("coverage", "report", "--ignore-errors", "--show-missing")


@nox.session(name="test-cli")
def test_cli(session: nox.Session) -> None:
    """Test the command line interface."""
    session.install(".")

    commands = [
        "fn-check-whitespace",
        "fn-check-mixed-case",
        "fn-check-snake-case",
        "nb-check-heading-levels",
        "nb-list-headings",
        "nb-insert-toc",
        "nb-check-hidden-cells",
        "nb-hide-solution-cells",
        "nb-check-kernel",
        "nb-hide-cells",
    ]

    for command in commands:
        session.run(command, "--help", silent=True)
        session.run(command, "--version", silent=True)
        session.run(command)


@nox.session
def lint(session: nox.Session) -> None:
    """Look for lint."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")


@nox.session
def build(session: nox.Session) -> None:
    """Build sdist and wheel dists."""
    session.install("pip")
    session.install("build")
    session.run("python", "--version")
    session.run("pip", "--version")
    session.run("python", "-m", "build", "--outdir", "./build/wheelhouse")


@nox.session
def release(session):
    """Tag, build and publish a new release to PyPI."""
    session.install("zest.releaser[recommended]")
    session.run("fullrelease")


@nox.session(name="publish-testpypi")
def publish_testpypi(session):
    """Publish wheelhouse/* to TestPyPI."""
    session.install("twine")
    session.run("twine", "check", "build/wheelhouse/*")
    session.run(
        "twine",
        "upload",
        "--skip-existing",
        "--repository-url",
        "https://test.pypi.org/legacy/",
        "build/wheelhouse/*.tar.gz",
    )


@nox.session(name="publish-pypi")
def publish_pypi(session):
    """Publish wheelhouse/* to PyPI."""
    session.install("twine")
    session.run("twine", "check", "build/wheelhouse/*")
    session.run(
        "twine",
        "upload",
        "--skip-existing",
        "build/wheelhouse/*.tar.gz",
    )


@nox.session(python=False)
def clean(session):
    """Remove all .venv's, build files and caches in the directory."""
    root_folders = (
        [
            "src/check_filenames.egg-info",
            ".pytest_cache",
            ".venv",
            "build",
            "build/wheelhouse",
        ]
        if not session.posargs
        else []
    )

    with session.chdir(ROOT):
        for folder in root_folders:
            session.log(f"rm -r {folder}")
            shutil.rmtree(folder, ignore_errors=True)

    for folder in _args_to_folders(session.posargs):
        with session.chdir(folder):
            for pattern in ["*.py[co]", "__pycache__"]:
                session.log(f"rm {pattern}")
                _clean_rglob(pattern)


def _args_to_folders(args):
    return [ROOT] if not args else [pathlib.Path(f) for f in args]


def _clean_rglob(pattern):
    nox_dir = pathlib.Path(".nox")

    for p in pathlib.Path(".").rglob(pattern):
        if nox_dir in p.parents:
            continue
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()
