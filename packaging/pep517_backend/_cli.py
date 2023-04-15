"""PEP 517 in-tree backend package CLI definition."""

import typing as t
from argparse import ArgumentParser

from ._manpage_generation import generate_manpages


def invoke_cli(argv: t.Sequence[str]) -> int:
    arg_parser = ArgumentParser(prog=f'python -m {__package__}')
    arg_parser.add_argument('arg', choices=('generate-manpages', ))
    arg_parser.parse_args(argv)

    generate_manpages('docs/man/man1/')
    return 0
