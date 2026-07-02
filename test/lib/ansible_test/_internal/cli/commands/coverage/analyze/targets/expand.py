"""Command line parsing for the `coverage analyze targets expand` command."""

from __future__ import annotations

import argparse

from ......commands.coverage.analyze.targets.expand import (
    command_coverage_analyze_targets_expand,
    CoverageAnalyzeTargetsExpandConfig,
)

from .....environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_expand(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `coverage analyze targets expand` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'expand',
        parents=[parent],
        help='expand target names from integers in aggregated coverage',
    )

    parser.set_defaults(
        func=command_coverage_analyze_targets_expand,
        config=CoverageAnalyzeTargetsExpandConfig,
    )

    targets_expand = parser.add_argument_group(title='coverage arguments')

    targets_expand.add_argument(
        'input_file',
        help='input file to read aggregated coverage from',
    )

    targets_expand.add_argument(
        'output_file',
        help='output file to write expanded coverage to',
    )

    add_environments(parser, completer, ControllerMode.ORIGIN, TargetMode.NO_TARGETS)  # coverage analyze targets expand
