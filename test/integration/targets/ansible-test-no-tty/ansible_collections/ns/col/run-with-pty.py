#!/usr/bin/env python
"""Run a command using a PTY."""

import pty
import sys

sys.exit(pty.spawn(sys.argv[1:]))
