"""PEP 517 build backend wrapper for optionally pre-building docs for sdist."""

from __future__ import annotations

import os
import subprocess
import sys
import typing as t
from configparser import ConfigParser
from contextlib import suppress
from importlib.metadata import import_module
from io import StringIO
from pathlib import Path

from setuptools.build_meta import (
    build_sdist as _setuptools_build_sdist,
    get_requires_for_build_sdist as _setuptools_get_requires_for_build_sdist,
)

with suppress(ImportError):
    # NOTE: Only available for sdist builds that bundle manpages. Declared by
    # NOTE: `get_requires_for_build_sdist()` when `--build-manpages` is passed.
    from docutils.core import publish_file
    from docutils.writers import manpage


__all__ = (  # noqa: WPS317, WPS410
    'build_sdist', 'get_requires_for_build_sdist',
)


BUILD_MANPAGES_CONFIG_SETTING = '--build-manpages'
"""Config setting name toggle that is used to request manpage in sdists."""


def _make_in_tree_ansible_importable() -> None:
    """Add the library directory to module lookup paths."""
    lib_path = str(Path.cwd() / 'lib/')
    sys.path.insert(0, lib_path)  # NOTE: for the current runtime session


def _get_package_distribution_version() -> str:
    """Retrieve the current version number from setuptools config."""
    setup_cfg_path = Path.cwd() / 'setup.cfg'
    setup_cfg = ConfigParser()
    setup_cfg.read_string(setup_cfg_path.read_text())
    cfg_version = setup_cfg.get('metadata', 'version')
    importable_version_str = cfg_version.removeprefix('attr: ')
    version_mod_str, version_var_str = importable_version_str.rsplit('.', 1)
    _make_in_tree_ansible_importable()
    return getattr(import_module(version_mod_str), version_var_str)


def _generate_rst_in_templates() -> t.Iterable[Path]:
    """Create ``*.1.rst.in`` files out of CLI Python modules."""
    generate_man_cmd = (
        sys.executable,
        'hacking/build-ansible.py',
        'generate-man',
        '--template-file=docs/templates/man.j2',
        '--output-dir=docs/man/man1/',
        '--output-format=man',
        *Path('lib/ansible/cli/').glob('*.py'),
    )
    subprocess.check_call(tuple(map(str, generate_man_cmd)))
    return Path('docs/man/man1/').glob('*.1.rst.in')


def _convert_rst_in_template_to_manpage(
        rst_doc_template: str,
        destination_path: os.PathLike,
        version_number: str,
) -> None:
    """Render pre-made ``*.1.rst.in`` templates into manpages.

    This includes pasting the hardcoded version into the resulting files.
    The resulting ``in``-files are wiped in the process.
    """
    templated_rst_doc = rst_doc_template.replace('%VERSION%', version_number)

    with StringIO(templated_rst_doc) as in_mem_rst_doc:
        publish_file(
            source=in_mem_rst_doc,
            destination_path=destination_path,
            writer=manpage.Writer(),
        )


def build_sdist(  # noqa: WPS210, WPS430
         sdist_directory: os.PathLike,
         config_settings: dict[str, str] | None = None,
) -> str:
    build_manpages_requested = BUILD_MANPAGES_CONFIG_SETTING in (
        config_settings or {}
    )
    if build_manpages_requested:
        Path('docs/man/man1/').mkdir(exist_ok=True, parents=True)
        version_number = _get_package_distribution_version()
        for rst_in in _generate_rst_in_templates():
            _convert_rst_in_template_to_manpage(
                rst_doc_template=rst_in.read_text(),
                destination_path=rst_in.with_suffix('').with_suffix(''),
                version_number=version_number,
            )
            rst_in.unlink()

    return _setuptools_build_sdist(
        sdist_directory=sdist_directory,
        config_settings=config_settings,
    )


def get_requires_for_build_sdist(
        config_settings: dict[str, str] | None = None,
) -> list[str]:
    build_manpages_requested = BUILD_MANPAGES_CONFIG_SETTING in (
        config_settings or {}
    )
    manpage_build_deps = [
        'docutils',  # provides `rst2man`
        'jinja2',  # used in `hacking/build-ansible.py generate-man`
        'pyyaml',  # needed for importing in-tree `ansible-core` from `lib/`
    ] if build_manpages_requested else []

    return _setuptools_get_requires_for_build_sdist(
        config_settings=config_settings,
    ) + manpage_build_deps
