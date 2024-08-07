"""Sanity test for Markdown files."""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import typing as t


def main() -> None:
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    cmd = [
        sys.executable,
        '-m', 'pymarkdown',
        '--config', pathlib.Path(__file__).parent / 'pymarkdown.config.json',
        '--strict-config',
        'scan',
    ] + paths

    process = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        text=True,
    )

    if process.stderr:
        print(process.stderr.strip(), file=sys.stderr)
        sys.exit(1)

    if not (stdout := process.stdout.strip()):
        return

    pattern = re.compile(r'^(?P<path_line_column>[^:]*:[0-9]+:[0-9]+): (?P<code>[^:]*): (?P<message>.*) \((?P<aliases>.*)\)$')
    matches = parse_to_list_of_dict(pattern, stdout)
    results = [f"{match['path_line_column']}: {match['aliases'].split(', ')[0]}: {match['message']}" for match in matches]

    print('\n'.join(results))


def parse_to_list_of_dict(pattern: re.Pattern, value: str) -> list[dict[str, t.Any]]:
    matched = []
    unmatched = []

    for line in value.splitlines():
        match = re.search(pattern, line)

        if match:
            matched.append(match.groupdict())
        else:
            unmatched.append(line)

    if unmatched:
        raise Exception(f'Pattern {pattern!r} did not match values:\n' + '\n'.join(unmatched))

    return matched


if __name__ == '__main__':
    main()
