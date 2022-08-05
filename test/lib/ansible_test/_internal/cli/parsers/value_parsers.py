"""Composite argument value parsers used by other parsers."""
from __future__ import annotations

import collections.abc as c
import typing as t

from ...host_configs import (
    NativePythonConfig,
    PythonConfig,
    VirtualPythonConfig,
)

from ..argparsing.parsers import (
    AbsolutePathParser,
    AnyParser,
    ChoicesParser,
    DocumentationState,
    IntegerParser,
    MatchConditions,
    Parser,
    ParserError,
    ParserState,
    ParserBoundary,
)


class PythonParser(Parser):
    """
    Composite argument parser for Python versions, with support for specifying paths and using virtual environments.

    Allowed formats:

    {version}
    venv/{version}
    venv/system-site-packages/{version}

    The `{version}` has two possible formats:

    X.Y
    X.Y@{path}

    Where `X.Y` is the Python major and minor version number and `{path}` is an absolute path with one of the following formats:

    /path/to/python
    /path/to/python/directory/

    When a trailing slash is present, it is considered a directory, and `python{version}` will be appended to it automatically.

    The default path depends on the context:

    - Known docker/remote environments can declare their own path.
    - The origin host uses `sys.executable` if `{version}` matches the current version in `sys.version_info`.
    - The origin host (as a controller or target) use the `$PATH` environment variable to find `python{version}`.
    - As a fallback/default, the path `/usr/bin/python{version}` is used.

    NOTE: The Python path determines where to find the Python interpreter.
          In the case of an ansible-test managed virtual environment, that Python interpreter will be used to create the virtual environment.
          So the path given will not be the one actually used for the controller or target.

    Known docker/remote environments limit the available Python versions to configured values known to be valid.
    The origin host and unknown environments assume all relevant Python versions are available.
    """
    def __init__(self,
                 versions: c.Sequence[str],
                 *,
                 allow_default: bool,
                 allow_venv: bool,
                 ):
        version_choices = list(versions)

        if allow_default:
            version_choices.append('default')

        first_choices = list(version_choices)

        if allow_venv:
            first_choices.append('venv/')

        venv_choices = list(version_choices) + ['system-site-packages/']

        self.versions = versions
        self.allow_default = allow_default
        self.allow_venv = allow_venv
        self.version_choices = version_choices
        self.first_choices = first_choices
        self.venv_choices = venv_choices
        self.venv_choices = venv_choices

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        boundary: ParserBoundary

        with state.delimit('@/', required=False) as boundary:
            version = ChoicesParser(self.first_choices).parse(state)

        python: PythonConfig

        if version == 'venv':
            with state.delimit('@/', required=False) as boundary:
                version = ChoicesParser(self.venv_choices).parse(state)

            if version == 'system-site-packages':
                system_site_packages = True

                with state.delimit('@', required=False) as boundary:
                    version = ChoicesParser(self.version_choices).parse(state)
            else:
                system_site_packages = False

            python = VirtualPythonConfig(version=version, system_site_packages=system_site_packages)
        else:
            python = NativePythonConfig(version=version)

        if boundary.match == '@':
            # FUTURE: For OriginConfig or ControllerConfig->OriginConfig the path could be validated with an absolute path parser (file or directory).
            python.path = AbsolutePathParser().parse(state)

        return python

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""

        docs = '[venv/[system-site-packages/]]' if self.allow_venv else ''

        if self.versions:
            docs += '|'.join(self.version_choices)
        else:
            docs += '{X.Y}'

        docs += '[@{path|dir/}]'

        return docs


class PlatformParser(ChoicesParser):
    """Composite argument parser for "{platform}/{version}" formatted choices."""
    def __init__(self, choices: list[str]) -> None:
        super().__init__(choices, conditions=MatchConditions.CHOICE | MatchConditions.ANY)

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        value = super().parse(state)

        if len(value.split('/')) != 2:
            raise ParserError(f'invalid platform format: {value}')

        return value


class SshConnectionParser(Parser):
    """
    Composite argument parser for connecting to a host using SSH.
    Format: user@host[:port]
    """
    EXPECTED_FORMAT = '{user}@{host}[:{port}]'

    def parse(self, state: ParserState) -> t.Any:
        """Parse the input from the given state and return the result."""
        namespace = state.current_namespace

        with state.delimit('@'):
            user = AnyParser(no_match_message=f'Expected {{user}} from: {self.EXPECTED_FORMAT}').parse(state)

        setattr(namespace, 'user', user)

        with state.delimit(':', required=False) as colon:  # type: ParserBoundary
            host = AnyParser(no_match_message=f'Expected {{host}} from: {self.EXPECTED_FORMAT}').parse(state)

        setattr(namespace, 'host', host)

        if colon.match:
            port = IntegerParser(65535).parse(state)
            setattr(namespace, 'port', port)

        return namespace

    def document(self, state: DocumentationState) -> t.Optional[str]:
        """Generate and return documentation for this parser."""
        return self.EXPECTED_FORMAT
