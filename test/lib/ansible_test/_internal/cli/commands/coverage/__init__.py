"""Command line parsing for all `coverage` commands."""
from __future__ import annotations

import argparse

from ....commands.coverage import (
    COVERAGE_GROUPS,
)

from ...environments import (
    CompositeActionCompletionFinder,
)

from .analyze import (
    do_analyze,
)

from .combine import (
    do_combine,
)

from .erase import (
    do_erase,
)

from .html import (
    do_html,
)

from .report import (
    do_report,
)

from .xml import (
    do_xml,
)


def do_coverage(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for all `coverage` commands."""
    coverage_common = argparse.ArgumentParser(add_help=False, parents=[parent])

    parser = subparsers.add_parser(
        'coverage',
        help='code coverage management and reporting',
    )

    coverage_subparsers = parser.add_subparsers(metavar='COMMAND', required=True)

    do_analyze(coverage_subparsers, coverage_common, completer)
    do_erase(coverage_subparsers, coverage_common, completer)

    do_combine(coverage_subparsers, parent, add_coverage_common, completer)
    do_report(coverage_subparsers, parent, add_coverage_common, completer)
    do_html(coverage_subparsers, parent, add_coverage_common, completer)
    do_xml(coverage_subparsers, parent, add_coverage_common, completer)


def add_coverage_common(
    parser: argparse.ArgumentParser,
):
    """Add common coverage arguments."""
    parser.add_argument(
        '--group-by',
        metavar='GROUP',
        action='append',
        choices=COVERAGE_GROUPS,
        help='group output by: %s' % ', '.join(COVERAGE_GROUPS),
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='include all python/powershell source files',
    )

    parser.add_argument(
        '--stub',
        action='store_true',
        help='generate empty report of all python/powershell source files',
    )
