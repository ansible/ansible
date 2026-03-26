#!/usr/bin/env python

from __future__ import annotations

import sys
import pathlib


def main():
    pathlib.Path(sys.argv[1]).write_text("CORRUPTED")
    sys.exit('intentional editor failure')


if __name__ == '__main__':
    main()
