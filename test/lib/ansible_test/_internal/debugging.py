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

from .processes import (
    Process,
    get_current_process,
)

from .config import (
    EnvironmentConfig,
)

from .metadata import (
    DebuggerSettings,
    DebuggerFlags,
)

from . import (
    data_context,
    CommonConfig,
)

HAS_DEBUGPY = False
try:
    import debugpy as _debugpy
    from debugpy.server import cli as _debugpy_cli

    HAS_DEBUGPY = True
except ImportError:
    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class PyDevDSettings(DebuggerSettings):
    debug_type: str = 'pydevd'
    package: str | None = None  # Auto-detected in post_init
    port: int = 5678

    module: str = ''  # Default set in post_init
    """
    The Python module to import.
    This should be pydevd or a derivative.
    If not provided it will be auto-detected.
    """

    args: list[str] = dataclasses.field(default_factory=list)
    """
    Arguments to pass to `pydevd` on the command line.
    Used for running Ansible CLI programs only.
    The `--client` and `--port` options will be provided by ansible-test.
    """

    settrace: dict[str, t.Any] = dataclasses.field(default_factory=dict)
    """
    Options to pass to the `{module}.settrace` method.
    Used for running or ansible-test or AnsiballZ modules only.
    The `host` and `port` options will be provided by ansible-test.
    The `suspend` option defaults to `False`.
    """

    def __post_init__(self) -> None:
        if not self.module:
            if not self.package or 'pydevd-pycharm' in self.package:
                module = 'pydevd_pycharm'
            else:
                module = 'pydevd'

            object.__setattr__(self, 'module', module)

        if self.package is None:
            if self.module == 'pydevd_pycharm':
                if pycharm_version := detect_pycharm_version():
                    package = f'pydevd-pycharm~={pycharm_version}'
                else:
                    package = None
            else:
                package = 'pydevd'

            object.__setattr__(self, 'package', package)

        self.settrace.setdefault('suspend', False)

        if port := detect_pydevd_port():
            object.__setattr__(self, 'port', port)

            if detect_pycharm_process():
                # This only works with the default PyCharm debugger.
                # Using it with PyCharm's "Python Debug Server" results in hangs in Ansible workers.
                # Further investigation is required to understand the cause.
                self.args + ['--multiprocess']


    def activate_debugger(self, host: str, port: int) -> None:
        module_name = self.module
        debugging_module = importlib.import_module(module_name)
        debugging_module.settrace(**self._get_settrace_arguments(host, port))

    def get_ansiballz_config(self) -> dict[str, object]:
        return dict(settrace=self.settrace)

    def get_cli_arguments(self, host: str, port: int) -> list[str]:
        return ['-m', 'pydevd', '--client', host, '--port', str(port)] + self.args + ['--file']

    def get_environment_variables(self, source_mapping: dict[str, str]) -> dict[str, str]:
        return dict(
            PATHS_FROM_ECLIPSE_TO_PYTHON=json.dumps(list(source_mapping.items())),
            PYDEVD_DISABLE_FILE_VALIDATION="1",
        )

    def _get_settrace_arguments(self, host: str, port: int) -> dict[str, object]:
        """Get settrace arguments for pydevd."""
        return self.settrace | dict(
            host=host,
            port=port,
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class DebugpySettings(DebuggerSettings):
    debug_type: str = 'debugpy'
    package: str | None = 'debugpy'
    port: int = 5678

    args: list[str] = dataclasses.field(default_factory=list)
    """
    Arguments to pass to `debugpy` on the command line.
    Used for running Ansible CLI programs only.
    The `--connect`, `--parent-session-pid`, and `--adapter-access-token` options will be provided by ansible-test.
    """

    connect: dict[str, object] = dataclasses.field(default_factory=dict)
    """
    Options to pass to the `debugpy.connect` method.
    Used for running or ansible-test or AnsiballZ modules only.
    The endpoint addr, `access_token`, and `parent_session_pid` options will be provided by ansible-test.
    """

    def __post_init__(self) -> None:
        self.connect.setdefault('parent_session_pid', os.getpid())

        if token := get_debugpy_access_token():
            self.connect.setdefault('access_token', token)

        if port := detect_debugpy_port():
            object.__setattr__(self, 'port', port)

    def activate_debugger(self, host: str, port: int) -> None:
        if not HAS_DEBUGPY:
            raise ImportError("debugpy is not installed, cannot activate debugger.")

        _debugpy.connect((host, port), **self.connect)

    def get_ansiballz_config(self) -> dict[str, object]:
        return dict(connect=self.connect)

    def get_cli_arguments(self, host: str, port: int) -> list[str]:
        cli_args = ['-m', 'debugpy', '--connect', f"{host}:{port}", "--parent-session-pid", str(self.connect['parent_session_pid'])]
        if access_token := self.connect.get('access_token'):
            cli_args += ['--adapter-access-token', access_token]
        if self.args:
            cli_args += self.args

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


def parse_debugger_settings(value: str, debugger_type: type[DebuggerSettings] | None) -> DebuggerSettings:
    """Parse remote debugger settings and apply defaults."""
    try:
        debugger_values = json.loads(value)
        if not debugger_type:
            selected_type = debugger_values.get('debug_type', None)
            match selected_type:
                case 'pydevd':
                    debugger_type = PyDevDSettings
                case 'debugpy':
                    debugger_type = DebugpySettings
                case _:
                    raise ApplicationError(f"Invalid debugger setting: unsupported debug_type '{selected_type}' for remote debugging.")

        return debugger_type(**debugger_values)
    except ApplicationError:
        raise
    except Exception as ex:
        raise ApplicationError(f"Invalid debugger settings: {ex}") from ex


def load_debugger_settings(args: EnvironmentConfig) -> None:
    """Load the remote debugger settings."""
    debugger_type: type[DebuggerSettings] | None = None

    if args.metadata.debugger_flags.on_demand:
        # On-demand debugging only enables debugging if we're running under a debugger, otherwise it's a no-op.

        if detect_pydevd_port():
            debugger_type = PyDevDSettings
        elif detect_debugpy_port():
            debugger_type = DebugpySettings
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

    value = os.environ.get('ANSIBLE_TEST_REMOTE_DEBUGGER') or '{}'
    settings = parse_debugger_settings(value, debugger_type)

    display.info(f'>>> Debugger Settings\n{json.dumps(dataclasses.asdict(settings), indent=4)}', verbosity=3)

    args.metadata.debugger_settings = settings


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


@cache
def detect_debugpy_port() -> int | None:
    """Return the port for the debugpy instance hosting this process, or `None` if not detected."""
    if HAS_DEBUGPY and _debugpy.is_client_connected():
        return _debugpy_cli.options.address[1]

    return None

@cache
def get_debugpy_access_token() -> str | None:
    """Return the access token for the debugpy instance hosting this process, or `None` if not detected."""
    if HAS_DEBUGPY and _debugpy.is_client_connected():
        return _debugpy_cli.options.adapter_access_token

    return None
