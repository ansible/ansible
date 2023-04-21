"""Manpages generation helpers."""

import os
import typing as t
import subprocess
import sys
from configparser import ConfigParser
from functools import lru_cache
from importlib import import_module
from io import StringIO
from pathlib import Path

from docutils.core import publish_file
from docutils.writers import manpage


@lru_cache(maxsize=1)
def _make_in_tree_ansible_importable() -> None:
    """Add the library directory to module lookup paths."""
    lib_path = str(Path.cwd() / 'lib/')
    sys.path.insert(0, lib_path)  # NOTE: for the current runtime session


@lru_cache(maxsize=1)
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


def _generate_rst_in_templates(target_dir: os.PathLike) -> t.Iterable[Path]:
    """Create ``*.1.rst.in`` files out of CLI Python modules."""
    generate_man_cmd = (
        sys.executable,
        'hacking/build-ansible.py',
        'generate-man',
        '--template-file=docs/templates/man.j2',
        f'--output-dir={target_dir !s}',
        '--output-format=man',
        *Path('lib/ansible/cli/').glob('*.py'),
    )
    subprocess.check_call(tuple(map(str, generate_man_cmd)))
    return Path(target_dir).glob('*.1.rst.in')


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


def generate_manpages(target_dir: os.PathLike) -> None:
    """Generate all manpages into a given directory."""
    Path(target_dir).mkdir(exist_ok=True, parents=True)
    version_number = _get_package_distribution_version()
    for rst_in in _generate_rst_in_templates(target_dir):
        _convert_rst_in_template_to_manpage(
            rst_doc_template=rst_in.read_text(),
            destination_path=rst_in.with_suffix('').with_suffix(''),
            version_number=version_number,
        )
        rst_in.unlink()
