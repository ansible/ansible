#!/usr/bin/env python
"""Prepends a relative timestamp to each input line from stdin and writes it to stdout."""

from __future__ import annotations

import sys
import time


def main():
    """Main program entry point."""
    start = time.time()

    sys.stdin.reconfigure(errors="surrogateescape")
    sys.stdout.reconfigure(errors="surrogateescape")

    for line in sys.stdin:
        seconds = time.time() - start
        sys.stdout.write("%02d:%02d %s" % (seconds // 60, seconds % 60, line))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
