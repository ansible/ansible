"""PEP 517 in-tree backend package CLI interface."""

from sys import argv, exit

from ._cli import invoke_cli


if __name__ == '__main__':
    exit(invoke_cli(argv[1:]))
