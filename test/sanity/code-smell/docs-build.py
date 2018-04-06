#!/usr/bin/env python

import os
import re
import subprocess


def main():
    base_dir = os.getcwd() + os.sep
    docs_dir = os.path.abspath('docs/docsite')
    cmd = ['make', 'singlehtmldocs']

    sphinx = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=docs_dir)
    stdout, stderr = sphinx.communicate()

    if sphinx.returncode != 0:
        raise subprocess.CalledProcessError(sphinx.returncode, cmd, output=stdout, stderr=stderr)

    with open('docs/docsite/rst_warnings', 'r') as warnings_fd:
        output = warnings_fd.read().strip()
        lines = output.splitlines()

    for line in lines:
        match = re.search('^(?P<path>[^:]+):((?P<line>[0-9]+):)?((?P<column>[0-9]+):)? (?P<level>WARNING|ERROR): (?P<message>.*)$', line)

        if not match:
            path = 'docs/docsite/rst/index.rst'
            lineno = 0
            column = 0
            level = 'unknown'
            message = line

            # surface unknown lines while filtering out known lines to avoid excessive output
            print('%s:%d:%d: %s: %s' % (path, lineno, column, level, message))
            continue

        path = match.group('path')
        lineno = int(match.group('line') or 0)
        column = int(match.group('column') or 0)
        level = match.group('level').lower()
        message = match.group('message')

        path = os.path.abspath(path)

        if path.startswith(base_dir):
            path = path[len(base_dir):]

        if level == 'warning':
            continue

        print('%s:%d:%d: %s: %s' % (path, lineno, column, level, message))


if __name__ == '__main__':
    main()
