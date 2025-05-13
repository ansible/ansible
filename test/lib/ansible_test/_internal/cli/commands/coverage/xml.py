"""Command line parsing for the `coverage xml` command."""

from __future__ import annotations

import argparse
import collections.abc as c
import typing as t

from ....commands.coverage.xml import (
    command_coverage_xml,
    CoverageXmlConfig,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_xml(
    subparsers,
    parent: argparse.ArgumentParser,
    add_coverage_common: c.Callable[[argparse.ArgumentParser], None],
    completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for the `coverage xml` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'xml',
        parents=[parent],
        help='generate xml coverage report',
    )

    parser.set_defaults(
        func=command_coverage_xml,
        config=CoverageXmlConfig,
    )

    coverage_combine = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='coverage arguments'))

    add_coverage_common(coverage_combine)

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.NO_TARGETS)  # coverage xml
