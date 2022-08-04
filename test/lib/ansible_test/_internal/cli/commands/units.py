"""Command line parsing for the `units` command."""
from __future__ import annotations

import argparse

from ...config import (
    UnitsConfig,
)

from ...commands.units import (
    command_units,
)

from ...target import (
    walk_units_targets,
)

from ..environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_units(
        subparsers,
        parent: argparse.ArgumentParser,
        completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `units` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'units',
        parents=[parent],
        help='unit tests',
    )

    parser.set_defaults(
        func=command_units,
        targets_func=walk_units_targets,
        config=UnitsConfig,
    )

    units = parser.add_argument_group(title='unit test arguments')

    units.add_argument(
        '--collect-only',
        action='store_true',
        help='collect tests but do not execute them',
    )

    units.add_argument(
        '--num-workers',
        metavar='INT',
        type=int,
        help='number of workers to use (default: auto)',
    )

    units.add_argument(
        '--requirements-mode',
        choices=('only', 'skip'),
        help=argparse.SUPPRESS,
    )

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.UNITS)  # units
