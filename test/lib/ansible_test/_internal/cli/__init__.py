"""Command line parsing."""
from __future__ import annotations

import argparse
import os
import sys

from .argparsing import (
    CompositeActionCompletionFinder,
)

from .commands import (
    do_commands,
)


from .compat import (
    HostSettings,
    convert_legacy_args,
)


def parse_args():  # type: () -> argparse.Namespace
    """Parse command line arguments."""
    completer = CompositeActionCompletionFinder()

    if completer.enabled:
        epilog = 'Tab completion available using the "argcomplete" python package.'
    else:
        epilog = 'Install the "argcomplete" python package to enable tab completion.'

    parser = argparse.ArgumentParser(epilog=epilog)

    do_commands(parser, completer)

    completer(
        parser,
        always_complete_options=False,
    )

    argv = sys.argv[1:]
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
