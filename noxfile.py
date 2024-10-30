from __future__ import annotations

import argparse

import nox

nox.needs_version = ">=2024.4.15"
nox.options.default_venv_backend = "uv|virtualenv"


@nox.session
def lint(session: nox.Session) -> None:
    """
    Run the linter.
    """
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def pylint(session: nox.Session) -> None:
    """
    Run PyLint.
    """
    # This needs to be installed into the package environment, and is slower
    # than a pre-commit check
    session.install("-e.[copier,cookiecutter]", "pylint")
    session.run("pylint", "src", *session.posargs)


@nox.session
def tests(session: nox.Session) -> None:
    """
    Run the unit and regular tests. Use --cov to activate coverage.
    """
    session.install("-e.[test]")
    session.run("pytest", *session.posargs)


@nox.session(default=False)
def docs(session: nox.Session) -> None:
    """
    Build the docs. Use "--non-interactive" to avoid serving. Pass "-b linkcheck" to check links.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", dest="builder", default="html", help="Build target (default: html)"
    )
    args, posargs = parser.parse_known_args(session.posargs)

    serve = args.builder == "html" and session.interactive
    extra_installs = ["sphinx-autobuild"] if serve else []
    session.install("-e.[docs]", *extra_installs)

    session.chdir("docs")

    shared_args = (
        "-n",  # nitpicky mode
        "-T",  # full tracebacks
        f"-b={args.builder}",
        ".",
        f"_build/{args.builder}",
        *posargs,
    )

    if serve:
        session.run("sphinx-autobuild", "--open-browser", *shared_args)
    else:
        session.run("sphinx-build", "--keep-going", *shared_args)


@nox.session(default=False)
def build_api_docs(session: nox.Session) -> None:
    """
    Build (regenerate) API docs.
    """

    session.install("sphinx")
    session.chdir("docs")
    session.run(
        "sphinx-apidoc",
        "-o",
        "api/",
        "--no-toc",
        "--force",
        "--module-first",
        "../src/CopyCuTTer",
    )


@nox.session(default=False)
def build(session: nox.Session) -> None:
    """
    Build an SDist and wheel.
    """

    session.install("build")
    session.run("python", "-m", "build")
