#!/usr/bin/env python
"""Run a command using a PTY."""

import os
import pty
import sys

sys.exit(os.waitstatus_to_exitcode(pty.spawn(sys.argv[1:])))
