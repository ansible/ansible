#!/usr/bin/env python
"""Run a command using a PTY."""
from __future__ import annotations

import sys

if sys.version_info < (3, 10):
    import vendored_pty as pty
else:
    import pty

sys.exit(1 if pty.spawn(sys.argv[1:]) else 0)
