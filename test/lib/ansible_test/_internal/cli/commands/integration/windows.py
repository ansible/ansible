"""Command line parsing for the `windows-integration` command."""
from __future__ import annotations

import argparse
import typing as t

from ....commands.integration.windows import (
    command_windows_integration,
)

from ....config import (
    WindowsIntegrationConfig,
)

from ....target import (
    walk_windows_integration_targets,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_windows_integration(
        subparsers,
        parent,  # type: argparse.ArgumentParser
        add_integration_common,  # type: t.Callable[[argparse.ArgumentParser], None]
        completer,  # type: CompositeActionCompletionFinder
):
    """Command line parsing for the `windows-integration` command."""
    parser = subparsers.add_parser(
        'windows-integration',
        parents=[parent],
        help='windows integration tests',
    )  # type: argparse.ArgumentParser

    parser.set_defaults(
        func=command_windows_integration,
        targets_func=walk_windows_integration_targets,
        config=WindowsIntegrationConfig,
    )

    windows_integration = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='windows integration test arguments'))

    add_integration_common(windows_integration)

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.WINDOWS_INTEGRATION)  # windows-integration
