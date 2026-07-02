"""Command line parsing for all integration commands."""

from __future__ import annotations

import argparse

from ...completers import (
    complete_target,
    register_completer,
)

from ...environments import (
    CompositeActionCompletionFinder,
)

from .network import (
    do_network_integration,
)

from .posix import (
    do_posix_integration,
)

from .windows import (
    do_windows_integration,
)


def do_integration(
    subparsers,
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
):
    """Command line parsing for all integration commands."""
    parser = argparse.ArgumentParser(
        add_help=False,
        parents=[parent],
    )

    do_posix_integration(subparsers, parser, add_integration_common, completer)
    do_network_integration(subparsers, parser, add_integration_common, completer)
    do_windows_integration(subparsers, parser, add_integration_common, completer)


def add_integration_common(
    parser: argparse.ArgumentParser,
):
    """Add common integration arguments."""
    register_completer(parser.add_argument(
        '--start-at',
        metavar='TARGET',
        help='start at the specified target',
    ), complete_target)

    parser.add_argument(
        '--start-at-task',
        metavar='TASK',
        help='start at the specified task',
    )

    parser.add_argument(
        '--tags',
        metavar='TAGS',
        help='only run plays and tasks tagged with these values',
    )

    parser.add_argument(
        '--skip-tags',
        metavar='TAGS',
        help='only run plays and tasks whose tags do not match these values',
    )

    parser.add_argument(
        '--diff',
        action='store_true',
        help='show diff output',
    )

    parser.add_argument(
        '--allow-destructive',
        action='store_true',
        help='allow destructive tests',
    )

    parser.add_argument(
        '--allow-root',
        action='store_true',
        help='allow tests requiring root when not root',
    )

    parser.add_argument(
        '--allow-disabled',
        action='store_true',
        help='allow tests which have been marked as disabled',
    )

    parser.add_argument(
        '--allow-unstable',
        action='store_true',
        help='allow tests which have been marked as unstable',
    )

    parser.add_argument(
        '--allow-unstable-changed',
        action='store_true',
        help='allow tests which have been marked as unstable when focused changes are detected',
    )

    parser.add_argument(
        '--allow-unsupported',
        action='store_true',
        help='allow tests which have been marked as unsupported',
    )

    parser.add_argument(
        '--retry-on-error',
        action='store_true',
        help='retry failed test with increased verbosity',
    )

    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='continue after failed test',
    )

    parser.add_argument(
        '--debug-strategy',
        action='store_true',
        help='run test playbooks using the debug strategy',
    )

    parser.add_argument(
        '--changed-all-target',
        metavar='TARGET',
        default='all',
        help='target to run when all tests are needed',
    )

    parser.add_argument(
        '--changed-all-mode',
        metavar='MODE',
        choices=('default', 'include', 'exclude'),
        help='include/exclude behavior with --changed-all-target: %(choices)s',
    )

    parser.add_argument(
        '--list-targets',
        action='store_true',
        help='list matching targets instead of running tests',
    )

    parser.add_argument(
        '--no-temp-workdir',
        action='store_true',
        help='do not run tests from a temporary directory (use only for verifying broken tests)',
    )

    parser.add_argument(
        '--no-temp-unicode',
        action='store_true',
        help='avoid unicode characters in temporary directory (use only for verifying broken tests)',
    )
