"""Command line parsing for the `integration` command."""
from __future__ import annotations

import argparse
import collections.abc as c
import typing as t

from ....commands.integration.posix import (
    command_posix_integration,
)

from ....config import (
    PosixIntegrationConfig,
)

from ....target import (
    walk_posix_integration_targets,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_posix_integration(
    subparsers,
    parent: argparse.ArgumentParser,
    add_integration_common: c.Callable[[argparse.ArgumentParser], None],
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `integration` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'integration',
        parents=[parent],
        help='posix integration tests',
    )

    parser.set_defaults(
        func=command_posix_integration,
        targets_func=walk_posix_integration_targets,
        config=PosixIntegrationConfig,
    )

    posix_integration = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='integration test arguments'))

    add_integration_common(posix_integration)

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.POSIX_INTEGRATION)  # integration
