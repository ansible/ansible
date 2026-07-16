"""Gather and format 'deprecated' comments"""

from __future__ import annotations

import os
import operator
import re
import shutil
import shlex
import subprocess
import sys

from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Iterator

import ansible.release
from ansible.module_utils.compat.version import LooseVersion
ANSIBLE_VERSION = LooseVersion('.'.join(ansible.release.__version__.split('.')[:3]))

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

    linenum: int = -1
    full_line: str = ""
    deprecation_comment: str = ""

    parsed_deprecation: dict[str, str] = field(default_factory=dict)
    
    @property
    def deprecation_start_col(self) -> int:
        """Column where the d of `deprecated:`"""
        return len(self.full_line) - len(self.deprecation_comment) - len("deprecated:")


def get_matches_ripgrep(rg_bin: str, regex: re.Pattern, stream: Iterator[PipelineState]) -> Iterator[PipelineState]:
    if not stream:
        return
    
    cmd = [
        rg_bin,
        "-I",  # TODO idk
        "-n",  # Line number
        "-H",  # Display file
        "-0",  # Separate filepath with \x00 (makes : parsing possible)
        regex.pattern,
        *[state.path for state in stream],
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode > 1:
        raise RuntimeError(f"ripgrep failed: {result.stderr}")

    for line in result.stdout.splitlines():
        path, _, match = line.partition("\x00")
        linenum, _, full_line = match.partition(":")
        match = regex.search(full_line)
        if match:
            yield PipelineState(
                path=path,
                linenum=int(linenum),
                full_line=full_line,
                deprecation_comment = match.group(1),
            )


def get_matches_python(regex: re.Pattern, stream: Iterator[PipelineState]) -> Iterator[PipelineState]:
    for state in stream:
        with open(state.path, "r", encoding="utf-8", errors="ignore") as file:
            for linenum, full_line in enumerate(file, start=1):
                match = regex.search(full_line)
                if match and (comment := match.group(1)) is not None:
                    yield PipelineState(
                        path=state.path,
                        linenum=linenum,
                        full_line=full_line,
                        deprecation_comment=comment,
                    )

        
def match_deprecations(batches: dict[str, list[PipelineState]]) -> Iterator[PipelineState]:
    ripgrep_bin = shutil.which("rg")
    if ripgrep_bin:
        get_matches = partial(get_matches_ripgrep, ripgrep_bin)
    else:
        get_matches = get_matches_python

    for ext, batch in batches.items():
        regex = COMMENT_REGEXES[ext]
        yield from get_matches(regex, batch)
    

def batch_filetypes(stream: Iterator[PipelineState]) -> dict[str, list[PipelineState]]:
    batches = {ext: [] for ext in COMMENT_REGEXES}
    for state in stream:
        batches[state.path.suffix].append(state)
    return batches


def parse_deprecations(stream: Iterator[PipelineState]) -> Iterator[PipelineState]:
    """Parse deprecation comment to a dict, store in PipelineState.parsed_deprecation"""
    valid_keys = {'description', 'core_version', 'python_version'}
    for state in stream:
        data = dict.fromkeys(valid_keys)
        for opt in shlex.split(state.deprecation_comment):
            if '=' not in opt:
                data[opt] = None
                continue
            key, _sep, value = opt.partition('=')
            data[key] = value
    
        if not data['description']:
            data['description'] = 'description not provided'
    
        if not any((data['core_version'], data['python_version'])):
            print(f"{state.path}:{state.linenum}:{state.deprecation_start_col}: ansible-deprecated-version-comment-missing-version: Deprecated comment missing version")
        elif (bad := set(data).difference(valid_keys)):
            print(f"{state.path}:{state.linenum}:{state.deprecation_start_col}: ansible-deprecated-version-comment-invalid-key: Deprecated comment contains invalid keys {','.join(bad)!r}")
        else:
            state.parsed_deprecation = data
            yield state


def process_deprecation(controller_paths, min_controller_py_version, min_target_py_version, state: PipelineState) -> PipelineState:
    necessary_checks = []
    if state.parsed_deprecation['core_version']:
        necessary_checks.append((
            '',
            'core',
            state.parsed_deprecation['core_version'],
            ANSIBLE_VERSION,
            operator.ge,
        ))
    if state.parsed_deprecation['python_version']:
        necessary_checks.append((
            'python-',
            'python',
            state.parsed_deprecation['python_version'],
            min_controller_py_version if state.path in controller_paths else min_target_py_version,
            operator.gt
        ))

    for errorcode_interp, msg_interp, version, check_version, comparator in necessary_checks:
        try:
            if comparator(LooseVersion(check_version), LooseVersion(version)):
                print(f"{state.path}:{state.linenum}:{state.deprecation_start_col}: ansible-deprecated-{errorcode_interp}version-comment: Deprecated {msg_interp} version ({version}) found: {state.parsed_deprecation['description']}")
        except (ValueError, TypeError) as exc:
            print(f"{state.path}:{state.linenum}:{state.deprecation_start_col}: ansible-deprecated-version-comment-invalid-version: Deprecated comment contains invalid version {version}: {exc}")


"""
Architecture:

It starts with a path
Each function takes an object and returns a stream

Output:
path:line:column: code: message
"""


def main():
    """Main entry point."""
    raw_paths = sys.argv[1:] or sys.stdin.read().splitlines()
    separator_idx = raw_paths.index('--')
    controller_paths = set(raw_paths[:separator_idx])
    target_paths = set(raw_paths[separator_idx + 1:])
    min_controller_py_version = os.environ['ANSIBLE_TEST_CONTROLLER_PYTHON_VERSIONS'].split(',')[0]
    min_target_py_version = os.environ['ANSIBLE_TEST_REMOTE_ONLY_PYTHON_VERSIONS'].split(',')[0]

    # It's basically the Builder pattern. Each step processes PipelineState objects and:
    # if it's good, passes it to the next level, if it's bad prints the correct error instead
    paths: Iterator[PipelineState] = (PipelineState(path=Path(path)) for path in (controller_paths | target_paths) if path.suffix in COMMENT_REGEXES)
    filetype_batches: dict[str, list[PipelineState]] = batch_filetypes(paths)  # non-lazy batches to leverage ripgrep
    matched_deprecations: Iterator[PipelineState] = match_deprecations(filetype_batches)
    parsed_deprecations: Iterator[PipelineState] = parse_deprecations(matched_deprecations)
    process = partial(process_deprecation, controller_paths, min_controller_py_version, min_target_py_version)
    _processed_deprecations: Iterator[PipelineState] = (process(state) for state in parsed_deprecations)

    # exhaust the generator so that the errors print
    list(_processed_deprecations)

if __name__ == '__main__':
    main()
