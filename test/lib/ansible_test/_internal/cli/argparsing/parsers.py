"""General purpose composite argument parsing and completion."""
from __future__ import annotations

import abc
import collections.abc as c
import contextlib
import dataclasses
import enum
import os
import re
import typing as t

# NOTE: When choosing delimiters, take into account Bash and argcomplete behavior.
#
# Recommended characters for assignment and/or continuation: `/` `:` `=`
#
# The recommended assignment_character list is due to how argcomplete handles continuation characters.
# see: https://github.com/kislyuk/argcomplete/blob/5a20d6165fbb4d4d58559378919b05964870cc16/argcomplete/__init__.py#L557-L558

PAIR_DELIMITER = ','
ASSIGNMENT_DELIMITER = '='
PATH_DELIMITER = '/'


# This class was originally frozen. However, that causes issues when running under Python 3.11.
# See: https://github.com/python/cpython/issues/99856
@dataclasses.dataclass
class Completion(Exception):
    """Base class for argument completion results."""


@dataclasses.dataclass
class CompletionUnavailable(Completion):
    """Argument completion unavailable."""

    message: str = 'No completions available.'


@dataclasses.dataclass
class CompletionError(Completion):
    """Argument completion error."""

    message: t.Optional[str] = None


@dataclasses.dataclass
class CompletionSuccess(Completion):
    """Successful argument completion result."""

    list_mode: bool
    consumed: str
    continuation: str
    matches: list[str] = dataclasses.field(default_factory=list)

    @property
    def preserve(self) -> bool:
        """
        True if argcomplete should not mangle completion values, otherwise False.
        Only used when more than one completion exists to avoid overwriting the word undergoing completion.
        """
        return len(self.matches) > 1 and self.list_mode

    @property
    def completions(self) -> list[str]:
        """List of completion values to return to argcomplete."""
        completions = self.matches
        continuation = '' if self.list_mode else self.continuation

        if not self.preserve:
            # include the existing prefix to avoid rewriting the word undergoing completion
            completions = [f'{self.consumed}{completion}{continuation}' for completion in completions]

        return completions


class ParserMode(enum.Enum):
    """Mode the parser is operating in."""

    PARSE = enum.auto()
    COMPLETE = enum.auto()
    LIST = enum.auto()


class ParserError(Exception):
    """Base class for all parsing exceptions."""


@dataclasses.dataclass
class ParserBoundary:
    """Boundary details for parsing composite input."""

    delimiters: str
    required: bool
    match: t.Optional[str] = None
    ready: bool = True


@dataclasses.dataclass
class ParserState:
    """State of the composite argument parser."""

    mode: ParserMode
    remainder: str = ''
    consumed: str = ''
    boundaries: list[ParserBoundary] = dataclasses.field(default_factory=list)
    namespaces: list[t.Any] = dataclasses.field(default_factory=list)
    parts: list[str] = dataclasses.field(default_factory=list)

    @property
    def incomplete(self) -> bool:
        """True if parsing is incomplete (unparsed input remains), otherwise False."""
        return self.remainder is not None

    def match(self, value: str, choices: list[str]) -> bool:
        """Return True if the given value matches the provided choices, taking into account parsing boundaries, otherwise return False."""
        if self.current_boundary:
            delimiters, delimiter = self.current_boundary.delimiters, self.current_boundary.match
        else:
            delimiters, delimiter = '', None

        for choice in choices:
            if choice.rstrip(delimiters) == choice:
                # choice is not delimited
                if value == choice:
                    return True  # value matched
            else:
                # choice is delimited
                if f'{value}{delimiter}' == choice:
                    return True  # value and delimiter matched

        return False

    def read(self) -> str:
        """Read and return the next input segment, taking into account parsing boundaries."""
        delimiters = "".join(boundary.delimiters for boundary in self.boundaries)

        if delimiters:
            pattern = '([' + re.escape(delimiters) + '])'
            regex = re.compile(pattern)
            parts = regex.split(self.remainder, 1)
        else:
            parts = [self.remainder]

        if len(parts) > 1:
            value, delimiter, remainder = parts
        else:
            value, delimiter, remainder = parts[0], None, None

        for boundary in reversed(self.boundaries):
            if delimiter and delimiter in boundary.delimiters:
                boundary.match = delimiter
                self.consumed += value + delimiter
                break

            boundary.match = None
            boundary.ready = False

            if boundary.required:
                break

        self.remainder = remainder

        return value

    @property
    def root_namespace(self) -> t.Any:
        """THe root namespace."""
        return self.namespaces[0]

    @property
    def current_namespace(self) -> t.Any:
        """The current namespace."""
        return self.namespaces[-1]

    @property
    def current_boundary(self) -> t.Optional[ParserBoundary]:
        """The current parser boundary, if any, otherwise None."""
        return self.boundaries[-1] if self.boundaries else None

    def set_namespace(self, namespace: t.Any) -> None:
        """Set the current namespace."""
        self.namespaces.append(namespace)

    @contextlib.contextmanager
    def delimit(self, delimiters: str, required: bool = True) -> c.Iterator[ParserBoundary]:
        """Context manager for delimiting parsing of input."""
        boundary = ParserBoundary(delimiters=delimiters, required=required)

        self.boundaries.append(boundary)

        try:
            yield boundary
        finally:
            self.boundaries.pop()

        if boundary.required and not boundary.match:
            raise ParserError('required delimiter not found, hit up-level delimiter or end of input instead')


