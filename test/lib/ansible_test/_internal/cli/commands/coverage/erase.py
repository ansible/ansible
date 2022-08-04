"""Command line parsing for the `coverage erase` command."""
from __future__ import annotations

import argparse

from ....commands.coverage.erase import (
    command_coverage_erase,
    CoverageEraseConfig,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_erase(
        subparsers,
        parent: argparse.ArgumentParser,
        completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for the `coverage erase` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'erase',
        parents=[parent],
        help='erase coverage data files',
    )

    parser.set_defaults(
        func=command_coverage_erase,
        config=CoverageEraseConfig,
    )

    add_environments(parser, completer, ControllerMode.ORIGIN, TargetMode.NO_TARGETS)  # coverage erase
