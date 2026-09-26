#!/usr/bin/env python
"""Run a command using a PTY."""
from __future__ import annotations

import sys
import pty

sys.exit(1 if pty.spawn(sys.argv[1:]) else 0)