@dataclasses.dataclass
class DocumentationState:
    """State of the composite argument parser's generated documentation."""

    sections: dict[str, str] = dataclasses.field(default_factory=dict)


class Parser(metaclass=abc.ABCMeta):
    """Base class for all composite argument parsers."""

    @abc.abstractmethod
    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        raise Exception(f'Undocumented parser: {type(self)}')


class MatchConditions(enum.Flag):
    """Acceptable condition(s) for matching user input to available choices."""

    CHOICE = enum.auto()
    """Match any choice."""
    ANY = enum.auto()
    """Match any non-empty string."""
    NOTHING = enum.auto()
    """Match an empty string which is not followed by a boundary match."""


class DynamicChoicesParser(Parser, metaclass=abc.ABCMeta):
    """Base class for composite argument parsers which use a list of choices that can be generated during completion."""

    def __init__(self, conditions: MatchConditions = MatchConditions.CHOICE) -> None:
        self.conditions = conditions

    @abc.abstractmethod
    def get_choices(self, value: str) -> list[str]:
        """Return a list of valid choices based on the given input value."""

    def no_completion_match(self, value: str) -> CompletionUnavailable:  # pylint: disable=unused-argument
        """Return an instance of CompletionUnavailable when no match was found for the given value."""
        return CompletionUnavailable()

    def no_choices_available(self, value: str) -> ParserError:  # pylint: disable=unused-argument
        """Return an instance of ParserError when parsing fails and no choices are available."""
        return ParserError('No choices available.')

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value = state.read()
        choices = self.get_choices(value)

        if state.mode == ParserMode.PARSE or state.incomplete:
            if self.conditions & MatchConditions.CHOICE and state.match(value, choices):
                return value

            if self.conditions & MatchConditions.ANY and value:
                return value

            if self.conditions & MatchConditions.NOTHING and not value and state.current_boundary and not state.current_boundary.match:
                return value

            if state.mode == ParserMode.PARSE:
                if choices:
                    raise ParserError(f'"{value}" not in: {", ".join(choices)}')

                raise self.no_choices_available(value)

            raise CompletionUnavailable()

        matches = [choice for choice in choices if choice.startswith(value)]

        if not matches:
            raise self.no_completion_match(value)

        continuation = state.current_boundary.delimiters if state.current_boundary and state.current_boundary.required else ''

        raise CompletionSuccess(
            list_mode=state.mode == ParserMode.LIST,
            consumed=state.consumed,
            continuation=continuation,
            matches=matches,
        )


class ChoicesParser(DynamicChoicesParser):
    """Composite argument parser which relies on a static list of choices."""

    def __init__(self, choices: list[str], conditions: MatchConditions = MatchConditions.CHOICE) -> None:
        self.choices = choices

        super().__init__(conditions=conditions)

    def get_choices(self, value: str) -> list[str]:
        """Return a list of valid choices based on the given input value."""
        return self.choices

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return '|'.join(self.choices)


