"""Composite argument key-value parsers used by other parsers."""
from __future__ import annotations

import typing as t

from ...constants import (
    CONTROLLER_PYTHON_VERSIONS,
    REMOTE_PROVIDERS,
    SECCOMP_CHOICES,
    SUPPORTED_PYTHON_VERSIONS,
)

from ...completion import (
    AuditMode,
    CGroupVersion,
)

from ...util import (
    REMOTE_ARCHITECTURES,
    WINDOWS_CONNECTIONS,
)

from ...host_configs import (
    OriginConfig,
)

from ...become import (
    SUPPORTED_BECOME_METHODS,
)

from ..argparsing.parsers import (
    AnyParser,
    BooleanParser,
    ChoicesParser,
    DocumentationState,
    EnumValueChoicesParser,
    IntegerParser,
    KeyValueParser,
    Parser,
    ParserState,
)

from .value_parsers import (
    PythonParser,
)

from .helpers import (
    get_controller_pythons,
    get_remote_pythons,
    get_docker_pythons,
)


class OriginKeyValueParser(KeyValueParser):
    """Composite argument parser for origin key/value pairs."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        versions = CONTROLLER_PYTHON_VERSIONS

        return dict(
            python=PythonParser(versions=versions, allow_venv=True, allow_default=True),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        python_parser = PythonParser(versions=CONTROLLER_PYTHON_VERSIONS, allow_venv=True, allow_default=True)

        section_name = 'origin options'

        state.sections[f'controller {section_name} (comma separated):'] = '\n'.join([
            f'  python={python_parser.document(state)}',
        ])

        return f'{{{section_name}}}  # default'


class ControllerKeyValueParser(KeyValueParser):
    """Composite argument parser for controller key/value pairs."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        versions = get_controller_pythons(state.root_namespace.controller, False)
        allow_default = bool(get_controller_pythons(state.root_namespace.controller, True))
        allow_venv = isinstance(state.root_namespace.controller, OriginConfig) or not state.root_namespace.controller

        return dict(
            python=PythonParser(versions=versions, allow_venv=allow_venv, allow_default=allow_default),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section_name = 'controller options'

        state.sections[f'target {section_name} (comma separated):'] = '\n'.join([
            f'  python={PythonParser(SUPPORTED_PYTHON_VERSIONS, allow_venv=False, allow_default=True).document(state)}  # non-origin controller',
            f'  python={PythonParser(SUPPORTED_PYTHON_VERSIONS, allow_venv=True, allow_default=True).document(state)}  # origin controller',
        ])

        return f'{{{section_name}}}  # default'


class DockerKeyValueParser(KeyValueParser):
    """Composite argument parser for docker key/value pairs."""

    def __init__(self, image: str, controller: bool) -> None:
        self.controller = controller
        self.versions = get_docker_pythons(image, controller, False)
        self.allow_default = bool(get_docker_pythons(image, controller, True))

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        return dict(
            python=PythonParser(versions=self.versions, allow_venv=False, allow_default=self.allow_default),
            seccomp=ChoicesParser(SECCOMP_CHOICES),
            cgroup=EnumValueChoicesParser(CGroupVersion),
            audit=EnumValueChoicesParser(AuditMode),
            privileged=BooleanParser(),
            memory=IntegerParser(),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        python_parser = PythonParser(versions=[], allow_venv=False, allow_default=self.allow_default)

        section_name = 'docker options'

        state.sections[f'{"controller" if self.controller else "target"} {section_name} (comma separated):'] = '\n'.join([
            f'  python={python_parser.document(state)}',
            f'  seccomp={ChoicesParser(SECCOMP_CHOICES).document(state)}',
            f'  cgroup={EnumValueChoicesParser(CGroupVersion).document(state)}',
            f'  audit={EnumValueChoicesParser(AuditMode).document(state)}',
            f'  privileged={BooleanParser().document(state)}',
            f'  memory={IntegerParser().document(state)}  # bytes',
        ])

        return f'{{{section_name}}}'


class PosixRemoteKeyValueParser(KeyValueParser):
    """Composite argument parser for POSIX remote key/value pairs."""

    def __init__(self, name: str, controller: bool) -> None:
        self.controller = controller
        self.versions = get_remote_pythons(name, controller, False)
        self.allow_default = bool(get_remote_pythons(name, controller, True))

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        return dict(
            become=ChoicesParser(list(SUPPORTED_BECOME_METHODS)),
            provider=ChoicesParser(REMOTE_PROVIDERS),
            arch=ChoicesParser(REMOTE_ARCHITECTURES),
            python=PythonParser(versions=self.versions, allow_venv=False, allow_default=self.allow_default),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        python_parser = PythonParser(versions=[], allow_venv=False, allow_default=self.allow_default)

        section_name = 'remote options'

        state.sections[f'{"controller" if self.controller else "target"} {section_name} (comma separated):'] = '\n'.join([
            f'  become={ChoicesParser(list(SUPPORTED_BECOME_METHODS)).document(state)}',
            f'  provider={ChoicesParser(REMOTE_PROVIDERS).document(state)}',
            f'  arch={ChoicesParser(REMOTE_ARCHITECTURES).document(state)}',
            f'  python={python_parser.document(state)}',
        ])

        return f'{{{section_name}}}'


class WindowsRemoteKeyValueParser(KeyValueParser):
    """Composite argument parser for Windows remote key/value pairs."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        return dict(
            provider=ChoicesParser(REMOTE_PROVIDERS),
            arch=ChoicesParser(REMOTE_ARCHITECTURES),
            connection=ChoicesParser(WINDOWS_CONNECTIONS),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section_name = 'remote options'

        state.sections[f'target {section_name} (comma separated):'] = '\n'.join([
            f'  provider={ChoicesParser(REMOTE_PROVIDERS).document(state)}',
            f'  arch={ChoicesParser(REMOTE_ARCHITECTURES).document(state)}',
            f'  connection={ChoicesParser(WINDOWS_CONNECTIONS).document(state)}',
        ])

        return f'{{{section_name}}}'


class NetworkRemoteKeyValueParser(KeyValueParser):
    """Composite argument parser for network remote key/value pairs."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        return dict(
            provider=ChoicesParser(REMOTE_PROVIDERS),
            arch=ChoicesParser(REMOTE_ARCHITECTURES),
            collection=AnyParser(),
            connection=AnyParser(),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        section_name = 'remote options'

        state.sections[f'target {section_name} (comma separated):'] = '\n'.join([
            f'  provider={ChoicesParser(REMOTE_PROVIDERS).document(state)}',
            f'  arch={ChoicesParser(REMOTE_ARCHITECTURES).document(state)}',
            '  collection={collection}',
            '  connection={connection}',
        ])

        return f'{{{section_name}}}'


class PosixSshKeyValueParser(KeyValueParser):
    """Composite argument parser for POSIX SSH host key/value pairs."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        return dict(
            python=PythonParser(versions=list(SUPPORTED_PYTHON_VERSIONS), allow_venv=False, allow_default=False),
        )

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        python_parser = PythonParser(versions=SUPPORTED_PYTHON_VERSIONS, allow_venv=False, allow_default=False)

        section_name = 'ssh options'

        state.sections[f'target {section_name} (comma separated):'] = '\n'.join([
            f'  python={python_parser.document(state)}',
        ])

        return f'{{{section_name}}}'


class EmptyKeyValueParser(KeyValueParser):
    """Composite argument parser when a key/value parser is required but there are no keys available."""

    def get_parsers(self, state: ParserState) -> dict[str, Parser]:
        """Return a dictionary of key names and value parsers."""
        return {}
