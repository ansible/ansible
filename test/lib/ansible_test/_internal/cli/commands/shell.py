"""Command line parsing for the `shell` command."""
from __future__ import annotations

import argparse

from ...commands.shell import (
    command_shell,
)

from ...config import (
    ShellConfig,
)

from ..environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_shell(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `shell` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'shell',
        parents=[parent],
        help='open an interactive shell',
    )

    parser.set_defaults(
        func=command_shell,
        config=ShellConfig,
    )

    shell = parser.add_argument_group(title='shell arguments')

    shell.add_argument(
        'cmd',
        nargs='*',
        help='run the specified command',
    )

    shell.add_argument(
        '--raw',
        action='store_true',
        help='direct to shell with no setup',
    )

    shell.add_argument(
        '--export',
        metavar='PATH',
        help='export inventory instead of opening a shell',
    )

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.SHELL)  # shell
