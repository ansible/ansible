"""Command line parsing for the `coverage html` command."""
from __future__ import annotations

import argparse
import collections.abc as c
import typing as t

from ....commands.coverage.html import (
    command_coverage_html,
    CoverageHtmlConfig,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_html(
        subparsers,
        parent: argparse.ArgumentParser,
        add_coverage_common: c.Callable[[argparse.ArgumentParser], None],
        completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for the `coverage html` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'html',
        parents=[parent],
        help='generate html coverage report',
    )

    parser.set_defaults(
        func=command_coverage_html,
        config=CoverageHtmlConfig,
    )

    coverage_combine = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='coverage arguments'))

    add_coverage_common(coverage_combine)

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.NO_TARGETS)  # coverage html
