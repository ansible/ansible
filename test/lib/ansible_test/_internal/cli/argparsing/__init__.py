"""Completion finder which brings together custom options and completion logic."""
from __future__ import annotations

import abc
import argparse
import os
import re
import typing as t

from .argcompletion import (
    OptionCompletionFinder,
    get_comp_type,
    register_safe_action,
    warn,
)

from .parsers import (
    Completion,
    CompletionError,
    CompletionSuccess,
    CompletionUnavailable,
    DocumentationState,
    NamespaceParser,
    Parser,
    ParserError,
    ParserMode,
    ParserState,
)


class RegisteredCompletionFinder(OptionCompletionFinder):
    """
    Custom option completion finder for argcomplete which allows completion results to be registered.
    These registered completions, if provided, are used to filter the final completion results.
    This works around a known bug: https://github.com/kislyuk/argcomplete/issues/221
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.registered_completions: t.Optional[list[str]] = None

    def completer(
            self,
            prefix: str,
            action: argparse.Action,
            parsed_args: argparse.Namespace,
            **kwargs,
    ) -> list[str]:
        """
        Return a list of completions for the specified prefix and action.
        Use this as the completer function for argcomplete.
        """
        kwargs.clear()
        del kwargs

        completions = self.get_completions(prefix, action, parsed_args)

        if action.nargs and not isinstance(action.nargs, int):
            # prevent argcomplete from including unrelated arguments in the completion results
            self.registered_completions = completions

        return completions

    @abc.abstractmethod
    def get_completions(
            self,
            prefix: str,
            action: argparse.Action,
            parsed_args: argparse.Namespace,
    ) -> list[str]:
        """
        Return a list of completions for the specified prefix and action.
        Called by the complete function.
        """

    def quote_completions(self, completions, cword_prequote, last_wordbreak_pos):
        """Modify completion results before returning them."""
        if self.registered_completions is not None:
            # If one of the completion handlers registered their results, only allow those exact results to be returned.
            # This prevents argcomplete from adding results from other completers when they are known to be invalid.
            allowed_completions = set(self.registered_completions)
            completions = [completion for completion in completions if completion in allowed_completions]

        return super().quote_completions(completions, cword_prequote, last_wordbreak_pos)


class CompositeAction(argparse.Action, metaclass=abc.ABCMeta):
    """Base class for actions that parse composite arguments."""
    documentation_state: dict[t.Type[CompositeAction], DocumentationState] = {}

    def __init__(
            self,
            *args,
            **kwargs,
    ):
        self.definition = self.create_parser()
        self.documentation_state[type(self)] = documentation_state = DocumentationState()
        self.definition.document(documentation_state)

        kwargs.update(dest=self.definition.dest)

        super().__init__(*args, **kwargs)

        register_safe_action(type(self))

    @abc.abstractmethod
    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""

    def __call__(
            self,
            parser,
            namespace,
            values,
            option_string=None,
    ):
        state = ParserState(mode=ParserMode.PARSE, namespaces=[namespace], remainder=values)

        try:
            self.definition.parse(state)
        except ParserError as ex:
            error = str(ex)
        except CompletionError as ex:
            error = ex.message
        else:
            return

        if get_comp_type():
            # FUTURE: It may be possible to enhance error handling by surfacing this error message during downstream completion.
            return  # ignore parse errors during completion to avoid breaking downstream completion

        raise argparse.ArgumentError(self, error)


class CompositeActionCompletionFinder(RegisteredCompletionFinder):
    """Completion finder with support for composite argument parsing."""
    def get_completions(
            self,
            prefix: str,
            action: argparse.Action,
            parsed_args: argparse.Namespace,
    ) -> list[str]:
        """Return a list of completions appropriate for the given prefix and action, taking into account the arguments that have already been parsed."""
        assert isinstance(action, CompositeAction)

        state = ParserState(
            mode=ParserMode.LIST if self.list_mode else ParserMode.COMPLETE,
            remainder=prefix,
            namespaces=[parsed_args],
        )

        answer = complete(action.definition, state)

        completions = []

        if isinstance(answer, CompletionSuccess):
            self.disable_completion_mangling = answer.preserve
            completions = answer.completions

        if isinstance(answer, CompletionError):
            warn(answer.message)

        return completions


def detect_file_listing(value: str, mode: ParserMode) -> bool:
    """
    Return True if Bash will show a file listing and redraw the prompt, otherwise return False.

    If there are no list results, a file listing will be shown if the value after the last `=` or `:` character:

        - is empty
        - matches a full path
        - matches a partial path

    Otherwise Bash will play the bell sound and display nothing.

    see: https://github.com/kislyuk/argcomplete/issues/328
    see: https://github.com/kislyuk/argcomplete/pull/284
    """
    listing = False

    if mode == ParserMode.LIST:
        right = re.split('[=:]', value)[-1]
        listing = not right or os.path.exists(right)

        if not listing:
            directory = os.path.dirname(right)

            # noinspection PyBroadException
            try:
                filenames = os.listdir(directory or '.')
            except Exception:  # pylint: disable=broad-except
                pass
            else:
                listing = any(filename.startswith(right) for filename in filenames)

    return listing


def detect_false_file_completion(value: str, mode: ParserMode) -> bool:
    """
    Return True if Bash will provide an incorrect file completion, otherwise return False.

    If there are no completion results, a filename will be automatically completed if the value after the last `=` or `:` character:

        - matches exactly one partial path

    Otherwise Bash will play the bell sound and display nothing.

    see: https://github.com/kislyuk/argcomplete/issues/328
    see: https://github.com/kislyuk/argcomplete/pull/284
    """
    completion = False

    if mode == ParserMode.COMPLETE:
        completion = True

        right = re.split('[=:]', value)[-1]
        directory, prefix = os.path.split(right)

        # noinspection PyBroadException
        try:
            filenames = os.listdir(directory or '.')
        except Exception:  # pylint: disable=broad-except
            pass
        else:
            matches = [filename for filename in filenames if filename.startswith(prefix)]
            completion = len(matches) == 1

    return completion


def complete(
        completer: Parser,
        state: ParserState,
) -> Completion:
    """Perform argument completion using the given completer and return the completion result."""
    value = state.remainder

    answer: Completion

    try:
        completer.parse(state)
        raise ParserError('completion expected')
    except CompletionUnavailable as ex:
        if detect_file_listing(value, state.mode):
            # Displaying a warning before the file listing informs the user it is invalid. Bash will redraw the prompt after the list.
            # If the file listing is not shown, a warning could be helpful, but would introduce noise on the terminal since the prompt is not redrawn.
            answer = CompletionError(ex.message)
        elif detect_false_file_completion(value, state.mode):
            # When the current prefix provides no matches, but matches files a single file on disk, Bash will perform an incorrect completion.
            # Returning multiple invalid matches instead of no matches will prevent Bash from using its own completion logic in this case.
            answer = CompletionSuccess(
                list_mode=True,  # abuse list mode to enable preservation of the literal results
                consumed='',
                continuation='',
                matches=['completion', 'invalid']
            )
        else:
            answer = ex
    except Completion as ex:
        answer = ex

    return answer
