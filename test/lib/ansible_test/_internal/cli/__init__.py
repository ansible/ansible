"""Command line parsing."""

from __future__ import annotations

import argparse
import os
import sys
import typing as t

from .argparsing import (
    CompositeActionCompletionFinder,
)

from .commands import (
    do_commands,
)

from .epilog import (
    get_epilog,
)

from .compat import (
    HostSettings,
    convert_legacy_args,
)

from ..util import (
    get_ansible_version,
)


def parse_args(argv: t.Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    completer = CompositeActionCompletionFinder()

    parser = argparse.ArgumentParser(prog='ansible-test', epilog=get_epilog(completer), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version', version=f'%(prog)s version {get_ansible_version()}')

    do_commands(parser, completer)

    completer(
        parser,
        always_complete_options=False,
    )

    if argv is None:
        argv = sys.argv[1:]
    else:
        argv = argv[1:]

    args = parser.parse_args(argv)

    if args.explain and not args.verbosity:
        args.verbosity = 1

    if args.no_environment:
        pass
    elif args.host_path:
        args.host_settings = HostSettings.deserialize(os.path.join(args.host_path, 'settings.dat'))
    else:
        args.host_settings = convert_legacy_args(argv, args, args.target_mode)
        args.host_settings.apply_defaults()

    return args
