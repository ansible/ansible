from __future__ import annotations

import os
import pathlib
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

HERE = pathlib.Path(__file__).resolve().parent

COMMIT_FILE = HERE / "_commit.txt"


def _commit_from_git() -> str | None:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=HERE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return sha.decode().strip() or None


def _commit_from_file() -> str | None:
    try:
        return COMMIT_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def parent_commit() -> str | None:
    """Return the parent ansible-core commit sha, or None if unavailable.

    Resolution order:

    1. ANSIBLE_CORE_COMMIT env var, so release tooling and no-git environments
       can pin (or blank) the value.
    2. git, for normal source-tree builds.
    3. _commit.txt, written at sdist time and shipped in the sdist, so a wheel
       built from an unpacked sdist recovers the sha (there is no .git there).
    """
    override = os.environ.get("ANSIBLE_CORE_COMMIT")
    if override is not None:
        return override.strip() or None

    return _commit_from_git() or _commit_from_file()


class sdist(_sdist):
    """Persist the resolved commit into the sdist so wheels built from it keep it."""

    def run(self):
        sha = parent_commit()
        if sha:
            COMMIT_FILE.write_text(sha + "\n", encoding="utf-8")
        super().run()


class build_py(_build_py):
    """Write the resolved commit into the built package so it ships in wheels."""

    def run(self):
        super().run()
        sha = parent_commit()
        target_dir = pathlib.Path(self.build_lib) / "ansible_utils"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "_commit.py"
        target.write_text(
            "from __future__ import annotations\n\ncommit: str | None = {sha!r}\n",
            encoding="utf-8",
        )


setup(cmdclass={"sdist": sdist, "build_py": build_py})
