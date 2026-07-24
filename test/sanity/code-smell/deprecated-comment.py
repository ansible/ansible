from __future__ import annotations

import os
import re
import shlex
import sys

from dataclasses import dataclass, replace
from collections.abc import Iterator

import ansible.release
from ansible.module_utils.compat.version import LooseVersion

ANSIBLE_VERSION = '.'.join(ansible.release.__version__.split('.')[:3])

COMMENT_REGEX = re.compile("(//|#|;) deprecated: (.*)")


@dataclass(slots=True)
class DeprecationComment:
    path: str
    linenum: int
    col: int
    deprecation_comment: str
    description: str = ""
    python_version: str = ""
    core_version: str = ""

    @property
    def prefix(self) -> str:
        return f"{self.path}:{self.linenum}:{self.col}"


def match_deprecations(paths: list[str]) -> Iterator[DeprecationComment]:
    """Scan each file for lines containing a deprecation comment."""
    for file_path in paths:
        with open(file_path, "r", errors="ignore") as file:
            for linenum, full_line in enumerate(file, start=1):
                match = COMMENT_REGEX.search(full_line)
                if match:
                    yield DeprecationComment(
                        path=file_path,
                        linenum=linenum,
                        col=match.start(),
                        deprecation_comment=match.group(2))


def parse_deprecations(deprecations: Iterator[DeprecationComment]) -> Iterator[DeprecationComment]:
    """Parse the deprecation comment."""
    valid_keys = {'description', 'core_version', 'python_version'}
    for deprecation in deprecations:
        data = dict.fromkeys(valid_keys)
        try:
            options = shlex.split(deprecation.deprecation_comment)
        except ValueError as exc:
            print(f"{deprecation.prefix}: ansible-deprecated-version-comment-invalid-syntax: Deprecation comment has invalid syntax: {exc}")
            continue
        for opt in options:
            if '=' not in opt:
                data[opt.strip(',')] = None
                continue
            key, _sep, value = opt.partition('=')
            data[key.strip(',')] = value.strip(',')

        if not data['description']:
            data['description'] = 'description not provided'

        errors = []
        if not any((data['core_version'], data['python_version'])):
            errors.append("ansible-deprecated-version-comment-missing-version: Deprecated comment missing version")
        if bad := set(data).difference(valid_keys):
            errors.append(f"ansible-deprecated-version-comment-invalid-key: Deprecated comment contains invalid keys {','.join(bad)!r}")

        if errors:
            for error in errors:
                print(f"{deprecation.prefix}: {error}")
        else:
            yield replace(deprecation, **data)


def process_deprecations(stream: Iterator[DeprecationComment], min_py: str) -> None:
    """Report deprecations whose version has been reached or passed."""
    for deprecation in stream:
        description = deprecation.description
        core_version = deprecation.core_version
        python_version = deprecation.python_version
        err_prefix = deprecation.prefix

        if core_version:
            try:
                if LooseVersion(ANSIBLE_VERSION) >= LooseVersion(core_version):
                    print(f"{err_prefix}: ansible-deprecated-version-comment: Deprecated core version ('{core_version}') found: {description}")
            except (ValueError, TypeError) as exc:
                print(f"{err_prefix}: ansible-deprecated-version-comment-invalid-version: Deprecated comment contains invalid version {core_version}: {exc}")

        if python_version:
            try:
                if LooseVersion(min_py) > LooseVersion(python_version):
                    print(f"{err_prefix}: ansible-deprecated-python-version-comment: Deprecated python version ('{python_version}') found: {description}")
            except (ValueError, TypeError) as exc:
                print(f"{err_prefix}: ansible-deprecated-version-comment-invalid-version: Deprecated comment contains invalid version {python_version}: {exc}")


def main():
    """Main entry point."""
    raw_paths = sys.argv[1:] or sys.stdin.read().splitlines()
    separator_idx = raw_paths.index('--')
    controller_paths: list[str] = raw_paths[:separator_idx]
    target_paths: list[str] = raw_paths[separator_idx + 1 :]
    min_controller_py = os.environ['ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS'].split(',')[0]
    min_target_py = os.environ['ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS'].split(',')[0]

    for (paths, min_python_version) in ((controller_paths, min_controller_py),
                                        (target_paths, min_target_py)):
        raw_deprecations = match_deprecations(paths)
        deprecations = parse_deprecations(raw_deprecations)
        process_deprecations(deprecations, min_python_version)


if __name__ == '__main__':
    main()