class EnumValueChoicesParser(ChoicesParser):
    """Composite argument parser which relies on a static list of choices derived from the values of an enum."""

    def __init__(self, enum_type: t.Type[enum.Enum], conditions: MatchConditions = MatchConditions.CHOICE) -> None:
        self.enum_type = enum_type

        super().__init__(choices=[str(item.value) for item in enum_type], conditions=conditions)

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value = super().parse(state)
        return self.enum_type(value)


class IntegerParser(DynamicChoicesParser):
    """Composite argument parser for integers."""

    PATTERN = re.compile('^[1-9][0-9]*$')

    def __init__(self, maximum: t.Optional[int] = None) -> None:
        self.maximum = maximum

        super().__init__()

    def get_choices(self, value: str) -> list[str]:
        """Return a list of valid choices based on the given input value."""
        if not value:
            numbers = list(range(1, 10))
        elif self.PATTERN.search(value):
            int_prefix = int(value)
            base = int_prefix * 10
            numbers = [int_prefix] + [base + i for i in range(0, 10)]
        else:
            numbers = []

        # NOTE: the minimum is currently fixed at 1

        if self.maximum is not None:
            numbers = [n for n in numbers if n <= self.maximum]

        return [str(n) for n in numbers]

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value = super().parse(state)
        return int(value)

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return '{integer}'


class BooleanParser(ChoicesParser):
    """Composite argument parser for boolean (yes/no) values."""

    def __init__(self) -> None:
        super().__init__(['yes', 'no'])

    def parse(self, state: ParserState) -> bool:
        """Parse the input from the given state and return the result."""
        value = super().parse(state)
        return value == 'yes'


class AnyParser(ChoicesParser):
    """Composite argument parser which accepts any input value."""

    def __init__(self, nothing: bool = False, no_match_message: t.Optional[str] = None) -> None:
        self.no_match_message = no_match_message

        conditions = MatchConditions.ANY

        if nothing:
            conditions |= MatchConditions.NOTHING

        super().__init__([], conditions=conditions)

    def no_completion_match(self, value: str) -> CompletionUnavailable:
        """Return an instance of CompletionUnavailable when no match was found for the given value."""
        if self.no_match_message:
            return CompletionUnavailable(message=self.no_match_message)

        return super().no_completion_match(value)

    def no_choices_available(self, value: str) -> ParserError:
        """Return an instance of ParserError when parsing fails and no choices are available."""
        if self.no_match_message:
            return ParserError(self.no_match_message)

        return super().no_choices_available(value)


class RelativePathNameParser(DynamicChoicesParser):
    """Composite argument parser for relative path names."""

    RELATIVE_NAMES = ['.', '..']

    def __init__(self, choices: list[str]) -> None:
        self.choices = choices

        super().__init__()

    def get_choices(self, value: str) -> list[str]:
        """Return a list of valid choices based on the given input value."""
        choices = list(self.choices)

        if value in self.RELATIVE_NAMES:
            # complete relative names, but avoid suggesting them unless the current name is relative
            # unfortunately this will be sorted in reverse of what bash presents ("../ ./" instead of "./ ../")
            choices.extend(f'{item}{PATH_DELIMITER}' for item in self.RELATIVE_NAMES)

        return choices


class FileParser(Parser):
    """Composite argument parser for absolute or relative file paths."""

    def parse(self, state: ParserState) -> str:
        """Parse the input from the given state and return the result."""
        if state.mode == ParserMode.PARSE:
            path = AnyParser().parse(state)

            if not os.path.isfile(path):
                raise ParserError(f'Not a file: {path}')
        else:
            path = ''

            with state.delimit(PATH_DELIMITER, required=False) as boundary:  # type: ParserBoundary
                while boundary.ready:
                    directory = path or '.'

                    try:
                        with os.scandir(directory) as scan:  # type: c.Iterator[os.DirEntry]
                            choices = [f'{item.name}{PATH_DELIMITER}' if item.is_dir() else item.name for item in scan]
                    except OSError:
                        choices = []

                    if not path:
                        choices.append(PATH_DELIMITER)  # allow absolute paths
                        choices.append('../')  # suggest relative paths

                    part = RelativePathNameParser(choices).parse(state)
                    path += f'{part}{boundary.match or ""}'

        return path


