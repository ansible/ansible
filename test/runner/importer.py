#!/usr/bin/env python
"""Import the given python module(s) and report error(s) encountered."""

from __future__ import absolute_import, print_function

import imp
import os
import sys
import traceback


def main():
    """Main program function."""
    base_dir = os.getcwd()
    messages = set()

    for path in sys.argv[1:]:
        try:
            with open(path, 'r') as module_fd:
                imp.load_module('module_import_test', module_fd, os.path.abspath(path), ('.py', 'r', imp.PY_SOURCE))
        except Exception as ex:  # pylint: disable=locally-disabled, broad-except
            exc_type, _, exc_tb = sys.exc_info()
            message = str(ex)
            results = list(reversed(traceback.extract_tb(exc_tb)))
            source = None
            line = 0
            offset = 0

            for result in results:
                if result[0].startswith(base_dir):
                    source = result[0][len(base_dir) + 1:].replace('test/runner/import/', '')
                    line = result[1] or 0
                    break

            if not source:
                # If none of our source files are found in the traceback, report the file we were testing.
                # I haven't been able to come up with a test case that encounters this issue yet.
                source = path
                message += ' (in %s:%d)' % (results[-1][0], results[-1][1] or 0)
            elif isinstance(ex, SyntaxError):
                if ex.filename.endswith(path):  # pylint: disable=locally-disabled, no-member
                    # A SyntaxError in the source we're importing will have the correct path, line and offset.
                    # However, the traceback will report the path to this importer.py script instead.
                    # We'll use the details from the SyntaxError in this case, as it's more accurate.
                    source = path
                    line = ex.lineno or 0  # pylint: disable=locally-disabled, no-member
                    offset = ex.offset or 0  # pylint: disable=locally-disabled, no-member
                    message = str(ex)

                    # Hack to remove the filename and line number from the message, if present.
                    message = message.replace(' (%s, line %d)' % (os.path.basename(path), line), '')

            error = '%s:%d:%d: %s: %s' % (source, line, offset, exc_type.__name__, message)

            if error not in messages:
                messages.add(error)
                print(error)

    if messages:
        exit(10)

if __name__ == '__main__':
    main()
