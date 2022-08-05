"""Composite argument parsers for ansible-test specific command-line arguments."""
from __future__ import annotations

import typing as t

from ...constants import (
    SUPPORTED_PYTHON_VERSIONS,
)

from ...ci import (
    get_ci_provider,
)

from ...host_configs import (
    ControllerConfig,
    NetworkConfig,
    NetworkInventoryConfig,
    PosixConfig,
    WindowsConfig,
    WindowsInventoryConfig,
)

from ..argparsing.parsers import (
    DocumentationState,
    Parser,
    ParserState,
    TypeParser,
)

from .value_parsers import (
    PythonParser,
)

from .host_config_parsers import (
    ControllerParser,
    DockerParser,
    NetworkInventoryParser,
    NetworkRemoteParser,
    OriginParser,
    PosixRemoteParser,
    PosixSshParser,
    WindowsInventoryParser,
    WindowsRemoteParser,
)


from .base_argument_parsers import (
    ControllerNamespaceParser,
    TargetNamespaceParser,
    TargetsNamespaceParser,
)


class OriginControllerParser(ControllerNamespaceParser, TypeParser):
    """Composite argument parser for the controller when delegation is not supported."""
    def get_stateless_parsers(self) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        return dict(
            origin=OriginParser(),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section = '--controller options:'

        state.sections[section] = ''  # place this section before the sections created by the parsers below
        state.sections[section] = '\n'.join([f'  {name}:{parser.document(state)}' for name, parser in self.get_stateless_parsers().items()])

        return None


class DelegatedControllerParser(ControllerNamespaceParser, TypeParser):
    """Composite argument parser for the controller when delegation is supported."""
    def get_stateless_parsers(self) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        parsers: dict[str, Parser] = dict(
            origin=OriginParser(),
            docker=DockerParser(controller=True),
        )

        if get_ci_provider().supports_core_ci_auth():
            parsers.update(
                remote=PosixRemoteParser(controller=True),
            )

        return parsers

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section = '--controller options:'

        state.sections[section] = ''  # place this section before the sections created by the parsers below
        state.sections[section] = '\n'.join([f'  {name}:{parser.document(state)}' for name, parser in self.get_stateless_parsers().items()])

        return None


class PosixTargetParser(TargetNamespaceParser, TypeParser):
    """Composite argument parser for a POSIX target."""
    def get_stateless_parsers(self) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        parsers: dict[str, Parser] = dict(
            controller=ControllerParser(),
            docker=DockerParser(controller=False),
        )

        if get_ci_provider().supports_core_ci_auth():
            parsers.update(
                remote=PosixRemoteParser(controller=False),
            )

        parsers.update(
            ssh=PosixSshParser(),
        )

        return parsers

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section = f'{self.option_name} options (choose one):'

        state.sections[section] = ''  # place this section before the sections created by the parsers below
        state.sections[section] = '\n'.join([f'  {name}:{parser.document(state)}' for name, parser in self.get_stateless_parsers().items()])

        return None


class WindowsTargetParser(TargetsNamespaceParser, TypeParser):
    """Composite argument parser for a Windows target."""
    @property
    def allow_inventory(self) -> bool:
        """True if inventory is allowed, otherwise False."""
        return True

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        return self.get_internal_parsers(state.root_namespace.targets)

    def get_stateless_parsers(self) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        return self.get_internal_parsers([])

    def get_internal_parsers(self, targets: list[WindowsConfig]) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        parsers: dict[str, Parser] = {}

        if self.allow_inventory and not targets:
            parsers.update(
                inventory=WindowsInventoryParser(),
            )

        if not targets or not any(isinstance(target, WindowsInventoryConfig) for target in targets):
            if get_ci_provider().supports_core_ci_auth():
                parsers.update(
                    remote=WindowsRemoteParser(),
                )

        return parsers

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section = f'{self.option_name} options (choose one):'

        state.sections[section] = ''  # place this section before the sections created by the parsers below
        state.sections[section] = '\n'.join([f'  {name}:{parser.document(state)}' for name, parser in self.get_stateless_parsers().items()])

        return None


class NetworkTargetParser(TargetsNamespaceParser, TypeParser):
    """Composite argument parser for a network target."""
    @property
    def allow_inventory(self) -> bool:
        """True if inventory is allowed, otherwise False."""
        return True

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        return self.get_internal_parsers(state.root_namespace.targets)

    def get_stateless_parsers(self) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        return self.get_internal_parsers([])

    def get_internal_parsers(self, targets: list[NetworkConfig]) -> dict[str, Parser]:
        """Return a dictionary of type names and type parsers."""
        parsers: dict[str, Parser] = {}

        if self.allow_inventory and not targets:
            parsers.update(
                inventory=NetworkInventoryParser(),
            )

        if not targets or not any(isinstance(target, NetworkInventoryConfig) for target in targets):
            if get_ci_provider().supports_core_ci_auth():
                parsers.update(
                    remote=NetworkRemoteParser(),
                )

        return parsers

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section = f'{self.option_name} options (choose one):'

        state.sections[section] = ''  # place this section before the sections created by the parsers below
        state.sections[section] = '\n'.join([f'  {name}:{parser.document(state)}' for name, parser in self.get_stateless_parsers().items()])

        return None


class PythonTargetParser(TargetsNamespaceParser, Parser):
    """Composite argument parser for a Python target."""
    def __init__(self, allow_venv: bool) -> None:
        super().__init__()

        self.allow_venv = allow_venv

    @property
    def option_name(self) -> str:
        """The option name used for this parser."""
        return '--target-python'

    def get_value(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result, without storing the result in the namespace."""
        versions = list(SUPPORTED_PYTHON_VERSIONS)

        for target in state.root_namespace.targets or []:  # type: PosixConfig
            versions.remove(target.python.version)

        parser = PythonParser(versions, allow_venv=self.allow_venv, allow_default=True)
        python = parser.parse(state)

        value = ControllerConfig(python=python)

        return value

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section = f'{self.option_name} options (choose one):'

        state.sections[section] = '\n'.join([
            f'  {PythonParser(SUPPORTED_PYTHON_VERSIONS, allow_venv=False, allow_default=True).document(state)}  # non-origin controller',
            f'  {PythonParser(SUPPORTED_PYTHON_VERSIONS, allow_venv=True, allow_default=True).document(state)}  # origin controller',
        ])

        return None


class SanityPythonTargetParser(PythonTargetParser):
    """Composite argument parser for a sanity Python target."""
    def __init__(self) -> None:
        super().__init__(allow_venv=False)


class UnitsPythonTargetParser(PythonTargetParser):
    """Composite argument parser for a units Python target."""
    def __init__(self) -> None:
        super().__init__(allow_venv=True)


class PosixSshTargetParser(PosixTargetParser):
    """Composite argument parser for a POSIX SSH target."""
    @property
    def option_name(self) -> str:
        """The option name used for this parser."""
        return '--target-posix'


class WindowsSshTargetParser(WindowsTargetParser):
    """Composite argument parser for a Windows SSH target."""
    @property
    def option_name(self) -> str:
        """The option name used for this parser."""
        return '--target-windows'

    @property
    def allow_inventory(self) -> bool:
        """True if inventory is allowed, otherwise False."""
        return False

    @property
    def limit_one(self) -> bool:
        """True if only one target is allowed, otherwise False."""
        return True


class NetworkSshTargetParser(NetworkTargetParser):
    """Composite argument parser for a network SSH target."""
    @property
    def option_name(self) -> str:
        """The option name used for this parser."""
        return '--target-network'

    @property
    def allow_inventory(self) -> bool:
        """True if inventory is allowed, otherwise False."""
        return False

    @property
    def limit_one(self) -> bool:
        """True if only one target is allowed, otherwise False."""
        return True
