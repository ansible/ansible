"""Command line parsing for the `env` command."""

from __future__ import annotations

import argparse

from ...commands.env import (
    EnvConfig,
    command_env,
)

from ..environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_env(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `env` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'env',
        parents=[parent],
        help='show information about the test environment',
    )

    parser.set_defaults(
        func=command_env,
        config=EnvConfig,
    )

    env = parser.add_argument_group(title='env arguments')

    env.add_argument(
        '--show',
        action='store_true',
        help='show environment on stdout',
    )

    env.add_argument(
        '--dump',
        action='store_true',
        help='dump environment to disk',
    )

    env.add_argument(
        '--list-files',
        action='store_true',
        help='list files on stdout',
    )

    env.add_argument(
        '--timeout',
        type=float,
        metavar='MINUTES',
        help='timeout for future ansible-test commands (0 clears)',
    )

    add_environments(parser, completer, ControllerMode.NO_DELEGATION, TargetMode.NO_TARGETS)  # env
