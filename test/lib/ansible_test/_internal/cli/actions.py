"""Actions for handling composite arguments with argparse."""
from __future__ import annotations

from .argparsing import (
    CompositeAction,
    NamespaceParser,
)

from .parsers import (
    DelegatedControllerParser,
    NetworkSshTargetParser,
    NetworkTargetParser,
    OriginControllerParser,
    PosixSshTargetParser,
    PosixTargetParser,
    SanityPythonTargetParser,
    UnitsPythonTargetParser,
    WindowsSshTargetParser,
    WindowsTargetParser,
)


class OriginControllerAction(CompositeAction):
    """Composite action parser for the controller when the only option is `origin`."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return OriginControllerParser()


class DelegatedControllerAction(CompositeAction):
    """Composite action parser for the controller when delegation is supported."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return DelegatedControllerParser()


class PosixTargetAction(CompositeAction):
    """Composite action parser for a POSIX target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return PosixTargetParser()


class WindowsTargetAction(CompositeAction):
    """Composite action parser for a Windows target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return WindowsTargetParser()


class NetworkTargetAction(CompositeAction):
    """Composite action parser for a network target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return NetworkTargetParser()


class SanityPythonTargetAction(CompositeAction):
    """Composite action parser for a sanity target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return SanityPythonTargetParser()


class UnitsPythonTargetAction(CompositeAction):
    """Composite action parser for a units target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return UnitsPythonTargetParser()


class PosixSshTargetAction(CompositeAction):
    """Composite action parser for a POSIX SSH target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return PosixSshTargetParser()


class WindowsSshTargetAction(CompositeAction):
    """Composite action parser for a Windows SSH target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return WindowsSshTargetParser()


class NetworkSshTargetAction(CompositeAction):
    """Composite action parser for a network SSH target."""

    def create_parser(self) -> NamespaceParser:
        """Return a namespace parser to parse the argument associated with this action."""
        return NetworkSshTargetParser()
