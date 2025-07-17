"""Setup and configure remote debugging."""

from __future__ import annotations

import abc
import dataclasses
import importlib
import json
import os
import re
import sys
import typing as t

from .util import (
    cache,
    display,
    raw_command,
    ApplicationError,
    get_subclasses,
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
    DebuggerFlags,
)

from .data import (
    data_context,
)


class DebuggerProfile(t.Protocol):
    """Protocol for debugger profiles."""

    @property
    def debugger_host(self) -> str:
        """The hostname to expose to the debugger."""

    @property
    def debugger_port(self) -> int:
        """The port to expose to the debugger."""

    def get_source_mapping(self) -> dict[str, str]:
        """The source mapping to expose to the debugger."""


@dataclasses.dataclass(frozen=True, kw_only=True)
class DebuggerSettings(metaclass=abc.ABCMeta):
    """Common debugger settings."""

    port: int = 5678
    """
    The port on the origin host which is listening for incoming connections from the debugger.
    SSH port forwarding will be automatically configured for non-local hosts to connect to this port as needed.
    """

    def as_dict(self) -> dict[str, object]:
        """Convert this instance to a dict."""
        data = dataclasses.asdict(self)
        data.update(__type__=self.__class__.__name__)

        return data

    @classmethod
    def from_dict(cls, value: dict[str, t.Any]) -> t.Self:
        """Load an instance from a dict."""
        debug_cls = globals()[value.pop('__type__')]

        return debug_cls(**value)

    @classmethod
    def get_debug_type(cls) -> str:
        """Return the name for this debugger."""
        return cls.__name__.removesuffix('Settings').lower()

    @classmethod
    def get_config_env_var_name(cls) -> str:
        """Return the name of the environment variable used to customize settings for this debugger."""
        return f'ANSIBLE_TEST_REMOTE_DEBUGGER_{cls.get_debug_type().upper()}'

    @classmethod
    def parse(cls, value: str) -> t.Self:
        """Parse debugger settings from the given JSON and apply defaults."""
        try:
            settings = cls(**json.loads(value))
        except Exception as ex:
            raise ApplicationError(f"Invalid {cls.get_debug_type()} settings: {ex}") from ex

        return cls.apply_defaults(settings)

    @classmethod
    @abc.abstractmethod
    def is_active(cls) -> bool:
        """Detect if the debugger is active."""

    @classmethod
    @abc.abstractmethod
    def apply_defaults(cls, settings: t.Self) -> t.Self:
        """Apply defaults to the given settings."""

    @abc.abstractmethod
    def get_python_package(self) -> str:
        """The Python package to install for debugging."""

    @abc.abstractmethod
    def activate_debugger(self, profile: DebuggerProfile) -> None:
        """Activate the debugger in ansible-test after delegation."""

    @abc.abstractmethod
    def get_ansiballz_config(self, profile: DebuggerProfile) -> dict[str, object]:
        """Gets the extra configuration data for the AnsiballZ extension module."""

    @abc.abstractmethod
    def get_cli_arguments(self, profile: DebuggerProfile) -> list[str]:
        """Get command line arguments for the debugger when running Ansible CLI programs."""

    @abc.abstractmethod
    def get_environment_variables(self, profile: DebuggerProfile) -> dict[str, str]:
        """Get environment variables needed to configure the debugger for debugging."""


