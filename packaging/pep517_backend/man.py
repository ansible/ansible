"""Build ansible-core man pages."""

from __future__ import annotations

import io
import pathlib
import subprocess
import sys
import tempfile
import typing as t

import docutils.core
import docutils.writers.manpage

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
CHECKOUT_DIR = SCRIPT_DIR.parent.parent

DEFAULT_RELATIVE_OUTPUT_DIR = 'docs/man/man1'


def main() -> None:
    """Main program entry point."""
    sys.path.insert(0, str(CHECKOUT_DIR / 'lib'))

    from ansible import __version__

    build_man_pages(__version__)


def build_man_pages(version: str, output_dir: pathlib.Path | None = None) -> None:
    """Build all man pages for ansible-core."""
    output_dir = output_dir or CHECKOUT_DIR / DEFAULT_RELATIVE_OUTPUT_DIR
    output_dir.mkdir(exist_ok=True, parents=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        for rst_in in _generate_rst_in_templates(pathlib.Path(temp_dir)):
            rst_doc_template = rst_in.read_text().replace('%VERSION%', version)
            destination_path = output_dir / rst_in.with_suffix('').with_suffix('').name
            print(f'Creating {destination_path.name} ...')
            _convert_rst_to_man(rst_doc_template, destination_path)


def _generate_rst_in_templates(output_dir: pathlib.Path) -> t.Iterable[pathlib.Path]:
    """Create ``*.1.rst.in`` files out of CLI Python modules."""
    entry_points = list(pathlib.Path(CHECKOUT_DIR / 'lib/ansible/cli').glob('*.py'))

    generate_man_cmd = (
        sys.executable,
        CHECKOUT_DIR / 'hacking/build-ansible.py',
        'generate-man',
        '--template-file', CHECKOUT_DIR / 'docs/templates/man.j2',
        '--output-dir', output_dir,
        '--output-format', 'man',
        *entry_points,
    )

    subprocess.run(tuple(map(str, generate_man_cmd)), check=True)

    return output_dir.glob('*.1.rst.in')


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
