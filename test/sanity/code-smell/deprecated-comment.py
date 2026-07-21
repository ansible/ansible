"""Gather and format 'deprecated' comments"""

from __future__ import annotations

import os
import re
import shlex
import sys

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterator

import ansible.release
from ansible.module_utils.compat.version import LooseVersion

ANSIBLE_VERSION = '.'.join(ansible.release.__version__.split('.')[:3])

_COMMENT_PREFIXES = {
    ".bash": r"#",
    ".bat": r"\bREM\b",
    ".cs": r"//",
    ".fish": r"#",
    ".ini": r";",
    ".ps1": r"#",
    ".psm1": r"#",
    ".py": r"#",
    ".pyi": r"#",
    ".sh": r"#",
    ".yml": r"#",
    ".yaml": r"#",
}


def compile_comment_regexes():
    regexes = {}
    for filetype, prefix in _COMMENT_PREFIXES.items():
        regex = re.compile(fr"{prefix}\s+deprecated: (.*)$")
        regexes[filetype] = regex
    return regexes


COMMENT_REGEXES = compile_comment_regexes()


@dataclass(slots=True)
class DeprecationComment:
    path: Path

    min_py: str

    linenum: int = -1
    col: int = 0
    deprecation_comment: str = ""

    parsed_deprecation: dict[str, str | None] = field(default_factory=dict)

    @property
    def prefix(self) -> str:
        return f"{self.path}:{self.linenum}:{self.col}"

    def with_deprecation(self, linenum: int, col: int, deprecation_comment: str) -> DeprecationComment:
        return replace(self, linenum=linenum, col=col, deprecation_comment=deprecation_comment)


def classify_files(min_controller_py: str, controller_files: list[str], min_target_py: str, target_files: list[str]) -> Iterator[DeprecationComment]:
    """Yield a DeprecationComment per file whose extension supports deprecation comments."""
    for raw_path in controller_files:
        path = Path(raw_path)
        if path.suffix in COMMENT_REGEXES:
            yield DeprecationComment(path=path, min_py=min_controller_py)

    for raw_path in target_files:
        path = Path(raw_path)
        if path.suffix in COMMENT_REGEXES:
            yield DeprecationComment(path=path, min_py=min_target_py)


def match_deprecations(stream: Iterator[DeprecationComment]) -> Iterator[DeprecationComment]:
    """Scan each file for lines containing a deprecation comment."""
    for state in stream:
        regex = COMMENT_REGEXES[state.path.suffix]
        with open(state.path, "r", encoding="utf-8", errors="ignore") as file:
            for linenum, full_line in enumerate(file, start=1):
                match = regex.search(full_line)
                if match:
                    col = match.start()
                    yield state.with_deprecation(linenum, col, match.group(1))


def parse_deprecations(stream: Iterator[DeprecationComment]) -> Iterator[DeprecationComment]:
    """Parse the deprecation comment into a dict."""
    valid_keys = {'description', 'core_version', 'python_version'}
    for state in stream:
        data = dict.fromkeys(valid_keys)
        try:
            options = shlex.split(state.deprecation_comment)
        except ValueError as exc:
            print(f"{state.prefix}: ansible-deprecated-version-comment-invalid-syntax: Deprecation comment has invalid syntax: {exc}")
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
                print(f"{state.prefix}: {error}")
        else:
            yield replace(state, parsed_deprecation=data)


def process_deprecations(stream: Iterator[DeprecationComment]) -> None:
    """Report deprecations whose version has been reached or passed."""
    for state in stream:
        description = state.parsed_deprecation['description']
        core_version = state.parsed_deprecation['core_version']
        python_version = state.parsed_deprecation['python_version']

        if core_version:
            try:
                if LooseVersion(ANSIBLE_VERSION) >= LooseVersion(core_version):
                    print(f"{state.prefix}: ansible-deprecated-version-comment: Deprecated core version ('{core_version}') found: {description}")
            except (ValueError, TypeError) as exc:
                print(f"{state.prefix}: ansible-deprecated-version-comment-invalid-version: Deprecated comment contains invalid version {core_version}: {exc}")

        if python_version:
            try:
                if LooseVersion(state.min_py) > LooseVersion(python_version):
                    print(f"{state.prefix}: ansible-deprecated-python-version-comment: Deprecated python version ('{python_version}') found: {description}")
            except (ValueError, TypeError) as exc:
                print(
                    f"{state.prefix}: ansible-deprecated-version-comment-invalid-version: Deprecated comment contains invalid version {python_version}: {exc}"
                )


def main():
    """Main entry point."""
    raw_paths = sys.argv[1:] or sys.stdin.read().splitlines()
    separator_idx = raw_paths.index('--')
    controller_paths = raw_paths[:separator_idx]
    target_paths = raw_paths[separator_idx + 1 :]
    min_controller_py = os.environ['ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS'].split(',')[0]
    min_target_py = os.environ['ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS'].split(',')[0]

    # Each stage yields valid states to the next; invalid ones are printed as errors and dropped.
    classified_files: Iterator[DeprecationComment] = classify_files(min_controller_py, controller_paths, min_target_py, target_paths)
    matched_deprecations: Iterator[DeprecationComment] = match_deprecations(classified_files)
    parsed_deprecations: Iterator[DeprecationComment] = parse_deprecations(matched_deprecations)
    process_deprecations(parsed_deprecations)


if __name__ == '__main__':
    main()
