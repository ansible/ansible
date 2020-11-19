#!/usr/bin/env python
# Copyright: (c) 2020-2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Making sure the type annotations are correct across packages."""

import pathlib
import subprocess
import sys


THIS_PKG_DIR = pathlib.Path(__file__).parent


def run_mypy(python_version: str = None) -> int:
    """Execute mypy against a given Python version.

    This function proxies mypy's return code and filters out
    the output so that `ansible-test` wouldn't get confused.
    """
    mypy_cmd = (
        sys.executable, '-m', 'mypy',
        '--config-file', str(THIS_PKG_DIR / 'mypy.ini'),
        '--install-types',
        '--show-error-codes',
        *(
            () if python_version is None
            else ('--python-version', python_version)
        ),
        # 'hacking/shippable/incidental.py',
        'lib/ansible/galaxy/collection/',
        'lib/ansible/galaxy/dependency_resolution',
        # 'test/lib/ansible_test/_internal',
        # 'test/utils/shippable/check_matrix.py',
    )
    if python_version and python_version[0] > '2':
        mypy_cmd += 'test/sanity/code-smell/mypy.py',  # self-test

    try:
        mypy_out = subprocess.check_output(mypy_cmd, universal_newlines=True)
    except subprocess.CalledProcessError as proc_err:
        mypy_out = proc_err.output
        return_code = proc_err.returncode
    else:
        return_code = 0

    if not return_code:
        # NOTE: Interrupt because `ansible-test sanity` runner treats any
        # NOTE: output as a linting failure.
        return return_code

    print(
        f'{__file__!s}:Results of type checking with mypy against '
        f'{python_version or "unspecified"!s} Python '
        f'(return code {return_code!s})',
        file=sys.stderr,
    )
    for line in mypy_out.splitlines():
        if line.startswith((u'Success: no issues found in ', u'Found ')):
            out_stream = sys.stderr
        else:
            out_stream = sys.stdout

        print(line, file=out_stream)

    return return_code


def main() -> int:
    """Validate type annotations with mypy against Python 2 and 3."""
    target_pythons = '3.9', '3.6', '2.7'
    return_code = sum(run_mypy(py_ver) for py_ver in target_pythons)
    return return_code


if __name__ == '__main__':
    main()
