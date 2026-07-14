#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Generate frozen sanity test requirements from source requirements files."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import subprocess
import tempfile
import typing as t
import venv

import packaging.version
import packaging.specifiers
import packaging.requirements

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
        source_requirements = [packaging.requirements.Requirement(re.sub(' #.*$', '', line)) for line in self.source_path.read_text().splitlines()]

        install_packages = {requirement.name for requirement in source_requirements}
        exclude_packages = {'distribute', 'pip', 'setuptools', 'wheel'} - install_packages

        with tempfile.TemporaryDirectory() as venv_dir:
            venv.create(venv_dir, with_pip=True)

            python = pathlib.Path(venv_dir, 'bin', 'python')
            pip = [python, '-m', 'pip', '--disable-pip-version-check']
            env = dict()

            pip_freeze = subprocess.run(pip + ['freeze'], env=env, check=True, capture_output=True, text=True)

            if pip_freeze.stdout:
                raise Exception(f'Initial virtual environment is not empty:\n{pip_freeze.stdout}')

            subprocess.run(pip + ['install', '-r', self.source_path], env=env, check=True)

            freeze_options = ['--all']

            for exclude_package in exclude_packages:
                freeze_options.extend(('--exclude', exclude_package))

            pip_freeze = subprocess.run(pip + ['freeze'] + freeze_options, env=env, check=True, capture_output=True, text=True)

        self.write_requirements(pip_freeze.stdout)

    def update_pre_build(self) -> None:
        """Update requirements in place with current pre-build instructions."""
        requirements = pathlib.Path(self.requirements_path).read_text()
        lines = requirements.splitlines(keepends=True)
        lines = [line for line in lines if not line.startswith('#')]
        requirements = ''.join(lines)

        self.write_requirements(requirements)

    def write_requirements(self, requirements: str) -> None:
        """Write the given test requirements to the requirements file for this test."""
        pre_build = pre_build_instructions(requirements)

        requirements = f'# edit "{self.source_path.name}" and generate with: {SELF} --test {self.name}\n{pre_build}{requirements}'

        with open(self.requirements_path, 'w') as requirement_file:
            requirement_file.write(requirements)

    @staticmethod
    def create(path: pathlib.Path) -> SanityTest:
        return SanityTest(
            name=path.stem.replace('sanity.', '').replace('.requirements', ''),
            requirements_path=path,
            source_path=path.with_suffix('.in'),
        )


def pre_build_instructions(requirements: str) -> str:
    """Parse the given requirements and return any applicable pre-build instructions."""
    parsed_requirements = requirements.splitlines()

    package_versions = {
        match.group('package').lower(): match.group('version') for match
        in (re.search('^(?P<package>.*)==(?P<version>.*)$', requirement) for requirement in parsed_requirements)
        if match
    }

    instructions: list[str] = []

    build_constraints = (
        ('pyyaml', '>= 5.4, <= 6.0', ('Cython < 3.0',)),
    )

    for package, specifier, constraints in build_constraints:
        version_string = package_versions.get(package)

        if version_string:
            version = packaging.version.Version(version_string)
            specifier_set = packaging.specifiers.SpecifierSet(specifier)

            if specifier_set.contains(version):
                instructions.append(f'# pre-build requirement: {package} == {version}\n')

                for constraint in constraints:
                    instructions.append(f'# pre-build constraint: {constraint}\n')

    return ''.join(instructions)


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

    parser.add_argument(
        '--pre-build-only',
        action='store_true',
        help='apply pre-build instructions to existing requirements',
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    test_names: set[str] = set(args.test_names or [])

    tests = [test for test in tests if test.name in test_names] if test_names else tests

    for test in tests:
        print(f'===[ {test.name} ]===', flush=True)

        if args.pre_build_only:
            test.update_pre_build()
        else:
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
