"""Command line parsing for all commands."""

from __future__ import annotations

import argparse
import functools
import sys

from ...util import (
    display,
)

from ..completers import (
    complete_target,
    register_completer,
)

from ..environments import (
    CompositeActionCompletionFinder,
)

from .coverage import (
    do_coverage,
)

from .env import (
    do_env,
)

from .integration import (
    do_integration,
)

from .sanity import (
    do_sanity,
)

from .shell import (
    do_shell,
)

from .units import (
    do_units,
)


def do_commands(
    parent: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for all commands."""
    common = argparse.ArgumentParser(add_help=False)

    common.add_argument(
        '-e',
        '--explain',
        action='store_true',
        help='explain commands that would be executed',
    )

    common.add_argument(
        '-v',
        '--verbose',
        dest='verbosity',
        action='count',
        default=0,
        help='display more output',
    )

    common.add_argument(
        '--color',
        metavar='COLOR',
        nargs='?',
        help='generate color output: yes, no, auto',
        const='yes',
        default='auto',
        type=color,
    )

    common.add_argument(
        '--debug',
        action='store_true',
        help='run ansible commands in debug mode',
    )

    common.add_argument(
        '--truncate',
        dest='truncate',
        metavar='COLUMNS',
        type=int,
        default=display.columns,
        help='truncate some long output (0=disabled) (default: auto)',
    )

    common.add_argument(
        '--display-traceback',
        dest='display_traceback',
        metavar='TB',
        type=str,
        default='never',
        choices=('error', 'warning', 'deprecated', 'always', 'never'),
        help='set ANSIBLE_DISPLAY_TRACEBACK (%(choices)s) (default: %(default)s)',
    )

    common.add_argument(
        '--redact',
        dest='redact',
        action='store_true',
        default=True,
        help=argparse.SUPPRESS,  # kept for backwards compatibility, but no point in advertising since it's the default
    )

    common.add_argument(
        '--no-redact',
        dest='redact',
        action='store_false',
        default=False,
        help='show sensitive values in output',
    )

    test = argparse.ArgumentParser(add_help=False, parents=[common])

    testing = test.add_argument_group(title='common testing arguments')

    register_completer(testing.add_argument(
        'include',
        metavar='TARGET',
        nargs='*',
        help='test the specified target',
    ), functools.partial(complete_target, completer))

    register_completer(testing.add_argument(
        '--include',
        metavar='TARGET',
        action='append',
        help='include the specified target',
    ), functools.partial(complete_target, completer))

    register_completer(testing.add_argument(
        '--exclude',
        metavar='TARGET',
        action='append',
        help='exclude the specified target',
    ), functools.partial(complete_target, completer))

    register_completer(testing.add_argument(
        '--require',
        metavar='TARGET',
        action='append',
        help='require the specified target',
    ), functools.partial(complete_target, completer))

    testing.add_argument(
        '--coverage',
        action='store_true',
        help='analyze code coverage when running tests',
    )

    testing.add_argument(
        '--coverage-check',
        action='store_true',
        help='only verify code coverage can be enabled',
    )

    testing.add_argument(
        '--base-branch',
        metavar='BRANCH',
        help='base branch used for change detection',
    )

    testing.add_argument(
        '--changed',
        action='store_true',
        help='limit targets based on changes',
    )

    changes = test.add_argument_group(title='change detection arguments')

    changes.add_argument(
        '--tracked',
        action='store_true',
        help=argparse.SUPPRESS,
    )

    changes.add_argument(
        '--untracked',
        action='store_true',
        help='include untracked files',
    )

    changes.add_argument(
        '--ignore-committed',
        dest='committed',
        action='store_false',
        help='exclude committed files',
    )

    changes.add_argument(
        '--ignore-staged',
        dest='staged',
        action='store_false',
        help='exclude staged files',
    )

    changes.add_argument(
        '--ignore-unstaged',
        dest='unstaged',
        action='store_false',
        help='exclude unstaged files',
    )

    changes.add_argument(
        '--changed-from',
        metavar='PATH',
        help=argparse.SUPPRESS,
    )

    changes.add_argument(
        '--changed-path',
        metavar='PATH',
        action='append',
        help=argparse.SUPPRESS,
    )

    subparsers = parent.add_subparsers(metavar='COMMAND', required=True)

    do_coverage(subparsers, common, completer)
    do_env(subparsers, common, completer)
    do_shell(subparsers, common, completer)

    do_integration(subparsers, test, completer)
    do_sanity(subparsers, test, completer)
    do_units(subparsers, test, completer)


def color(value: str) -> bool:
    """Strict converter for color option."""
    if value == 'yes':
        return True

    if value == 'no':
        return False

    if value == 'auto':
        return sys.stdout.isatty()

    raise argparse.ArgumentTypeError(f"invalid choice: '{value}' (choose from 'yes', 'no', 'auto')")
