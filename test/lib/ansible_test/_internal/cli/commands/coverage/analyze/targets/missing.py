"""Command line parsing for the `coverage analyze targets missing` command."""
from __future__ import annotations

import argparse

from ......commands.coverage.analyze.targets.missing import (
    command_coverage_analyze_targets_missing,
    CoverageAnalyzeTargetsMissingConfig,
)

from .....environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_missing(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `coverage analyze targets missing` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'missing',
        parents=[parent],
        help='identify coverage in one file missing in another',
    )

    parser.set_defaults(
        func=command_coverage_analyze_targets_missing,
        config=CoverageAnalyzeTargetsMissingConfig,
    )

    targets_missing = parser.add_argument_group(title='coverage arguments')

    targets_missing.add_argument(
        'from_file',
        help='input file containing aggregated coverage',
    )

    targets_missing.add_argument(
        'to_file',
        help='input file containing aggregated coverage',
    )

    targets_missing.add_argument(
        'output_file',
        help='output file to write aggregated coverage to',
    )

    targets_missing.add_argument(
        '--only-gaps',
        action='store_true',
        help='report only arcs/lines not hit by any target',
    )

    targets_missing.add_argument(
        '--only-exists',
        action='store_true',
        help='limit results to files that exist',
    )

    add_environments(parser, completer, ControllerMode.ORIGIN, TargetMode.NO_TARGETS)  # coverage analyze targets missing
