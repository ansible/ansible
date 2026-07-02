"""Command line parsing for the `coverage analyze targets generate` command."""

from __future__ import annotations

import argparse

from ......commands.coverage.analyze.targets.generate import (
    command_coverage_analyze_targets_generate,
    CoverageAnalyzeTargetsGenerateConfig,
)

from .....environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_generate(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `coverage analyze targets generate` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'generate',
        parents=[parent],
        help='aggregate coverage by integration test target',
    )

    parser.set_defaults(
        func=command_coverage_analyze_targets_generate,
        config=CoverageAnalyzeTargetsGenerateConfig,
    )

    targets_generate = parser.add_argument_group(title='coverage arguments')

    targets_generate.add_argument(
        'input_dir',
        nargs='?',
        help='directory to read coverage from',
    )

    targets_generate.add_argument(
        'output_file',
        help='output file for aggregated coverage',
    )

    add_environments(parser, completer, ControllerMode.ORIGIN, TargetMode.NO_TARGETS)  # coverage analyze targets generate
