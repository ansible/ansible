"""Command line parsing for all debug commands."""

from __future__ import annotations

import argparse

from ...environments import (
    CompositeActionCompletionFinder,
)

from .pwsh import (
    do_pwsh_debug,
)


def do_debug(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for all debug commands."""
    parser = argparse.ArgumentParser(
        add_help=False,
        parents=[parent],
    )

    parser.add_argument(
        'cmd',
        nargs=argparse.REMAINDER,
        help='run the specified command in the debug session instead of opening a shell',
    )

    parser.add_argument(
        '--limit',
        metavar='OPT',
        help='limit inventory hosts to an additional pattern, a debug session must only target a single host',
    )

    parser.add_argument(
        '--inventory', '--inventory-file',
        metavar='OPT',
        help='inventory source to use for debugging',
    )

    do_pwsh_debug(subparsers, parser, completer)
