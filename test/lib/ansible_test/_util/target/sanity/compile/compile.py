"""Python syntax checker with lint friendly output."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

ENCODING = 'utf-8'
ERRORS = 'replace'
Text = type(u'')


def main():
    """Main program entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        compile_source(path)


def compile_source(path):
    """Compile the specified source file, printing an error if one occurs."""
    with open(path, 'rb') as source_fd:
        source = source_fd.read()

    try:
        compile(source, path, 'exec', dont_inherit=True)
    except SyntaxError as ex:
        extype, message, lineno, offset = type(ex), ex.text, ex.lineno, ex.offset
    except BaseException as ex:  # pylint: disable=broad-except
        extype, message, lineno, offset = type(ex), str(ex), 0, 0
    else:
        return

    # In some situations offset can be None. This can happen for syntax errors on Python 2.6
    # (__future__ import following after a regular import).
    offset = offset or 0

    result = "%s:%d:%d: %s: %s" % (path, lineno, offset, extype.__name__, safe_message(message))

    if sys.version_info <= (3,):
        result = result.encode(ENCODING, ERRORS)

    print(result)


def safe_message(value):
    """Given an input value as text or bytes, return the first non-empty line as text, ensuring it can be round-tripped as UTF-8."""
    if isinstance(value, Text):
        value = value.encode(ENCODING, ERRORS)

    value = value.decode(ENCODING, ERRORS)
    value = value.strip().splitlines()[0].strip()

    return value


if __name__ == '__main__':
    main()