class AbsolutePathParser(Parser):
    """Composite argument parser for absolute file paths. Paths are only verified for proper syntax, not for existence."""

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        path = ''

        with state.delimit(PATH_DELIMITER, required=False) as boundary:  # type: ParserBoundary
            while boundary.ready:
                if path:
                    path += AnyParser(nothing=True).parse(state)
                else:
                    path += ChoicesParser([PATH_DELIMITER]).parse(state)

                path += boundary.match or ''

        return path


class NamespaceParser(Parser, metaclass=abc.ABCMeta):
    """Base class for composite argument parsers that store their results in a namespace."""

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        namespace = state.current_namespace
        current = getattr(namespace, self.dest)

        if current and self.limit_one:
            if state.mode == ParserMode.PARSE:
                raise ParserError('Option cannot be specified more than once.')

            raise CompletionError('Option cannot be specified more than once.')

        value = self.get_value(state)

        if self.use_list:
            if not current:
                current = []
                setattr(namespace, self.dest, current)

            current.append(value)
        else:
            setattr(namespace, self.dest, value)

        return value

    def get_value(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result, without storing the result in the namespace."""
        return super().parse(state)

    @property
    def use_list(self) -> bool:
        """True if the destination is a list, otherwise False."""
        return False

    @property
    def limit_one(self) -> bool:
        """True if only one target is allowed, otherwise False."""
        return not self.use_list

    @property
    @abc.abstractmethod
    def dest(self) -> str:
        """The name of the attribute where the value should be stored."""


class NamespaceWrappedParser(NamespaceParser):
    """Composite argument parser that wraps a non-namespace parser and stores the result in a namespace."""

    def __init__(self, dest: str, parser: Parser) -> None:
        self._dest = dest
        self.parser = parser

    def get_value(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result, without storing the result in the namespace."""
        return self.parser.parse(state)

    @property
    def dest(self) -> str:
        """The name of the attribute where the value should be stored."""
        return self._dest


class KeyValueParser(Parser, metaclass=abc.ABCMeta):
    """Base class for key/value composite argument parsers."""

    @abc.abstractmethod
    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        namespace = state.current_namespace
        parsers = self.get_parsers(state)
        keys = list(parsers)

        with state.delimit(PAIR_DELIMITER, required=False) as pair:  # type: ParserBoundary
            while pair.ready:
                with state.delimit(ASSIGNMENT_DELIMITER):
                    key = ChoicesParser(keys).parse(state)

                value = parsers[key].parse(state)

                setattr(namespace, key, value)

                keys.remove(key)

        return namespace


class PairParser(Parser, metaclass=abc.ABCMeta):
    """Base class for composite argument parsers consisting of a left and right argument parser, with input separated by a delimiter."""

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        namespace = self.create_namespace()

        state.set_namespace(namespace)

        with state.delimit(self.delimiter, self.required) as boundary:  # type: ParserBoundary
            choice = self.get_left_parser(state).parse(state)

        if boundary.match:
            self.get_right_parser(choice).parse(state)

        return namespace

    @property
    def required(self) -> bool:
        """True if the delimiter (and thus right parser) is required, otherwise False."""
        return False

    @property
    def delimiter(self) -> str:
        """The delimiter to use between the left and right parser."""
        return PAIR_DELIMITER

    @abc.abstractmethod
    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""

    @abc.abstractmethod
    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""

    @abc.abstractmethod
    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""


class TypeParser(Parser, metaclass=abc.ABCMeta):
    """Base class for composite argument parsers which parse a type name, a colon and then parse results based on the type given by the type name."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:  # pylint: disable=unused-argument
        """Return a dictionary of type names and type parsers."""
        return self.get_stateless_parsers()

    @abc.abstractmethod
    def get_stateless_parsers(self) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        parsers = self.get_parsers(state)

        with state.delimit(':'):
            key = ChoicesParser(list(parsers)).parse(state)

        value = parsers[key].parse(state)

        return value
