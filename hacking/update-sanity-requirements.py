#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Generate frozen sanity test requirements from source requirements files."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import subprocess
import tempfile
import typing as t
import venv

try:
    import argcomplete
except ImportError:
    argcomplete = None


FILE = pathlib.Path(__file__).resolve()
ROOT = FILE.parent.parent
SELF = FILE.relative_to(ROOT)


@dataclasses.dataclass(frozen=True)
class SanityTest:
    name: str
    requirements_path: pathlib.Path
    source_path: pathlib.Path

    def freeze_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as venv_dir:
            venv.create(venv_dir, with_pip=True)

            python = pathlib.Path(venv_dir, 'bin', 'python')
            pip = [python, '-m', 'pip', '--disable-pip-version-check']
            env = dict()

            pip_freeze = subprocess.run(pip + ['freeze'], env=env, check=True, capture_output=True, text=True)

            if pip_freeze.stdout:
                raise Exception(f'Initial virtual environment is not empty:\n{pip_freeze.stdout}')

            subprocess.run(pip + ['install', 'wheel'], env=env, check=True)  # make bdist_wheel available during pip install
            subprocess.run(pip + ['install', '-r', self.source_path], env=env, check=True)

            pip_freeze = subprocess.run(pip + ['freeze'], env=env, check=True, capture_output=True, text=True)

        requirements = f'# edit "{self.source_path.name}" and generate with: {SELF} --test {self.name}\n{pip_freeze.stdout}'

        with open(self.requirements_path, 'w') as requirement_file:
            requirement_file.write(requirements)

    @staticmethod
    def create(path: pathlib.Path) -> SanityTest:
        return SanityTest(
            name=path.stem.replace('sanity.', '').replace('.requirements', ''),
            requirements_path=path,
            source_path=path.with_suffix('.in'),
        )


def main() -> None:
    tests = find_tests()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test',
        metavar='TEST',
        dest='test_names',
        action='append',
        choices=[test.name for test in tests],
        help='test requirements to update'
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    test_names: set[str] = set(args.test_names or [])

    tests = [test for test in tests if test.name in test_names] if test_names else tests

    for test in tests:
        print(f'===[ {test.name} ]===')
        test.freeze_requirements()


def find_tests() -> t.List[SanityTest]:
    globs = (
        'test/lib/ansible_test/_data/requirements/sanity.*.txt',
        'test/sanity/code-smell/*.requirements.txt',
    )

    tests: t.List[SanityTest] = []

    for glob in globs:
        tests.extend(get_tests(pathlib.Path(glob)))

    return sorted(tests, key=lambda test: test.name)


def get_tests(glob: pathlib.Path) -> t.List[SanityTest]:
    path = pathlib.Path(ROOT, glob.parent)
    pattern = glob.name

    return [SanityTest.create(item) for item in path.glob(pattern)]


if __name__ == '__main__':
    main()
