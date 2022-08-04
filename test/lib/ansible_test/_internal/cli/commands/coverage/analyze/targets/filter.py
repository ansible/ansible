"""Command line parsing for the `coverage analyze targets filter` command."""
from __future__ import annotations

import argparse

from ......commands.coverage.analyze.targets.filter import (
    command_coverage_analyze_targets_filter,
    CoverageAnalyzeTargetsFilterConfig,
)

from .....environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_filter(
        subparsers,
        parent: argparse.ArgumentParser,
        completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `coverage analyze targets filter` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'filter',
        parents=[parent],
        help='filter aggregated coverage data',
    )

    parser.set_defaults(
        func=command_coverage_analyze_targets_filter,
        config=CoverageAnalyzeTargetsFilterConfig,
    )

    targets_filter = parser.add_argument_group(title='coverage arguments')

    targets_filter.add_argument(
        'input_file',
        help='input file to read aggregated coverage from',
    )

    targets_filter.add_argument(
        'output_file',
        help='output file to write expanded coverage to',
    )

    targets_filter.add_argument(
        '--include-target',
        metavar='TGT',
        dest='include_targets',
        action='append',
        help='include the specified targets',
    )

    targets_filter.add_argument(
        '--exclude-target',
        metavar='TGT',
        dest='exclude_targets',
        action='append',
        help='exclude the specified targets',
    )

    targets_filter.add_argument(
        '--include-path',
        metavar='REGEX',
        help='include paths matching the given regex',
    )

    targets_filter.add_argument(
        '--exclude-path',
        metavar='REGEX',
        help='exclude paths matching the given regex',
    )

    add_environments(parser, completer, ControllerMode.ORIGIN, TargetMode.NO_TARGETS)  # coverage analyze targets filter
