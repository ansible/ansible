"""Setup and configure remote debugging."""

from __future__ import annotations

import dataclasses
import importlib
import json
import os
import re
import typing as t

from .util import (
    cache,
    display,
    raw_command,
    ApplicationError,
)
from .util_common import (
    CommonConfig,
)

from .processes import (
    Process,
    get_current_process,
)

from .config import (
    EnvironmentConfig,
)

from .metadata import (
    DebugpySettings,
    PyDevDSettings,
    DebuggerFlags,
)

from .data import (
    data_context,
)

HAS_DEBUGPY = False
try:
    import debugpy as _debugpy
    from debugpy.server import cli as _debugpy_cli

    HAS_DEBUGPY = True
except ImportError:
    pass


class DebuggerProfile(t.Protocol):
    """Commons interface for debugger profiles."""

    debug_type: str
    """The type of debugger as known by the AnsiballZ extension config suffix."""
    package: str | None
    """The package name of the debugger to install by ansible-tesst, or `None` if not applicable."""
    port: int
    """The port on the origin host which is listening for incoming connections from the debugger."""

    def activate_debugger(self, host: str, port: int) -> None:
        """Activate the debugger in ansible-test after delegation."""

    def get_ansiballz_config(self, host: str, port: int) -> dict[str, object]:
        """Gets the extra configuration data for the AnsiballZ extension module."""

    def get_cli_arguments(self, host: str, port: int) -> list[str]:
        """Get command line arguments for the debugger when running Ansible CLI programs."""

    def get_environment_variables(self, source_mapping: dict[str, str]) -> dict[str, str]:
        """Get environment variables needed to configure the debugger for debugging."""


class PyDevDProfile(DebuggerProfile):
    """Profile for the PyDevD debugger."""

    def __init__(self, settings: PyDevDSettings) -> None:
        self._settings = settings
        self.debug_type = 'pydevd'
        self.package = settings.package
        self.port = settings.port

    def activate_debugger(self, host: str, port: int) -> None:
        module_name = self._settings.module
        debugging_module = importlib.import_module(module_name)
        debugging_module.settrace(**self._get_settrace_arguments(host, port))

    def get_ansiballz_config(self, host: str, port: int) -> dict[str, object]:
        settrace = dict(
            host=host,
            port=port,
        ) | self._settings.settrace

        return dict(
            module=self._settings.module,
            settrace=settrace,
        )

    def get_cli_arguments(self, host: str, port: int) -> list[str]:
        return ['-m', 'pydevd', '--client', host, '--port', str(port)] + self._settings.args + ['--file']

    def get_environment_variables(self, source_mapping: dict[str, str]) -> dict[str, str]:
        return dict(
            PATHS_FROM_ECLIPSE_TO_PYTHON=json.dumps(list(source_mapping.items())),
            PYDEVD_DISABLE_FILE_VALIDATION="1",
        )

    def _get_settrace_arguments(self, host: str, port: int) -> dict[str, object]:
        """Get settrace arguments for pydevd."""
        return self._settings.settrace | dict(
            host=host,
            port=port,
        )


class DebugpyProfile(DebuggerProfile):
    """Profile for the debugpy debugger."""

    def __init__(self, settings: DebugpySettings) -> None:
        self._settings = settings
        self.debug_type = 'debugpy'
        self.package = 'debugpy'
        self.port = settings.port

    def activate_debugger(self, host: str, port: int) -> None:
        if not HAS_DEBUGPY:
            raise ImportError("debugpy is not installed, cannot activate debugger.")

        _debugpy.connect((host, port), **self._settings.connect)

    def get_ansiballz_config(self, host: str, port: int) -> dict[str, object]:
        return dict(
            host=host,
            port=port,
            connect=self._settings.connect,
        )

    def get_cli_arguments(self, host: str, port: int) -> list[str]:
        cli_args = ['-m', 'debugpy', '--connect', f"{host}:{port}"]
        if access_token := self._settings.connect.get('access_token'):
            cli_args += ['--adapter-access-token', str(access_token)]
        if session_pid := self._settings.connect.get('parent_session_pid'):
            cli_args += ['--parent-session-pid', str(session_pid)]
        if self._settings.args:
            cli_args += self._settings.args

        return cli_args

    def get_environment_variables(self, source_mapping: dict[str, str]) -> dict[str, str]:
        return dict(
            PATHS_FROM_ECLIPSE_TO_PYTHON=json.dumps(list(source_mapping.items())),
            PYDEVD_DISABLE_FILE_VALIDATION="1",
        )


def initialize_debugger(args: CommonConfig) -> None:
    """Initialize the debugger settings before delegation."""
    if not isinstance(args, EnvironmentConfig):
        return

    if args.metadata.loaded:
        return  # after delegation

    if collection := data_context().content.collection:
        args.metadata.collection_root = collection.root

    load_debugger_settings(args)


def parse_debugpy_debugger_settings(value: str) -> DebugpySettings:
    """Parse debugpy remote debugger settings and apply defaults."""
    try:
        settings = DebugpySettings(**json.loads(value))
    except Exception as ex:
        raise ApplicationError(f"Invalid debugpy settings: {ex}") from ex

    if port := detect_debugpy_port():
        settings = dataclasses.replace(settings, port=port)

    if token := get_debugpy_access_token():
        settings.connect.setdefault('access_token', token)

    # If not set explicitly, use the current process PID.
    # This assumes that this ansible-test process is the one initially launched by debugpy.
    settings.connect.setdefault('parent_session_pid', os.getpid())

    return settings


