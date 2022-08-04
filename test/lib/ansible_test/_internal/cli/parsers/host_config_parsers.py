"""Composite parsers for the various types of hosts."""
from __future__ import annotations

import typing as t

from ...completion import (
    docker_completion,
    network_completion,
    remote_completion,
    windows_completion,
    filter_completion,
)

from ...host_configs import (
    ControllerConfig,
    DockerConfig,
    NetworkInventoryConfig,
    NetworkRemoteConfig,
    OriginConfig,
    PosixRemoteConfig,
    PosixSshConfig,
    WindowsInventoryConfig,
    WindowsRemoteConfig,
)

from ..compat import (
    get_fallback_remote_controller,
)

from ..argparsing.parsers import (
    ChoicesParser,
    DocumentationState,
    FileParser,
    MatchConditions,
    NamespaceWrappedParser,
    PairParser,
    Parser,
    ParserError,
    ParserState,
)

from .value_parsers import (
    PlatformParser,
    SshConnectionParser,
)

from .key_value_parsers import (
    ControllerKeyValueParser,
    DockerKeyValueParser,
    EmptyKeyValueParser,
    NetworkRemoteKeyValueParser,
    OriginKeyValueParser,
    PosixRemoteKeyValueParser,
    PosixSshKeyValueParser,
    WindowsRemoteKeyValueParser,
)

from .helpers import (
    get_docker_pythons,
    get_remote_pythons,
)


class OriginParser(Parser):
    """Composite argument parser for the origin."""
    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        namespace = OriginConfig()

        state.set_namespace(namespace)

        parser = OriginKeyValueParser()
        parser.parse(state)

        return namespace

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return OriginKeyValueParser().document(state)


class ControllerParser(Parser):
    """Composite argument parser for the controller."""
    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        namespace = ControllerConfig()

        state.set_namespace(namespace)

        parser = ControllerKeyValueParser()
        parser.parse(state)

        return namespace

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return ControllerKeyValueParser().document(state)


class DockerParser(PairParser):
    """Composite argument parser for a docker host."""
    def __init__(self, controller: bool) -> None:
        self.controller = controller

    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return DockerConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        return NamespaceWrappedParser('name', ChoicesParser(list(filter_completion(docker_completion(), controller_only=self.controller)),
                                                            conditions=MatchConditions.CHOICE | MatchConditions.ANY))

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return DockerKeyValueParser(choice, self.controller)

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value: DockerConfig = super().parse(state)

        if not value.python and not get_docker_pythons(value.name, self.controller, True):
            raise ParserError(f'Python version required for docker image: {value.name}')

        return value

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        default = 'default'
        content = '\n'.join([f'  {image} ({", ".join(get_docker_pythons(image, self.controller, False))})'
                             for image, item in filter_completion(docker_completion(), controller_only=self.controller).items()])

        content += '\n'.join([
            '',
            '  {image}  # python must be specified for custom images',
        ])

        state.sections[f'{"controller" if self.controller else "target"} docker images and supported python version (choose one):'] = content

        return f'{{image}}[,{DockerKeyValueParser(default, self.controller).document(state)}]'


class PosixRemoteParser(PairParser):
    """Composite argument parser for a POSIX remote host."""
    def __init__(self, controller: bool) -> None:
        self.controller = controller

    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return PosixRemoteConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        return NamespaceWrappedParser('name', PlatformParser(list(filter_completion(remote_completion(), controller_only=self.controller))))

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return PosixRemoteKeyValueParser(choice, self.controller)

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value: PosixRemoteConfig = super().parse(state)

        if not value.python and not get_remote_pythons(value.name, self.controller, True):
            raise ParserError(f'Python version required for remote: {value.name}')

        return value

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        default = get_fallback_remote_controller()
        content = '\n'.join([f'  {name} ({", ".join(get_remote_pythons(name, self.controller, False))})'
                             for name, item in filter_completion(remote_completion(), controller_only=self.controller).items()])

        content += '\n'.join([
            '',
            '  {platform}/{version}  # python must be specified for unknown systems',
        ])

        state.sections[f'{"controller" if self.controller else "target"} remote systems and supported python versions (choose one):'] = content

        return f'{{system}}[,{PosixRemoteKeyValueParser(default, self.controller).document(state)}]'


class WindowsRemoteParser(PairParser):
    """Composite argument parser for a Windows remote host."""
    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return WindowsRemoteConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        names = list(filter_completion(windows_completion()))

        for target in state.root_namespace.targets or []:  # type: WindowsRemoteConfig
            names.remove(target.name)

        return NamespaceWrappedParser('name', PlatformParser(names))

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return WindowsRemoteKeyValueParser()

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        content = '\n'.join([f'  {name}' for name, item in filter_completion(windows_completion()).items()])

        content += '\n'.join([
            '',
            '  windows/{version}  # use an unknown windows version',
        ])

        state.sections['target remote systems (choose one):'] = content

        return f'{{system}}[,{WindowsRemoteKeyValueParser().document(state)}]'


class NetworkRemoteParser(PairParser):
    """Composite argument parser for a network remote host."""
    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return NetworkRemoteConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        names = list(filter_completion(network_completion()))

        for target in state.root_namespace.targets or []:  # type: NetworkRemoteConfig
            names.remove(target.name)

        return NamespaceWrappedParser('name', PlatformParser(names))

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return NetworkRemoteKeyValueParser()

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        content = '\n'.join([f'  {name}' for name, item in filter_completion(network_completion()).items()])

        content += '\n'.join([
            '',
            '  {platform}/{version}  # use an unknown platform and version',
        ])

        state.sections['target remote systems (choose one):'] = content

        return f'{{system}}[,{NetworkRemoteKeyValueParser().document(state)}]'


class WindowsInventoryParser(PairParser):
    """Composite argument parser for a Windows inventory."""
    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return WindowsInventoryConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        return NamespaceWrappedParser('path', FileParser())

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return EmptyKeyValueParser()

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return '{path}  # INI format inventory file'


class NetworkInventoryParser(PairParser):
    """Composite argument parser for a network inventory."""
    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return NetworkInventoryConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        return NamespaceWrappedParser('path', FileParser())

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return EmptyKeyValueParser()

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return '{path}  # INI format inventory file'


class PosixSshParser(PairParser):
    """Composite argument parser for a POSIX SSH host."""
    def create_namespace(self) -> t.Any:
        """Create and return a namespace."""
        return PosixSshConfig()

    def get_left_parser(self, state: ParserState) -> Parser:
        """Return the parser for the left side."""
        return SshConnectionParser()

    def get_right_parser(self, choice: t.Any) -> Parser:
        """Return the parser for the right side."""
        return PosixSshKeyValueParser()

    @property
    def required(self) -> bool:
        """True if the delimiter (and thus right parser) is required, otherwise False."""
        return True

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return f'{SshConnectionParser().document(state)}[,{PosixSshKeyValueParser().document(state)}]'
