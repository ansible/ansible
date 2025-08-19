"""Command line parsing for the `windows-debug` command."""

from __future__ import annotations

import argparse

from ....commands.debug.pwsh import (
    command_pwsh_debug,
)

from ....config import (
    PwshDebugConfig,
)

from ...environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_pwsh_debug(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `pwsh-debug` command."""
    help = 'open an interactive shell for debugging PowerShell modules'
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'pwsh-debug',
        parents=[parent],
        description=help,
        help=help,
    )

    parser.add_argument(
        '--wait-at-entry',
        action='store_true',
        help=(
            'wait for the debugger to attach before executing any PowerShell module, only for PowerShell 7 targets '
            'only as PowerShell 5 targets will always wait for the debugger to attach'
        ),
    )

    parser.set_defaults(
        func=command_pwsh_debug,
        config=PwshDebugConfig,
    )

    add_environments(parser, completer, ControllerMode.NO_DELEGATION, TargetMode.NO_TARGETS)  # pwsh-debug
