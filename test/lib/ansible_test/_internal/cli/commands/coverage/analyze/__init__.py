"""Command line parsing for all `coverage analyze` commands."""
from __future__ import annotations

import argparse

from .targets import (
    do_targets,
)

from ....environments import (
    CompositeActionCompletionFinder,
)


def do_analyze(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for all `coverage analyze` commands."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'analyze',
        help='analyze collected coverage data',
    )

    analyze_subparsers = parser.add_subparsers(metavar='COMMAND', required=True)

    do_targets(analyze_subparsers, parent, completer)
