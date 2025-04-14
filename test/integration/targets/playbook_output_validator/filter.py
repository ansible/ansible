#!/usr/bin/env python

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('stdout', type=pathlib.Path)
    parser.add_argument('stderr', type=pathlib.Path)
    parser.add_argument('--match-stdout', type=re.compile, action='extend', default=[], help='matching regex patterns to save to stdout')
    parser.add_argument('--match-stderr', type=re.compile, action='extend', default=[], help='matching regex patterns to save to stderr')

    args = parser.parse_args()

    stdout_path: pathlib.Path = args.stdout
    stderr_path: pathlib.Path = args.stderr
    stdout_patterns: list[re.Pattern] = args.match_stdout
    stderr_patterns: list[re.Pattern] = args.match_stderr

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    ansible_test_temp_root = os.environ['JUNIT_TASK_RELATIVE_PATH']

    for line in sys.stdin:
        line = re.sub(r'\033\[[\d+;]+m', '', line)  # remove ANSI color sequences
        line = re.sub(re.escape(ansible_test_temp_root), 'ANSIBLE_TEST_TEMP_ROOT', line)

        if (match := re.search(r'^(?P<prefix>.*? => )(?P<json>\{.+})$', line)) and (data := json.loads(match.group('json'))):
            stdout_lines.append(f'{match.group("prefix")}{json.dumps(data, indent=4)}\n')
        elif re.search(r'^(?:PLAYBOOK:|PLAY|TASK) ', line):
            stdout_lines.append(line)
        elif re.search(r'^\[(?:DEPRECATION WARNING|WARNING|ERROR)]: .*$', line):
            stderr_lines.append(line)
        elif any(pattern.match(line) for pattern in stdout_patterns):
            stdout_lines.append(line)
        elif any(pattern.match(line) for pattern in stderr_patterns):
            stderr_lines.append(line)
        else:
            continue

    stdout_path.write_text(''.join(stdout_lines))
    stderr_path.write_text(''.join(stderr_lines))


if __name__ == '__main__':
    main()
