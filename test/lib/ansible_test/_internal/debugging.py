"""Setup and configure remote debugging."""

from __future__ import annotations

import dataclasses
import json
import os
import re

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


def initialize_debugger(args: CommonConfig) -> None:
    """Initialize the debugger settings before delegation."""
    if not isinstance(args, EnvironmentConfig):
        return

    if args.metadata.loaded:
        return  # after delegation

    if collection := data_context().content.collection:
        args.metadata.collection_root = collection.root

    load_debugger_settings(args)


def parse_debugger_settings(value: str) -> DebuggerSettings:
    """Parse remote debugger settings and apply defaults."""
    try:
        settings = DebuggerSettings(**json.loads(value))
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
    if args.metadata.debugger_flags.on_demand:
        # On-demand debugging only enables debugging if we're running under a debugger, otherwise it's a no-op.

        if not detect_pydevd_port():
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
    settings = parse_debugger_settings(value)

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
