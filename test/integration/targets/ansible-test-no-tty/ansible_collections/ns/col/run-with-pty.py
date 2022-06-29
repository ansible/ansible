#!/usr/bin/env python
"""Run a command using a PTY."""

import pty
import sys

sys.exit(1 if pty.spawn(sys.argv[1:]) else 0)
