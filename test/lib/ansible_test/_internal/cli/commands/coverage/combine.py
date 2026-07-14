"""Command line parsing for the `coverage combine` command."""

from __future__ import annotations

import argparse
import collections.abc as c
import typing as t

from ....commands.coverage.combine import (
    command_coverage_combine,
    CoverageCombineConfig,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_combine(
    subparsers,
    parent: argparse.ArgumentParser,
    add_coverage_common: c.Callable[[argparse.ArgumentParser], None],
    completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for the `coverage combine` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'combine',
        parents=[parent],
        help='combine coverage data and rewrite remote paths',
    )

    parser.set_defaults(
        func=command_coverage_combine,
        config=CoverageCombineConfig,
    )

    coverage_combine = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='coverage arguments'))

    add_coverage_common(coverage_combine)

    coverage_combine.add_argument(
        '--export',
        metavar='DIR',
        help='directory to export combined coverage files to',
    )

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.NO_TARGETS)  # coverage combine
