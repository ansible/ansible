#!/usr/bin/env python
"""Build ansible-core man pages."""

from __future__ import annotations

import argparse
import io
import pathlib
import subprocess
import sys
import tempfile

import docutils.core
import docutils.writers.manpage

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
CHECKOUT_DIR = SCRIPT_DIR.parent

DEFAULT_RELATIVE_OUTPUT_DIR = 'docs/man/man1'


def main() -> None:
    """Main program entry point."""
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output-dir', metavar='DIR', default=DEFAULT_RELATIVE_OUTPUT_DIR, type=pathlib.Path, help='directory where to build man pages')
    parser.add_argument('--version', required=True, help='version to embed in the man pages')

    args = parser.parse_args()

    build_man_pages(args.version, args.output_dir)


def build_man_pages(version: str, output_dir: pathlib.Path) -> None:
    """Build all man pages for ansible-core."""
    output_dir.mkdir(exist_ok=True, parents=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        for rst_in in _generate_rst_in_templates(pathlib.Path(temp_dir)):
            rst_doc_template = rst_in.read_text().replace('%VERSION%', version)
            destination_path = output_dir / rst_in.with_suffix('').with_suffix('').name
            print(f'Creating {destination_path.name} ...')
            _convert_rst_to_man(rst_doc_template, destination_path)


def _generate_rst_in_templates(output_dir: pathlib.Path) -> list[pathlib.Path]:
    """Create ``*.1.rst.in`` files out of CLI Python modules."""
    generate_man_cmd = (
        sys.executable,
        CHECKOUT_DIR / 'hacking/build-ansible.py',
        'generate-man',
        '--template-file', CHECKOUT_DIR / 'docs/templates/man.j2',
        '--output-dir', output_dir,
        '--output-format', 'man',
        *pathlib.Path(CHECKOUT_DIR / 'lib/ansible/cli').glob('*.py'),
    )  # fmt: skip

    subprocess.check_call(generate_man_cmd)

    return list(output_dir.glob('*.1.rst.in'))


def _convert_rst_to_man(rst_doc_template: str, destination_path: pathlib.Path) -> None:
    """Render a ``*.1.rst.in`` templates into a man page."""
    with io.StringIO(rst_doc_template) as in_mem_rst_doc:
        docutils.core.publish_file(
            source=in_mem_rst_doc,
            destination_path=destination_path,
            writer=docutils.writers.manpage.Writer(),
        )


if __name__ == '__main__':
    main()
