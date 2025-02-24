"""Sanity test which executes black."""

from __future__ import annotations

import itertools
import os
import re
import subprocess
import sys


def main() -> None:
    """Main program entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    env = os.environ.copy()

    controller_python_versions = env['ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS'].split(',')
    fix_mode = bool(int(env['ANSIBLE_TEST_FIX_MODE']))

    version_options = [('-t', f'py{version.replace(".", "")}') for version in controller_python_versions]

    options = {
        '-m': 'black',
        '--line-length': '160',
        '--config': '/dev/null',
    }

    flags = [
        '--skip-string-normalization',
    ]

    if not fix_mode:
        flags.append('--check')

    cmd = [sys.executable]
    cmd += itertools.chain.from_iterable(options.items())
    cmd += itertools.chain.from_iterable(version_options)
    cmd += flags
    cmd.extend(paths)

    try:
        completed_process = subprocess.run(cmd, env=env, capture_output=True, check=True, text=True)
        stdout, stderr = completed_process.stdout, completed_process.stderr

        if stdout:
            raise Exception(f'{stdout=} {stderr=}')
    except subprocess.CalledProcessError as ex:
        if ex.returncode != 1 or ex.stdout or not ex.stderr:
            raise Exception(f'{ex.returncode=} {ex.stdout=} {ex.stderr=}') from None

        stderr = ex.stderr

    stderr = re.sub('(Oh no|All done).*$', '', stderr, flags=re.DOTALL).strip()
    lines = stderr.splitlines()

    check_prefix = 'would reformat '
    fix_prefix = 'reformatted '

    prefix = fix_prefix if fix_mode else check_prefix

    for line in lines:
        if not line.startswith(prefix):
            raise Exception(f'{line=}')

        if fix_mode:
            continue

        line = line.removeprefix(prefix)

        print(f'{line}: Reformatting required. Run `ansible-test sanity --test black --fix` to update this file.')


if __name__ == '__main__':
    main()
