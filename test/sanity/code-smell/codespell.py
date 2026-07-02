"""Check for common misspelled words using codespell."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

import typing as t


def main() -> None:
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    ignore_words_lines = (pathlib.Path(__file__).parent / 'codespell' / 'ignore-words.txt').read_text().splitlines()
    ignore_words = [re.split(r'\s*#', line, maxsplit=1)[0] for line in ignore_words_lines]

    quiet_level = (
        32  # don't print configuration file
        + 16  # don't print the list of fixed files
        + 4  # omit warnings about automatic fixes that were disabled in the dictionary
        + 2  # disable warnings about binary files
        + 1  # disable warnings about wrong encoding
    )

    paths = [path for path in paths if path != 'test/sanity/ignore.txt']

    with tempfile.NamedTemporaryFile(mode='wt') as ignore_words_temp_file:
        ignore_words_temp_file.write('\n'.join(ignore_words))
        ignore_words_temp_file.flush()

        cmd = [
            sys.executable,
            '-m',
            'codespell_lib',
            '--disable-colors',
            '--builtin',
            'clear',  # minimize false positives
            '--quiet-level',
            str(quiet_level),
            '--ignore-words',
            ignore_words_temp_file.name,
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

    if process.returncode not in (0, 65):
        print(f'Unexpected return code: {process.returncode}')
        sys.exit(1)

    pattern = re.compile(r'^(?P<path>[^:]*):(?P<line>[0-9]+): (?P<left>.*) ==> (?P<right>.*)$')
    matches = parse_to_list_of_dict(pattern, stdout)
    results: list[str] = []

    for match in matches:
        path, line_num_str, left, right = match['path'], match['line'], match['left'], match['right']
        line_num = int(line_num_str)

        try:
            line = pathlib.Path(path).read_text().splitlines()[line_num - 1]
            col_num = line.index(left) + 1
        except UnicodeDecodeError:
            col_num = 0

        if len(left) <= 3 and pathlib.Path(path).suffix == '.py':
            continue  # ignore short words in Python files, as they're likely just short variable names

        code = re.sub('[^a-zA-Z]', '_', left)

        results.append(f"{path}:{line_num}:{col_num}: {code}: {left} ==> {right}")

    if results:
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
