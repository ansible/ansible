"""PEP 517 build backend wrapper for optionally pre-building docs for sdist."""

from __future__ import annotations

import os
import re
import typing as t
from contextlib import contextmanager, suppress
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from setuptools.build_meta import (
    build_sdist as _setuptools_build_sdist,
    get_requires_for_build_sdist as _setuptools_get_requires_for_build_sdist,
)

from ._compat import chdir_cm
with suppress(ImportError):
    # NOTE: Only available for sdist builds that bundle manpages. Declared by
    # NOTE: `get_requires_for_build_sdist()` when `--build-manpages` is passed.
    from ._manpage_generation import generate_manpages


__all__ = (  # noqa: WPS317, WPS410
    'build_sdist', 'get_requires_for_build_sdist',
)


BUILD_MANPAGES_CONFIG_SETTING = '--build-manpages'
"""Config setting name toggle that is used to request manpage in sdists."""


@contextmanager
def _run_in_temporary_directory() -> t.Iterator[Path]:
    with TemporaryDirectory(prefix='.tmp-ansible-pep517-') as tmp_dir:
        with chdir_cm(tmp_dir):
            yield Path(tmp_dir)


def self_eliminate_from(pyproject_path):
    """Replace PEP 517 build backend with the setuptools' one."""
    pyproject_path = Path(pyproject_path)
    pyproject_path.write_text(
        re.sub(
            r"""(?x)
            backend-path\s=\s\[  # value is a list of double-quoted strings
                [^]]+
            ].*\n
            build-backend\s=\s"[^"]+".*\n  # value is double-quoted
            """,
            'build-backend = "setuptools.build_meta"\n',
            pyproject_path.read_text(),
        )
    )


def build_sdist(  # noqa: WPS210, WPS430
         sdist_directory: os.PathLike,
         config_settings: dict[str, str] | None = None,
) -> str:
    build_manpages_requested = BUILD_MANPAGES_CONFIG_SETTING in (
        config_settings or {}
    )
    original_src_dir = Path.cwd().resolve()
    with _run_in_temporary_directory() as tmp_dir:
        tmp_src_dir = Path(tmp_dir) / 'src'
        copytree(original_src_dir, tmp_src_dir, symlinks=True)
        os.chdir(tmp_src_dir)

        if build_manpages_requested:
            generate_manpages('docs/man/man1/')

        self_eliminate_from('pyproject.toml')

        built_sdist_basename = _setuptools_build_sdist(
            sdist_directory=sdist_directory,
            config_settings=config_settings,
        )

    return built_sdist_basename


def get_requires_for_build_sdist(
        config_settings: dict[str, str] | None = None,
) -> list[str]:
    build_manpages_requested = BUILD_MANPAGES_CONFIG_SETTING in (
        config_settings or {}
    )
    build_manpages_requested = True  # FIXME: Once pypa/build#559 is addressed.

    manpage_build_deps = [
        'docutils',  # provides API to convert RST to manpages
        'jinja2',  # used in `_manpage_generation.py`
        'pyyaml',  # needed for importing in-tree `ansible-core` from `lib/`
    ] if build_manpages_requested else []

    return _setuptools_get_requires_for_build_sdist(
        config_settings=config_settings,
    ) + manpage_build_deps
