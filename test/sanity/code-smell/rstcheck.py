"""Sanity test using rstcheck and sphinx."""
from __future__ import annotations

import re
import subprocess
import sys
import typing as t
from shlex import join as _shlex_join


RSTLINT_VIOLATION_ENTRY_REGEX = re.compile(
    r"""
    ^
    (?P<path>[^:]*):(?P<line>[0-9]+):
    \s
    \((?P<level>INFO|WARNING|ERROR|SEVERE)/[0-4]\)
    \s
    (?P<message>.*)
    $
    """,
    re.X,
)


class RSTLintError(RuntimeError):
    """Exception-container of ``rstcheck`` rule violations."""

    linting_violations: t.List[t.Dict[str, t.Union[str, int]]]

    def __init__(self, rstlint_output: str):
        self.linting_violations = _parse_to_list_of_dict(rstlint_output)

    def print_violations(self):
        """Output formatted rule violation lines to console."""
        for violation in self.linting_violations:
            print(
                f'{violation["path"] !s}:{violation["line"] !s}:0: '
                f'{violation["message"] !s}',
            )


def _map_doc_paths_to_extra_lint_args(rst_doc_paths: t.Tuple[str]):
    generic_doc_indexes: t.List[int] = []
    sphinx_cli_doc_indexes: t.List[int] = []

    sphinx_cli_doc_path_prefix = 'docs/docsite/rst/cli/ansible'

    ignored_rst_substitutions = (
        'br',
    )
    ignored_in_tree_sphinx_directives = (
        'ansible-cmd-docs',
    )

    generic_doc_extra_rstlint_args: t.List[str] = [
        '--ignore-substitutions', ','.join(ignored_rst_substitutions),
    ]
    sphinx_cli_doc_extra_rstlint_args: t.List[str] = [
        *generic_doc_extra_rstlint_args,
        '--ignore-directives', ','.join(ignored_in_tree_sphinx_directives),
    ]

    for doc_index, doc_path in enumerate(rst_doc_paths):
        is_sphinx_cli_doc = doc_path.startswith(sphinx_cli_doc_path_prefix)
        target_indexes_list = (
            sphinx_cli_doc_indexes if is_sphinx_cli_doc
            else generic_doc_indexes
        )
        target_indexes_list.append(doc_index)

    generic_doc_paths_generator = (
        rst_doc_paths[doc_index] for doc_index in generic_doc_indexes
    )
    sphinx_cli_paths_generator = (
        rst_doc_paths[doc_index] for doc_index in sphinx_cli_doc_indexes
    )
    return zip(
        (generic_doc_extra_rstlint_args, sphinx_cli_doc_extra_rstlint_args),
        (generic_doc_paths_generator, sphinx_cli_paths_generator),
    )


def _lint_rst_docs(
        rst_doc_paths: t.Iterable[str],
        rstlint_extra_cli_args: t.List[str],
):
    unwinded_rst_doc_paths = tuple(rst_doc_paths)
    if not unwinded_rst_doc_paths:  # calling `rstcheck` not passing docs fails
        return

    rstlint_cmd = (
        sys.executable,
        '-c', 'import rstcheck; rstcheck.main();',
        '--report', 'warning',
        *rstlint_extra_cli_args,
        *unwinded_rst_doc_paths,
    )
    rstlint_cmd_text = _shlex_join(rstlint_cmd)

    try:
        rstlint_result = subprocess.run(
            rstlint_cmd,
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,  # Has a `text` alias since Python 3.7
        )
    except subprocess.CalledProcessError as proc_err:
        raise RuntimeError(
            'Oops... Got unexpected error output from '
            f'``{rstlint_cmd_text !s}``:\n\n{proc_err.stderr !s}',
        ) from proc_err

    if rstlint_result.stdout:
        raise RuntimeError(
            f'Oops... Got unexpected output from ``{rstlint_cmd_text !s}``:'
            f'\n\n{rstlint_result !s}',
        )

    if rstlint_result.stderr:
        raise RSTLintError(rstlint_result.stderr)


def _parse_to_list_of_dict(value):
    matched = []
    unmatched = []

    for line in value.splitlines():
        match = RSTLINT_VIOLATION_ENTRY_REGEX.search(line)

        if match:
            matched.append(match.groupdict())
        else:
            unmatched.append(line)

    if unmatched:
        unmatched_list = '\n'.join(unmatched)
        raise RuntimeError(
            f'Pattern "{RSTLINT_VIOLATION_ENTRY_REGEX !s}" did not match '
            f'the following lines:\n{unmatched_list !s}',
        )

    return matched


def main(*paths: str) -> int:
    """Linting check CLI entry point."""
    if not paths:
        raise ValueError('Expected a list of paths but got none.')

    unexpected_errors = []
    return_code = 0

    for extra_cli_args, doc_paths in _map_doc_paths_to_extra_lint_args(paths):
        try:
            _lint_rst_docs(doc_paths, extra_cli_args)
        except RSTLintError as rst_err:
            return_code += 1
            rst_err.print_violations()
        except RuntimeError as runtime_err:
            print(str(runtime_err), file=sys.stderr)
            unexpected_errors.append(runtime_err)

    if unexpected_errors:
        raise unexpected_errors[-1]

    return return_code


if __name__ == '__main__':
    input_paths = sys.argv[1:] or sys.stdin.read().splitlines()
    sys.exit(main(*input_paths))
