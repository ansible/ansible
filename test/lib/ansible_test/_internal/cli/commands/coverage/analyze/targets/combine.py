"""Command line parsing for the `coverage analyze targets combine` command."""

from __future__ import annotations

import argparse

from ......commands.coverage.analyze.targets.combine import (
    command_coverage_analyze_targets_combine,
    CoverageAnalyzeTargetsCombineConfig,
)

from .....environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_combine(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `coverage analyze targets combine` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'combine',
        parents=[parent],
        help='combine multiple aggregated coverage files',
    )

    parser.set_defaults(
        func=command_coverage_analyze_targets_combine,
        config=CoverageAnalyzeTargetsCombineConfig,
    )

    targets_combine = parser.add_argument_group('coverage arguments')

    targets_combine.add_argument(
        'input_file',
        nargs='+',
        help='input file to read aggregated coverage from',
    )

    targets_combine.add_argument(
        'output_file',
        help='output file to write aggregated coverage to',
    )

    add_environments(parser, completer, ControllerMode.ORIGIN, TargetMode.NO_TARGETS)  # coverage analyze targets combine
