"""Wrapper around argcomplete providing bug fixes and additional features."""

from __future__ import annotations

import argparse
import enum
import os
import typing as t


class Substitute:
    """Substitute for missing class which accepts all arguments."""

    def __init__(self, *args, **kwargs) -> None:
        pass


try:
    import argcomplete

    try:
        # argcomplete 3+
        # see: https://github.com/kislyuk/argcomplete/commit/bd781cb08512b94966312377186ebc5550f46ae0
        from argcomplete.finders import (
            CompletionFinder,
            default_validator,
        )
    except ImportError:
        # argcomplete <3
        from argcomplete import (
            CompletionFinder,
            default_validator,
        )

    warn = argcomplete.warn  # pylint: disable=invalid-name
except ImportError:
    argcomplete = None

    CompletionFinder = Substitute
    default_validator = Substitute  # pylint: disable=invalid-name
    warn = Substitute  # pylint: disable=invalid-name


class CompType(enum.Enum):
    """
    Bash COMP_TYPE argument completion types.
    For documentation, see: https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-COMP_005fTYPE
    """

    COMPLETION = '\t'
    """
    Standard completion, typically triggered by a single tab.
    """
    MENU_COMPLETION = '%'
    """
    Menu completion, which cycles through each completion instead of showing a list.
    For help using this feature, see: https://stackoverflow.com/questions/12044574/getting-complete-and-menu-complete-to-work-together
    """
    LIST = '?'
    """
    Standard list, typically triggered by a double tab.
    """
    LIST_AMBIGUOUS = '!'
    """
    Listing with `show-all-if-ambiguous` set.
    For documentation, see https://www.gnu.org/software/bash/manual/html_node/Readline-Init-File-Syntax.html#index-show_002dall_002dif_002dambiguous
    For additional details, see: https://unix.stackexchange.com/questions/614123/explanation-of-bash-completion-comp-type
    """
    LIST_UNMODIFIED = '@'
    """
    Listing with `show-all-if-unmodified` set.
    For documentation, see https://www.gnu.org/software/bash/manual/html_node/Readline-Init-File-Syntax.html#index-show_002dall_002dif_002dunmodified
    For additional details, see: : https://unix.stackexchange.com/questions/614123/explanation-of-bash-completion-comp-type
    """

    @property
    def list_mode(self) -> bool:
        """True if completion is running in list mode, otherwise False."""
        return self in (CompType.LIST, CompType.LIST_AMBIGUOUS, CompType.LIST_UNMODIFIED)


def register_safe_action(action_type: t.Type[argparse.Action]) -> None:
    """Register the given action as a safe action for argcomplete to use during completion if it is not already registered."""
    if argcomplete and action_type not in argcomplete.safe_actions:
        if isinstance(argcomplete.safe_actions, set):
            # argcomplete 3+
            # see: https://github.com/kislyuk/argcomplete/commit/bd781cb08512b94966312377186ebc5550f46ae0
            argcomplete.safe_actions.add(action_type)
        else:
            # argcomplete <3
            argcomplete.safe_actions += (action_type,)


def get_comp_type() -> t.Optional[CompType]:
    """Parse the COMP_TYPE environment variable (if present) and return the associated CompType enum value."""
    value = os.environ.get('COMP_TYPE')
    comp_type = CompType(chr(int(value))) if value else None
    return comp_type


class OptionCompletionFinder(CompletionFinder):
    """
    Custom completion finder for argcomplete.
    It provides support for running completion in list mode, which argcomplete natively handles the same as standard completion.
    """

    enabled = bool(argcomplete)

    def __init__(self, *args, validator=None, **kwargs) -> None:
        if validator:
            raise ValueError()

        self.comp_type = get_comp_type()
        self.list_mode = self.comp_type.list_mode if self.comp_type else False
        self.disable_completion_mangling = False

        finder = self

        def custom_validator(completion, prefix):
            """Completion validator used to optionally bypass validation."""
            if finder.disable_completion_mangling:
                return True

            return default_validator(completion, prefix)

        super().__init__(
            *args,
            validator=custom_validator,
            **kwargs,
        )

    def __call__(self, *args, **kwargs):
        if self.enabled:
            super().__call__(*args, **kwargs)

    def quote_completions(self, completions, cword_prequote, last_wordbreak_pos):
        """Intercept default quoting behavior to optionally block mangling of completion entries."""
        if self.disable_completion_mangling:
            # Word breaks have already been handled when generating completions, don't mangle them further.
            # This is needed in many cases when returning completion lists which lack the existing completion prefix.
            last_wordbreak_pos = None

        return super().quote_completions(completions, cword_prequote, last_wordbreak_pos)