def parse_pydevd_debugger_settings(value: str) -> PyDevDSettings:
    """Parse PyDevD remote debugger settings and apply defaults."""
    try:
        settings = PyDevDSettings(**json.loads(value))
    except Exception as ex:
        raise ApplicationError(f"Invalid debugger settings: {ex}") from ex

    if not settings.module:
        if not settings.package or 'pydevd-pycharm' in settings.package:
            module = 'pydevd_pycharm'
        else:
            module = 'pydevd'

        settings = dataclasses.replace(settings, module=module)

    if settings.package is None:
        if settings.module == 'pydevd_pycharm':
            if pycharm_version := detect_pycharm_version():
                package = f'pydevd-pycharm~={pycharm_version}'
            else:
                package = None
        else:
            package = 'pydevd'

        settings = dataclasses.replace(settings, package=package)

    settings.settrace.setdefault('suspend', False)

    if port := detect_pydevd_port():
        settings = dataclasses.replace(settings, port=port)

        if detect_pycharm_process():
            # This only works with the default PyCharm debugger.
            # Using it with PyCharm's "Python Debug Server" results in hangs in Ansible workers.
            # Further investigation is required to understand the cause.
            settings = dataclasses.replace(settings, args=settings.args + ['--multiprocess'])

    return settings


def load_debugger_settings(args: EnvironmentConfig) -> None:
    """Load the remote debugger settings."""
    debug_type: t.Literal['pydevd', 'debugpy'] | None = None
    if args.metadata.debugger_flags.on_demand:
        # On-demand debugging only enables debugging if we're running under a debugger, otherwise it's a no-op.

        if detect_debugpy_port():
            debug_type = 'debugpy'
        elif detect_pydevd_port():
            debug_type = 'pydevd'
        else:
            display.info('Debugging disabled because no debugger was detected.', verbosity=1)
            args.metadata.debugger_flags = DebuggerFlags.all(False)
            return

        display.info('Enabling on-demand debugging.', verbosity=1)

        if not args.metadata.debugger_flags.enable:
            # Assume the user wants all debugging features enabled, since on-demand debugging with no features is pointless.
            args.metadata.debugger_flags = DebuggerFlags.all(True)

    if not args.metadata.debugger_flags.enable:
        return

    if not debug_type:
        debug_type = 'debugpy' if 'ANSIBLE_TEST_REMOTE_DEBUGGER_DEBUGPY' in os.environ else 'pydevd'

    settings: DebugpySettings | PyDevDSettings
    if debug_type == 'debugpy':
        value = os.environ.get('ANSIBLE_TEST_REMOTE_DEBUGGER_DEBUGPY') or '{}'
        settings = parse_debugpy_debugger_settings(value)
        args.metadata.debugpy_settings = settings
    else:
        value = os.environ.get('ANSIBLE_TEST_REMOTE_DEBUGGER_PYDEVD') or '{}'
        settings = parse_pydevd_debugger_settings(value)
        args.metadata.pydevd_settings = settings

    display.info(f'>>> Debugger Settings\n{json.dumps(dataclasses.asdict(settings), indent=4)}', verbosity=3)


@cache
def detect_pydevd_port() -> int | None:
    """Return the port for the pydevd instance hosting this process, or `None` if not detected."""
    current_process = get_current_process_cached()
    args = current_process.args

    if any('/pydevd.py' in arg for arg in args) and (port_idx := args.index('--port')):
        port = int(args[port_idx + 1])
        display.info(f'Detected pydevd debugger port {port}.', verbosity=1)
        return port

    return None


@cache
def detect_pycharm_version() -> str | None:
    """Return the version of PyCharm running ansible-test, or `None` if PyCharm was not detected. The result is cached."""
    if pycharm := detect_pycharm_process():
        output = raw_command([pycharm.args[0], '--version'], capture=True)[0]

        if match := re.search('^Build #PY-(?P<version>[0-9.]+)$', output, flags=re.MULTILINE):
            version = match.group('version')
            display.info(f'Detected PyCharm version {version}.', verbosity=1)
            return version

    display.warning('Skipping installation of `pydevd-pycharm` since the running PyCharm version could not be detected.')

    return None


@cache
def detect_pycharm_process() -> Process | None:
    """Return the PyCharm process running ansible-test, or `None` if PyCharm was not detected. The result is cached."""
    current_process = get_current_process_cached()
    parent = current_process.parent

    while parent:
        if parent.path.name == 'pycharm':
            return parent

        parent = parent.parent

    return None


@cache
def get_current_process_cached() -> Process:
    """Return the current process. The result is cached."""
    return get_current_process()


def detect_debugpy_port() -> int | None:
    """Return the port for the debugpy instance hosting this process, or `None` if not detected."""
    return _get_debugpy_cli_options()[0]


def get_debugpy_access_token() -> str | None:
    """Return the access token for the debugpy instance hosting this process, or `None` if not detected."""
    return _get_debugpy_cli_options()[1]


@cache
def _get_debugpy_cli_options() -> tuple[int | None, str | None]:
    if not (HAS_DEBUGPY and _debugpy.is_client_connected()):
        return (None, None)

    # get_cli_options is the new public API introduced after debugpy 1.8.15.
    # We should remove the _debugpy_cli fallback once the new version is released.
    if hasattr(_debugpy, 'get_cli_options'):
        opts = _debugpy.get_cli_options()
    else:
        opts = _debugpy_cli.options

    return opts.address[1], opts.adapter_access_token
