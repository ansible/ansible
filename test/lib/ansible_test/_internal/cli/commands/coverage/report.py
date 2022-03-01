"""Command line parsing for the `coverage report` command."""
from __future__ import annotations

import argparse
import typing as t

from ....commands.coverage.report import (
    command_coverage_report,
    CoverageReportConfig,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_report(
        subparsers,
        parent,  # type: argparse.ArgumentParser
        add_coverage_common,  # type: t.Callable[[argparse.ArgumentParser], None]
        completer,  # type: CompositeActionCompletionFinder
):  # type: (...) -> None
    """Command line parsing for the `coverage report` command."""
    parser = subparsers.add_parser(
        'report',
        parents=[parent],
        help='generate console coverage report',
    )  # type: argparse.ArgumentParser

    parser.set_defaults(
        func=command_coverage_report,
        config=CoverageReportConfig,
    )

    coverage_report = t.cast(argparse.ArgumentParser, parser.add_argument_group('coverage arguments'))

    add_coverage_common(coverage_report)

    coverage_report.add_argument(
        '--show-missing',
        action='store_true',
        help='show line numbers of statements not executed',
    )

    coverage_report.add_argument(
        '--include',
        metavar='PAT[,...]',
        help='only include paths that match a pattern (accepts quoted shell wildcards)',
    )

    coverage_report.add_argument(
        '--omit',
        metavar='PAT[,...]',
        help='omit paths that match a pattern (accepts quoted shell wildcards)',
    )

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.NO_TARGETS)  # coverage report
