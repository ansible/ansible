"""Manpages generation helpers."""

import os
import typing as t
import sys
from configparser import ConfigParser
from functools import lru_cache, partial
from importlib import import_module
from pathlib import Path

from docutils.core import publish_string
from jinja2 import Template


PROJECT_DIR_PATH = Path(__file__).parents[2]


_convert_rst_to_manpage_text = partial(publish_string, writer_name='manpage')


@lru_cache(maxsize=1)
def _make_in_tree_ansible_importable() -> None:
    """Add the library directory to module lookup paths."""
    lib_path = str(PROJECT_DIR_PATH / 'lib/')
    sys.path.insert(0, lib_path)  # NOTE: for the current runtime session


@lru_cache(maxsize=1)
def _make_in_tree_sphinx_extension_importable() -> None:
    """Add the Sphinx extension directory to module lookup paths."""
    sphinx_ext_path = str(PROJECT_DIR_PATH / 'docs' / 'docsite' / '_ext')
    sys.path.insert(0, sphinx_ext_path)


@lru_cache(maxsize=1)
def _get_package_distribution_version() -> str:
    """Retrieve the current version number from setuptools config."""
    setup_cfg_path = PROJECT_DIR_PATH / 'setup.cfg'
    setup_cfg = ConfigParser()
    setup_cfg.read_string(setup_cfg_path.read_text())
    cfg_version = setup_cfg.get('metadata', 'version')
    importable_version_str = cfg_version.removeprefix('attr: ')
    version_mod_str, version_var_str = importable_version_str.rsplit('.', 1)
    _make_in_tree_ansible_importable()
    return getattr(import_module(version_mod_str), version_var_str)


@lru_cache(maxsize=1)
def _load_jinja2_template() -> Template:
    manpage_rst_template_path = (
        PROJECT_DIR_PATH
        / 'packaging'
        / 'pep517_backend'
        / '_manpage_rst_template.j2'
    )
    return Template(manpage_rst_template_path.read_text())


@lru_cache(maxsize=1)
def _lookup_cli_bin_names() -> t.List[str]:
    _make_in_tree_sphinx_extension_importable()
    lookup_cli_bin_names = import_module(
        'cli_manpages._argparse_extractors',
        'cli_manpages',
    ).lookup_cli_bin_names
    return lookup_cli_bin_names()


@lru_cache(maxsize=1)
def _get_cli_jinja2_context_generator() -> t.Callable:
    _make_in_tree_sphinx_extension_importable()
    return import_module(
        'cli_manpages._argparse_extractors',
        'cli_manpages',
    ).generate_cli_jinja2_context


def _render_manpage_rst_from_j2_template(
        jinja2_template: Template,
        cli_bin_name: str,
        ansible_version: str,
) -> str:
    generate_cli_jinja2_context = _get_cli_jinja2_context_generator()
    jinja2_ctx = generate_cli_jinja2_context(cli_bin_name)
    manpage_document = jinja2_template.render({
        'ansible_core_version': ansible_version,
        **jinja2_ctx,
    })
    return manpage_document


def generate_manpages(target_dir: os.PathLike) -> None:
    """Generate all manpages into a given directory."""
    manpages_dir_path = Path(target_dir)

    cli_bin_name_list = _lookup_cli_bin_names()
    jinja2_template = _load_jinja2_template()
    ansible_version = _get_package_distribution_version()
    for cli_bin_name in cli_bin_name_list:
        manpage_name = f'{cli_bin_name}.1'
        print(
            f'Rendering {manpage_name} RST template in-memory...',
            file=sys.stderr,
        )
        manpage_rst = _render_manpage_rst_from_j2_template(
            jinja2_template, cli_bin_name, ansible_version,
        )
        print(f'Making {manpage_name} manpage in-memory...', file=sys.stderr)
        manpage_document = _convert_rst_to_manpage_text(manpage_rst)
        print(f'Writing {manpage_name} to disk...', file=sys.stderr)
        manpages_dir_path.mkdir(exist_ok=True, parents=True)
        (manpages_dir_path / manpage_name).write_bytes(manpage_document)
