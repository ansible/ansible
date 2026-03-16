"""Command line parsing for the `sanity` command."""

from __future__ import annotations

import argparse

from ...config import (
    data_context,
    SanityConfig,
)

from ...commands.sanity import (
    command_sanity,
    sanity_get_tests,
)

from ...target import (
    walk_sanity_targets,
)

from ..environments import (
    CompositeActionCompletionFinder,
    ControllerMode,
    TargetMode,
    add_environments,
)


def do_sanity(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for the `sanity` command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        'sanity',
        parents=[parent],
        help='sanity tests',
    )

    parser.set_defaults(
        func=command_sanity,
        targets_func=walk_sanity_targets,
        config=SanityConfig,
    )

    sanity = parser.add_argument_group(title='sanity test arguments')

    sanity.add_argument(
        '--test',
        metavar='TEST',
        action='append',
        choices=[test.name for test in sanity_get_tests()],
        help='tests to run',
    )

    sanity.add_argument(
        '--skip-test',
        metavar='TEST',
        action='append',
        choices=[test.name for test in sanity_get_tests()],
        help='tests to skip',
    )

    sanity.add_argument(
        '--allow-disabled',
        action='store_true',
        help='allow tests to run which are disabled by default',
    )

    sanity.add_argument(
        '--list-tests',
        action='store_true',
        help='list available tests',
    )

    sanity.add_argument(
        '--enable-optional-errors',
        action='store_true',
        help='enable optional errors',
    )

    sanity.add_argument(
        '--lint',
        action='store_true',
        help='write lint output to stdout, everything else stderr',
    )

    sanity.add_argument(
        '--junit',
        action='store_true',
        help='write test failures to junit xml files',
    )

    sanity.add_argument(
        '--failure-ok',
        action='store_true',
        help='exit successfully on failed tests after saving results',
    )

    sanity.add_argument(
        '--prime-venvs',
        action='store_true',
        help='prepare virtual environments without running tests',
    )

    if data_context().content.is_ansible:
        sanity.add_argument(
            '--fix',
            action='store_true',
            help='fix issues when possible instead of reporting them',
        )

    add_environments(parser, completer, ControllerMode.DELEGATED, TargetMode.SANITY)  # sanity
