"""Completers for use with argcomplete."""
from __future__ import annotations

import argparse

from ..target import (
    find_target_completion,
)

from .argparsing.argcompletion import (
    OptionCompletionFinder,
)


def complete_target(completer: OptionCompletionFinder, prefix: str, parsed_args: argparse.Namespace, **_) -> list[str]:
    """Perform completion for the targets configured for the command being parsed."""
    matches = find_target_completion(parsed_args.targets_func, prefix, completer.list_mode)
    completer.disable_completion_mangling = completer.list_mode and len(matches) > 1
    return matches


def complete_choices(choices: list[str], prefix: str, **_) -> list[str]:
    """Perform completion using the provided choices."""
    matches = [choice for choice in choices if choice.startswith(prefix)]
    return matches


def register_completer(action: argparse.Action, completer) -> None:
    """Register the given completer with the specified action."""
    action.completer = completer  # type: ignore[attr-defined]  # intentionally using an attribute that does not exist
