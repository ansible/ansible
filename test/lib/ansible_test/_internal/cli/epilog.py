"""Argument parsing epilog generation."""
from __future__ import annotations

from .argparsing import (
    CompositeActionCompletionFinder,
)

from ..data import (
    data_context,
)


def get_epilog(completer: CompositeActionCompletionFinder) -> str:
    """Generate and return the epilog to use for help output."""
    if completer.enabled:
        epilog = 'Tab completion available using the "argcomplete" python package.'
    else:
        epilog = 'Install the "argcomplete" python package to enable tab completion.'

    if data_context().content.unsupported:
        epilog += '\n\n' + data_context().explain_working_directory()

    return epilog