@dataclasses.dataclass(frozen=True, kw_only=True)
class PydevdSettings(DebuggerSettings):
    """Settings for the pydevd debugger."""

    package: str | None = None
    """
    The Python package to install for debugging.
    If `None` then the package will be auto-detected.
    If an empty string, then no package will be installed.
    """

    module: str | None = None
    """
    The Python module to import for debugging.
    This should be pydevd or a derivative.
    If not provided it will be auto-detected.
    """

    settrace: dict[str, object] = dataclasses.field(default_factory=dict)
    """
    Options to pass to the `{module}.settrace` method.
    Used for running AnsiballZ modules only.
    The `host` and `port` options will be provided by ansible-test.
    The `suspend` option defaults to `False`.
    """

    args: list[str] = dataclasses.field(default_factory=list)
    """
    Arguments to pass to `pydevd` on the command line.
    Used for running Ansible CLI programs only.
    The `--client` and `--port` options will be provided by ansible-test.
    """

    @classmethod
    def is_active(cls) -> bool:
        return detect_pydevd_port() is not None

    @classmethod
    def apply_defaults(cls, settings: t.Self) -> t.Self:
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

    def get_python_package(self) -> str:
        if self.package is None and self.module == 'pydevd_pycharm':
            display.warning('Skipping installation of `pydevd-pycharm` since the running PyCharm version was not detected.')

        return self.package

    def activate_debugger(self, profile: DebuggerProfile) -> None:
        debugging_module = importlib.import_module(self.module)
        debugging_module.settrace(**self._get_settrace_arguments(profile))

    def get_ansiballz_config(self, profile: DebuggerProfile) -> dict[str, object]:
        return dict(
            module=self.module,
            settrace=self._get_settrace_arguments(profile),
            source_mapping=profile.get_source_mapping(),
        )

    def get_cli_arguments(self, profile: DebuggerProfile) -> list[str]:
        # Although `pydevd_pycharm` can be used to invoke `settrace`, it cannot be used to run the debugger on the command line.
        return ['-m', 'pydevd', '--client', profile.debugger_host, '--port', str(profile.debugger_port)] + self.args + ['--file']

    def get_environment_variables(self, profile: DebuggerProfile) -> dict[str, str]:
        return dict(
            PATHS_FROM_ECLIPSE_TO_PYTHON=json.dumps(list(profile.get_source_mapping().items())),
            PYDEVD_DISABLE_FILE_VALIDATION="1",
        )

    def _get_settrace_arguments(self, profile: DebuggerProfile) -> dict[str, object]:
        """Get settrace arguments for pydevd."""
        return self.settrace | dict(
            host=profile.debugger_host,
            port=profile.debugger_port,
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class DebugpySettings(DebuggerSettings):
    """Settings for the debugpy debugger."""

    connect: dict[str, object] = dataclasses.field(default_factory=dict)
    """
    Options to pass to the `debugpy.connect` method.
    Used for running AnsiballZ modules and ansible-test after delegation.
    The endpoint addr, `access_token`, and `parent_session_pid` options will be provided by ansible-test.
    """

    args: list[str] = dataclasses.field(default_factory=list)
    """
    Arguments to pass to `debugpy` on the command line.
    Used for running Ansible CLI programs only.
    The `--connect`, `--adapter-access-token`, and `--parent-session-pid` options will be provided by ansible-test.
    """

    @classmethod
    def is_active(cls) -> bool:
        return detect_debugpy_options() is not None

    @classmethod
    def apply_defaults(cls, settings: t.Self) -> t.Self:
        if options := detect_debugpy_options():
            settings = dataclasses.replace(settings, port=options.port)
            settings.connect.update(
                access_token=options.adapter_access_token,
                parent_session_pid=os.getpid(),
            )
        else:
            display.warning('Debugging will be limited to the first connection. Run ansible-test under debugpy to support multiple connections.')

        return settings

    def get_python_package(self) -> str:
        return 'debugpy'

    def activate_debugger(self, profile: DebuggerProfile) -> None:
        import debugpy  # pylint: disable=import-error

        debugpy.connect((profile.debugger_host, profile.debugger_port), **self.connect)

    def get_ansiballz_config(self, profile: DebuggerProfile) -> dict[str, object]:
        return dict(
            host=profile.debugger_host,
            port=profile.debugger_port,
            connect=self.connect,
            source_mapping=profile.get_source_mapping(),
        )

    def get_cli_arguments(self, profile: DebuggerProfile) -> list[str]:
        cli_args = ['-m', 'debugpy', '--connect', f"{profile.debugger_host}:{profile.debugger_port}"]

        if access_token := self.connect.get('access_token'):
            cli_args += ['--adapter-access-token', str(access_token)]

        if session_pid := self.connect.get('parent_session_pid'):
            cli_args += ['--parent-session-pid', str(session_pid)]

        if self.args:
            cli_args += self.args

        return cli_args

    def get_environment_variables(self, profile: DebuggerProfile) -> dict[str, str]:
        return dict(
            PATHS_FROM_ECLIPSE_TO_PYTHON=json.dumps(list(profile.get_source_mapping().items())),
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


def load_debugger_settings(args: EnvironmentConfig) -> None:
    """Load the remote debugger settings."""
    use_debugger: type[DebuggerSettings] | None = None

    if args.metadata.debugger_flags.on_demand:
        # On-demand debugging only enables debugging if we're running under a debugger, otherwise it's a no-op.

        for candidate_debugger in get_subclasses(DebuggerSettings):
            if candidate_debugger.is_active():
                use_debugger = candidate_debugger
                break
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

    if not use_debugger:  # detect debug type based on env var
        for candidate_debugger in get_subclasses(DebuggerSettings):
            if candidate_debugger.get_config_env_var_name() in os.environ:
                use_debugger = candidate_debugger
                break
        else:
            display.info('Debugging disabled because no debugger configuration was provided.', verbosity=1)
            args.metadata.debugger_flags = DebuggerFlags.all(False)
            return

    config = os.environ.get(use_debugger.get_config_env_var_name()) or '{}'
    settings = use_debugger.parse(config)
    args.metadata.debugger_settings = settings

    display.info(f'>>> Debugger Settings ({use_debugger.get_debug_type()})\n{json.dumps(dataclasses.asdict(settings), indent=4)}', verbosity=3)


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


@dataclasses.dataclass(frozen=True, kw_only=True)
class DebugpyOptions:
    """Options detected from the debugpy instance hosting this process."""

    port: int
    adapter_access_token: str | None


@cache
def detect_debugpy_options() -> DebugpyOptions | None:
    """Return the options for the debugpy instance hosting this process, or `None` if not detected."""
    if "debugpy" not in sys.modules:
        return None

    import debugpy  # pylint: disable=import-error

    # get_cli_options is the new public API introduced after debugpy 1.8.15.
    # We should remove the debugpy.server cli fallback once the new version is
    # released.
    if hasattr(debugpy, 'get_cli_options'):
        opts = debugpy.get_cli_options()
    else:
        from debugpy.server import cli  # pylint: disable=import-error
        opts = cli.options

    # address can be None if the debugger is not configured through the CLI as
    # we expected.
    if not opts.address:
        return None

    port = opts.address[1]

    display.info(f'Detected debugpy debugger port {port}.', verbosity=1)

    return DebugpyOptions(
        port=port,
        adapter_access_token=opts.adapter_access_token,
    )
