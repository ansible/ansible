"""Base classes for the primary parsers for composite command line arguments."""
from __future__ import annotations

import abc
import typing as t

from ..argparsing.parsers import (
    CompletionError,
    NamespaceParser,
    ParserState,
)


class ControllerNamespaceParser(NamespaceParser, metaclass=abc.ABCMeta):
    """Base class for controller namespace parsers."""
    @property
    def dest(self) -> str:
        """The name of the attribute where the value should be stored."""
        return 'controller'

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        if state.root_namespace.targets:
            raise ControllerRequiredFirstError()

        return super().parse(state)


class TargetNamespaceParser(NamespaceParser, metaclass=abc.ABCMeta):
    """Base class for target namespace parsers involving a single target."""
    @property
    def option_name(self) -> str:
        """The option name used for this parser."""
        return '--target'

    @property
    def dest(self) -> str:
        """The name of the attribute where the value should be stored."""
        return 'targets'

    @property
    def use_list(self) -> bool:
        """True if the destination is a list, otherwise False."""
        return True

    @property
    def limit_one(self) -> bool:
        """True if only one target is allowed, otherwise False."""
        return True


class TargetsNamespaceParser(NamespaceParser, metaclass=abc.ABCMeta):
    """Base class for controller namespace parsers involving multiple targets."""
    @property
    def option_name(self) -> str:
        """The option name used for this parser."""
        return '--target'

    @property
    def dest(self) -> str:
        """The name of the attribute where the value should be stored."""
        return 'targets'

    @property
    def use_list(self) -> bool:
        """True if the destination is a list, otherwise False."""
        return True


class ControllerRequiredFirstError(CompletionError):
    """Exception raised when controller and target options are specified out-of-order."""
    def __init__(self):
        super().__init__('The `--controller` option must be specified before `--target` option(s).')
