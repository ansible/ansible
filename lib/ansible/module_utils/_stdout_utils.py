"""Utils for supplying bytes to stdout."""

from __future__ import annotations

import sys


__all__ = ('write_bytes_to_stdout', )


def write_bytes_to_stdout(*args, **kwargs):
    """Write bytes to stdout and flush immediately."""
    sys.stdout.buffer.write(*args, **kwargs)
    sys.stdout.flush()
