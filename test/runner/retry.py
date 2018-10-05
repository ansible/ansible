#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Automatically retry failed commands."""

from __future__ import absolute_import, print_function

# noinspection PyCompatibility
import argparse
import errno
import os
import sys
import time

from lib.util import (
    display,
    raw_command,
    ApplicationError,
    ApplicationWarning,
    SubprocessError,
)

try:
    import argcomplete
except ImportError:
    argcomplete = None


def main():
    """Main program function."""
    try:
        args = parse_args()
        display.verbosity = args.verbosity
        display.color = args.color

        command = [args.command] + args.args

        for attempt in range(0, args.tries):
            if attempt > 0:
                time.sleep(args.sleep)

            try:
                raw_command(command, env=os.environ)
                return
            except SubprocessError as ex:
                display.error(ex)
    except ApplicationWarning as ex:
        display.warning(str(ex))
        exit(0)
    except ApplicationError as ex:
        display.error(str(ex))
        exit(1)
    except KeyboardInterrupt:
        exit(2)
    except IOError as ex:
        if ex.errno == errno.EPIPE:
            exit(3)
        raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--verbose',
                        dest='verbosity',
                        action='count',
                        default=0,
                        help='display more output')

    parser.add_argument('--color',
                        metavar='COLOR',
                        nargs='?',
                        help='generate color output: %(choices)s',
                        choices=('yes', 'no', 'auto'),
                        const='yes',
                        default='auto')

    parser.add_argument('--tries',
                        metavar='TRIES',
                        type=int,
                        default=3,
                        help='number of tries to execute command (default: %(default)s)')

    parser.add_argument('--sleep',
                        metavar='SECONDS',
                        type=int,
                        default=3,
                        help='seconds to sleep between tries (default: %(default)s)')

    parser.add_argument('command',
                        help='command to execute')

    parser.add_argument('args',
                        metavar='...',
                        nargs=argparse.REMAINDER,
                        help='optional arguments for command')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if args.color == 'yes':
        args.color = True
    elif args.color == 'no':
        args.color = False
    elif 'SHIPPABLE' in os.environ:
        args.color = True
    else:
        args.color = sys.stdout.isatty()

    return args


if __name__ == '__main__':
    main()
