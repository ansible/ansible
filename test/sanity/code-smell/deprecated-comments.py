"""Gather and format 'deprecated' comments"""

from __future__ import annotations

import os
import operator
import re
import shlex
import sys

from dataclasses import dataclass, field
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
        regex = re.compile(fr"{prefix}\s+deprecated:(.*)$", re.IGNORECASE)
        regexes[filetype] = regex
    return regexes


COMMENT_REGEXES = compile_comment_regexes()


@dataclass(slots=True)
class PipelineState:
    path: Path

    min_py: str

    linenum: int = -1
    full_line_length: int = 0
    deprecation_comment: str = ""

    parsed_deprecation: dict[str, str] = field(default_factory=dict)

    @property
    def prefix(self) -> str:
        col = self.full_line_length - len(self.deprecation_comment) - len("deprecated:")
        return f"{self.path}:{self.linenum}:{col}"

    def with_deprecation(self, linenum: int, full_line_length: int, deprecation_comment: str) -> PipelineState:
        return PipelineState(
            path=self.path,
            min_py=self.min_py,
            linenum=linenum,
            full_line_length=full_line_length,
            deprecation_comment=deprecation_comment,
        )


def classify_files(min_controller_py, controller_files, min_target_py, target_files) -> Iterator[PipelineState]:
    """Create initial PipelineState, attach `path` and `min_py`"""
    for raw_path in controller_files:
        path = Path(raw_path)
        if path.suffix in COMMENT_REGEXES:
            yield PipelineState(path=path, min_py=min_controller_py)

    for raw_path in target_files:
        path = Path(raw_path)
        if path.suffix in COMMENT_REGEXES:
            yield PipelineState(path=path, min_py=min_target_py)


def match_deprecations(stream: Iterator[PipelineState]) -> Iterator[PipelineState]:
    for state in stream:
        regex = COMMENT_REGEXES[state.path.suffix]
        with open(state.path, "r", encoding="utf-8", errors="ignore") as file:
            for linenum, full_line in enumerate(file, start=1):
                match = regex.search(full_line)
                if match and (comment := match.group(1)) is not None:
                    yield state.with_deprecation(linenum, len(full_line), comment)


def parse_deprecations(stream: Iterator[PipelineState]) -> Iterator[PipelineState]:
    """Parse deprecation comment to a dict, store in PipelineState.parsed_deprecation"""
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
                data[opt] = None
                continue
            key, _sep, value = opt.partition('=')
            data[key] = value

        if not data['description']:
            data['description'] = 'description not provided'

        if not any((data['core_version'], data['python_version'])):
            print(f"{state.prefix}: ansible-deprecated-version-comment-missing-version: Deprecated comment missing version")
        elif bad := set(data).difference(valid_keys):
            print(f"{state.prefix}: ansible-deprecated-version-comment-invalid-key: Deprecated comment contains invalid keys {','.join(bad)!r}")
        else:
            state.parsed_deprecation = data
            yield state


def process_deprecations(stream: Iterator[PipelineState]) -> None:
    for state in stream:
        necessary_checks = []
        if state.parsed_deprecation['core_version']:
            necessary_checks.append(
                (
                    '',
                    'core',
                    state.parsed_deprecation['core_version'],
                    ANSIBLE_VERSION,
                    operator.ge,
                )
            )
        if state.parsed_deprecation['python_version']:
            necessary_checks.append(('python-', 'python', state.parsed_deprecation['python_version'], state.min_py, operator.gt))

        for errorcode_interp, msg_interp, version, check_version, comparator in necessary_checks:
            try:
                if comparator(LooseVersion(check_version), LooseVersion(version)):
                    error_code = f"ansible-deprecated-{errorcode_interp}version-comment"
                    print(f"{state.prefix}: {error_code}: Deprecated {msg_interp} version ({version}) found: {state.parsed_deprecation['description']}")
            except (ValueError, TypeError) as exc:
                print(f"{state.prefix}: ansible-deprecated-version-comment-invalid-version: Deprecated comment contains invalid version {version}: {exc}")


def main():
    """Main entry point."""
    raw_paths = sys.argv[1:] or sys.stdin.read().splitlines()
    separator_idx = raw_paths.index('--')
    controller_paths = raw_paths[:separator_idx]
    target_paths = raw_paths[separator_idx + 1 :]
    min_controller_py = os.environ['ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS'].split(',')[0]
    min_target_py = os.environ['ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS'].split(',')[0]

    # Each step processes PipelineState objects and:
    # if it's good, yields it to the next level with modifications
    # if it's bad, prints the correct error instead
    classified_files: Iterator[PipelineState] = classify_files(min_controller_py, controller_paths, min_target_py, target_paths)
    matched_deprecations: Iterator[PipelineState] = match_deprecations(classified_files)
    parsed_deprecations: Iterator[PipelineState] = parse_deprecations(matched_deprecations)
    process_deprecations(parsed_deprecations)


if __name__ == '__main__':
    main()
