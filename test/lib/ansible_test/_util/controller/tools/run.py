"""Run a subprocess while passing its stdout and stderr through a pipe to the current stdout."""
from __future__ import annotations

import subprocess
import sys


def main():
    """Main program entry point."""
    with subprocess.Popen(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        src = proc.stdout
        dst = sys.stdout.buffer

        for line in src:
            dst.write(line)
            dst.flush()

        return proc.wait()


if __name__ == '__main__':
    sys.exit(main())
