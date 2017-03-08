#!/usr/bin/env python
"""Python syntax checker with lint friendly output."""

import os
import parser
import re
import sys


def main():
    paths, verbose, skip_patterns = parse_options()
    paths = filter_paths(paths, skip_patterns)
    check(paths, verbose)


def parse_options():
    paths = []
    skip_patterns = []
    option = None
    verbose = False
    valid_options = [
        '-x',
        '-v',
    ]

    for arg in sys.argv[1:]:
        if option == '-x':
            skip_patterns.append(re.compile(arg))
            option = None
        elif arg.startswith('-'):
            if arg not in valid_options:
                raise Exception('Unknown Option: %s' % arg)
            if arg == '-v':
                verbose = True
            else:
                option = arg
        else:
            paths.append(arg)

    if option:
        raise Exception('Incomplete Option: %s' % option)

    return paths, verbose, skip_patterns


def filter_paths(paths, skip_patterns):
    if not paths:
        paths = ['.']

    candidates = paths
    paths = []

    for candidate in candidates:
        if os.path.isdir(candidate):
            for root, directories, files in os.walk(candidate):
                remove = []

                for directory in directories:
                    if directory.startswith('.'):
                        remove.append(directory)

                for path in remove:
                    directories.remove(path)

                for f in files:
                    if f.endswith('.py'):
                        paths.append(os.path.join(root, f))
        else:
            paths.append(candidate)

    final_paths = []

    for path in sorted(paths):
        skip = False

        for skip_pattern in skip_patterns:
            if skip_pattern.search(path):
                skip = True
                break

        if skip:
            continue

        final_paths.append(path)

    return final_paths


def check(paths, verbose):
    status = 0

    for path in paths:
        if verbose:
            sys.stderr.write('%s\n' % path)
            sys.stderr.flush()

        source_fd = open(path, 'r')

        try:
            source = source_fd.read()
        finally:
            source_fd.close()

        try:
            parser.suite(source)
        except SyntaxError:
            ex_type, ex, ex_traceback = sys.exc_info()
            status = 1
            message = ex.text.splitlines()[0].strip()
            sys.stdout.write("%s:%d:%d: SyntaxError: %s\n" % (path, ex.lineno, ex.offset, message))
            sys.stdout.flush()

    sys.exit(status)


if __name__ == '__main__':
    main()
