"""Command line parsing for all `coverage analyze targets` commands."""
from __future__ import annotations

import argparse

from .....environments import (
    CompositeActionCompletionFinder,
)

from .combine import (
    do_combine,
)

from .expand import (
    do_expand,
)

from .filter import (
    do_filter,
)

from .generate import (
    do_generate,
)

from .missing import (
    do_missing,
)


def do_targets(
        subparsers,
        parent: argparse.ArgumentParser,
        completer: CompositeActionCompletionFinder,
) -> None:
    """Command line parsing for all `coverage analyze targets` commands."""
    targets = subparsers.add_parser(
        'targets',
        help='analyze integration test target coverage',
    )

    targets_subparsers = targets.add_subparsers(metavar='COMMAND', required=True)

    do_generate(targets_subparsers, parent, completer)
    do_expand(targets_subparsers, parent, completer)
    do_filter(targets_subparsers, parent, completer)
    do_combine(targets_subparsers, parent, completer)
    do_missing(targets_subparsers, parent, completer)
