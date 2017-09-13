#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Verify the current Shippable run has the required number of jobs."""

from __future__ import absolute_import, print_function

# noinspection PyCompatibility
import argparse
import errno
import json
import os
import sys

from lib.http import (
    HttpClient,
)

from lib.util import (
    display,
    ApplicationError,
    ApplicationWarning,
    MissingEnvironmentVariable,
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

        try:
            run_id = os.environ['SHIPPABLE_BUILD_ID']
        except KeyError as ex:
            raise MissingEnvironmentVariable(ex.args[0])

        client = HttpClient(args)
        response = client.get('https://api.shippable.com/jobs?runIds=%s' % run_id)
        jobs = response.json()

        if not isinstance(jobs, list):
            raise ApplicationError(json.dumps(jobs, indent=4, sort_keys=True))

        if len(jobs) == 1:
            raise ApplicationError('Shippable run %s has only one job. Did you use the "Rebuild with SSH" option?' % run_id)
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

    parser.add_argument('-e', '--explain',
                        action='store_true',
                        help='explain commands that would be executed')

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
