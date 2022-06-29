#!/usr/bin/env python
"""Assert no TTY is available."""

import sys

assert not sys.stdin.isatty()
assert not sys.stdout.isatty()
assert not sys.stderr.isatty()
