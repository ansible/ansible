"""Provides compatibility with first-generation host delegation options in ansible-test."""
from __future__ import annotations

import argparse
import dataclasses
import enum
import os
import types
import typing as t

from ..constants import (
    CONTROLLER_PYTHON_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)

from ..util import (
    ApplicationError,
    display,
    filter_args,
    sorted_versions,
    str_to_version,
)

from ..docker_util import (
    docker_available,
)

from ..completion import (
    DOCKER_COMPLETION,
    REMOTE_COMPLETION,
    filter_completion,
)

from ..host_configs import (
    ControllerConfig,
    ControllerHostConfig,
    DockerConfig,
    FallbackDetail,
    FallbackReason,
    HostConfig,
    HostContext,
    HostSettings,
    NativePythonConfig,
    NetworkInventoryConfig,
    NetworkRemoteConfig,
    OriginConfig,
    PosixRemoteConfig,
    VirtualPythonConfig,
    WindowsInventoryConfig,
    WindowsRemoteConfig,
)

from ..data import (
    data_context,
)


def filter_python(version, versions):  # type: (t.Optional[str], t.Optional[t.List[str]]) -> t.Optional[str]
    """If a Python version is given and is in the given version list, return that Python version, otherwise return None."""
    return version if version in versions else None


def controller_python(version):  # type: (t.Optional[str]) -> t.Optional[str]
    """If a Python version is given and is supported by the controller, return that Python version, otherwise return None."""
    return filter_python(version, CONTROLLER_PYTHON_VERSIONS)


def get_fallback_remote_controller():  # type: () -> str
    """Return the remote fallback platform for the controller."""
    platform = 'freebsd'  # lower cost than RHEL and macOS
    candidates = [item for item in filter_completion(REMOTE_COMPLETION).values() if item.controller_supported and item.platform == platform]
    fallback = sorted(candidates, key=lambda value: str_to_version(value.version), reverse=True)[0]
    return fallback.name


def get_option_name(name):  # type: (str) -> str
    """Return a command-line option name from the given option name."""
    if name == 'targets':
        name = 'target'

    return f'--{name.replace("_", "-")}'


class PythonVersionUnsupportedError(ApplicationError):
    """A Python version was requested for a context which does not support that version."""
    def __init__(self, context, version, versions):
        super().__init__(f'Python {version} is not supported by environment `{context}`. Supported Python version(s) are: {", ".join(versions)}')


class PythonVersionUnspecifiedError(ApplicationError):
    """A Python version was not specified for a context which is unknown, thus the Python version is unknown."""
    def __init__(self, context):
        super().__init__(f'A Python version was not specified for environment `{context}`. Use the `--python` option to specify a Python version.')


class ControllerNotSupportedError(ApplicationError):
    """Option(s) were specified which do not provide support for the controller and would be ignored because they are irrelevant for the target."""
    def __init__(self, context):
        super().__init__(f'Environment `{context}` does not provide a Python version supported by the controller.')


class OptionsConflictError(ApplicationError):
    """Option(s) were specified which conflict with other options."""
    def __init__(self, first, second):
        super().__init__(f'Options `{" ".join(first)}` cannot be combined with options `{" ".join(second)}`.')


@dataclasses.dataclass(frozen=True)
class LegacyHostOptions:
    """Legacy host options used prior to the availability of separate controller and target host configuration."""
    python: t.Optional[str] = None
    python_interpreter: t.Optional[str] = None
    local: t.Optional[bool] = None
    venv: t.Optional[bool] = None
    venv_system_site_packages: t.Optional[bool] = None
    remote: t.Optional[str] = None
    remote_provider: t.Optional[str] = None
    docker: t.Optional[str] = None
    docker_privileged: t.Optional[bool] = None
    docker_seccomp: t.Optional[str] = None
    docker_memory: t.Optional[int] = None
    windows: t.Optional[t.List[str]] = None
    platform: t.Optional[t.List[str]] = None
    platform_collection: t.Optional[t.List[t.Tuple[str, str]]] = None
    platform_connection: t.Optional[t.List[t.Tuple[str, str]]] = None
    inventory: t.Optional[str] = None

    @staticmethod
    def create(namespace):  # type: (t.Union[argparse.Namespace, types.SimpleNamespace]) -> LegacyHostOptions
        """Create legacy host options from the given namespace."""
        kwargs = {field.name: getattr(namespace, field.name, None) for field in dataclasses.fields(LegacyHostOptions)}

        if kwargs['python'] == 'default':
            kwargs['python'] = None

        return LegacyHostOptions(**kwargs)

    @staticmethod
    def purge_namespace(namespace):  # type: (t.Union[argparse.Namespace, types.SimpleNamespace]) -> None
        """Purge legacy host options fields from the given namespace."""
        for field in dataclasses.fields(LegacyHostOptions):   # type: dataclasses.Field
            if hasattr(namespace, field.name):
                delattr(namespace, field.name)

    @staticmethod
    def purge_args(args):  # type: (t.List[str]) -> t.List[str]
        """Purge legacy host options from the given command line arguments."""
        fields = dataclasses.fields(LegacyHostOptions)  # type: t.Tuple[dataclasses.Field, ...]
        filters = {get_option_name(field.name): 0 if field.type is t.Optional[bool] else 1 for field in fields}  # type: t.Dict[str, int]

        return filter_args(args, filters)

    def get_options_used(self):  # type: () -> t.Tuple[str, ...]
        """Return a tuple of the command line options used."""
        fields = dataclasses.fields(self)  # type: t.Tuple[dataclasses.Field, ...]
        options = tuple(sorted(get_option_name(field.name) for field in fields if getattr(self, field.name)))
        return options


class TargetMode(enum.Enum):
    """Type of provisioning to use for the targets."""
    WINDOWS_INTEGRATION = enum.auto()  # windows-integration
    NETWORK_INTEGRATION = enum.auto()  # network-integration
    POSIX_INTEGRATION = enum.auto()  # integration
    SANITY = enum.auto()  # sanity
    UNITS = enum.auto()  # units
    SHELL = enum.auto()  # shell
    NO_TARGETS = enum.auto()  # coverage

    @property
    def one_host(self):
        """Return True if only one host (the controller) should be used, otherwise return False."""
        return self in (TargetMode.SANITY, TargetMode.UNITS, TargetMode.NO_TARGETS)

    @property
    def no_fallback(self):
        """Return True if no fallback is acceptable for the controller (due to options not applying to the target), otherwise return False."""
        return self in (TargetMode.WINDOWS_INTEGRATION, TargetMode.NETWORK_INTEGRATION, TargetMode.NO_TARGETS)

    @property
    def multiple_pythons(self):
        """Return True if multiple Python versions are allowed, otherwise False."""
        return self in (TargetMode.SANITY, TargetMode.UNITS)

    @property
    def has_python(self):
        """Return True if this mode uses Python, otherwise False."""
        return self in (TargetMode.POSIX_INTEGRATION, TargetMode.SANITY, TargetMode.UNITS, TargetMode.SHELL)


def convert_legacy_args(
        argv,  # type: t.List[str]
        args,  # type: t.Union[argparse.Namespace, types.SimpleNamespace]
        mode,  # type: TargetMode
):  # type: (...) -> HostSettings
    """Convert pre-split host arguments in the given namespace to their split counterparts."""
    old_options = LegacyHostOptions.create(args)
    old_options.purge_namespace(args)

    new_options = [
        '--controller',
        '--target',
        '--target-python',
    ]

    used_old_options = old_options.get_options_used()
    used_new_options = [name for name in new_options if name in argv]

    if used_old_options:
        if used_new_options:
            raise OptionsConflictError(used_old_options, used_new_options)

        controller, targets, controller_fallback = get_legacy_host_config(mode, old_options)

        if controller_fallback:
            if mode.one_host:
                display.info(controller_fallback.message, verbosity=1)
            else:
                display.warning(controller_fallback.message)

        used_default_pythons = mode in (TargetMode.SANITY, TargetMode.UNITS) and not native_python(old_options)
    else:
        controller = args.controller or OriginConfig()
        controller_fallback = None

        if mode == TargetMode.NO_TARGETS:
            targets = []
            used_default_pythons = False
        elif args.targets:
            targets = args.targets
            used_default_pythons = False
        else:
            targets = default_targets(mode, controller)
            used_default_pythons = mode in (TargetMode.SANITY, TargetMode.UNITS)

    args.controller = controller
    args.targets = targets

    if used_default_pythons:
        targets = t.cast(t.List[ControllerConfig], targets)
        skipped_python_versions = sorted_versions(list(set(SUPPORTED_PYTHON_VERSIONS) - {target.python.version for target in targets}))
    else:
        skipped_python_versions = []

    filtered_args = old_options.purge_args(argv)
    filtered_args = filter_args(filtered_args, {name: 1 for name in new_options})

    host_settings = HostSettings(
        controller=controller,
        targets=targets,
        skipped_python_versions=skipped_python_versions,
        filtered_args=filtered_args,
        controller_fallback=controller_fallback,
    )

    return host_settings


def controller_targets(
        mode,  # type: TargetMode
        options,  # type: LegacyHostOptions
        controller,  # type: ControllerHostConfig
):  # type: (...) -> t.List[ControllerConfig]
    """Return the configuration for controller targets."""
    python = native_python(options)

    if python:
        targets = [ControllerConfig(python=python)]
    else:
        targets = default_targets(mode, controller)

    return targets


def native_python(options):  # type: (LegacyHostOptions) -> t.Optional[NativePythonConfig]
    """Return a NativePythonConfig for the given version if it is not None, otherwise return None."""
    if not options.python and not options.python_interpreter:
        return None

    return NativePythonConfig(version=options.python, path=options.python_interpreter)


def get_legacy_host_config(
        mode,  # type: TargetMode
        options,  # type: LegacyHostOptions
):  # type: (...) -> t.Tuple[HostConfig, t.List[HostConfig], t.Optional[FallbackDetail]]
    """
    Returns controller and target host configs derived from the provided legacy host options.
    The goal is to match the original behavior, by using non-split testing whenever possible.
    When the options support the controller, use the options for the controller and use ControllerConfig for the targets.
    When the options do not support the controller, use the options for the targets and use a default controller config influenced by the options.
    """
    venv_fallback = 'venv/default'
    docker_fallback = 'default'
    remote_fallback = get_fallback_remote_controller()

    controller_fallback = None  # type: t.Optional[t.Tuple[str, str, FallbackReason]]

    if options.venv:
        if controller_python(options.python) or not options.python:
            controller = OriginConfig(python=VirtualPythonConfig(version=options.python or 'default', system_site_packages=options.venv_system_site_packages))
        else:
            controller_fallback = f'origin:python={venv_fallback}', f'--venv --python {options.python}', FallbackReason.PYTHON
            controller = OriginConfig(python=VirtualPythonConfig(version='default', system_site_packages=options.venv_system_site_packages))

        if mode in (TargetMode.SANITY, TargetMode.UNITS):
            targets = controller_targets(mode, options, controller)

            # Target sanity tests either have no Python requirements or manage their own virtual environments.
            # Thus there is no point in setting up virtual environments ahead of time for them.

            if mode == TargetMode.UNITS:
                targets = [ControllerConfig(python=VirtualPythonConfig(version=target.python.version, path=target.python.path,
                                                                       system_site_packages=options.venv_system_site_packages)) for target in targets]
        else:
            targets = [ControllerConfig(python=VirtualPythonConfig(version=options.python or 'default',
                                                                   system_site_packages=options.venv_system_site_packages))]
    elif options.docker:
        docker_config = filter_completion(DOCKER_COMPLETION).get(options.docker)

        if docker_config:
            if options.python and options.python not in docker_config.supported_pythons:
                raise PythonVersionUnsupportedError(f'--docker {options.docker}', options.python, docker_config.supported_pythons)

            if docker_config.controller_supported:
                if controller_python(options.python) or not options.python:
                    controller = DockerConfig(name=options.docker, python=native_python(options),
                                              privileged=options.docker_privileged, seccomp=options.docker_seccomp, memory=options.docker_memory)
                    targets = controller_targets(mode, options, controller)
                else:
                    controller_fallback = f'docker:{options.docker}', f'--docker {options.docker} --python {options.python}', FallbackReason.PYTHON
                    controller = DockerConfig(name=options.docker)
                    targets = controller_targets(mode, options, controller)
            else:
                controller_fallback = f'docker:{docker_fallback}', f'--docker {options.docker}', FallbackReason.ENVIRONMENT
                controller = DockerConfig(name=docker_fallback)
                targets = [DockerConfig(name=options.docker, python=native_python(options),
                                        privileged=options.docker_privileged, seccomp=options.docker_seccomp, memory=options.docker_memory)]
        else:
            if not options.python:
                raise PythonVersionUnspecifiedError(f'--docker {options.docker}')

            if controller_python(options.python):
                controller = DockerConfig(name=options.docker, python=native_python(options),
                                          privileged=options.docker_privileged, seccomp=options.docker_seccomp, memory=options.docker_memory)
                targets = controller_targets(mode, options, controller)
            else:
                controller_fallback = f'docker:{docker_fallback}', f'--docker {options.docker} --python {options.python}', FallbackReason.PYTHON
                controller = DockerConfig(name=docker_fallback)
                targets = [DockerConfig(name=options.docker, python=native_python(options),
                                        privileged=options.docker_privileged, seccomp=options.docker_seccomp, memory=options.docker_memory)]
    elif options.remote:
        remote_config = filter_completion(REMOTE_COMPLETION).get(options.remote)
        context, reason = None, None

        if remote_config:
            if options.python and options.python not in remote_config.supported_pythons:
                raise PythonVersionUnsupportedError(f'--remote {options.remote}', options.python, remote_config.supported_pythons)

            if remote_config.controller_supported:
                if controller_python(options.python) or not options.python:
                    controller = PosixRemoteConfig(name=options.remote, python=native_python(options), provider=options.remote_provider)
                    targets = controller_targets(mode, options, controller)
                else:
                    controller_fallback = f'remote:{options.remote}', f'--remote {options.remote} --python {options.python}', FallbackReason.PYTHON
                    controller = PosixRemoteConfig(name=options.remote, provider=options.remote_provider)
                    targets = controller_targets(mode, options, controller)
            else:
                context, reason = f'--remote {options.remote}', FallbackReason.ENVIRONMENT
                controller = None
                targets = [PosixRemoteConfig(name=options.remote, python=native_python(options), provider=options.remote_provider)]
        elif mode == TargetMode.SHELL and options.remote.startswith('windows/'):
            if options.python and options.python not in CONTROLLER_PYTHON_VERSIONS:
                raise ControllerNotSupportedError(f'--python {options.python}')

            controller = OriginConfig(python=native_python(options))
            targets = [WindowsRemoteConfig(name=options.remote, provider=options.remote_provider)]
        else:
            if not options.python:
                raise PythonVersionUnspecifiedError(f'--remote {options.remote}')

            if controller_python(options.python):
                controller = PosixRemoteConfig(name=options.remote, python=native_python(options), provider=options.remote_provider)
                targets = controller_targets(mode, options, controller)
            else:
                context, reason = f'--remote {options.remote} --python {options.python}', FallbackReason.PYTHON
                controller = None
                targets = [PosixRemoteConfig(name=options.remote, python=native_python(options), provider=options.remote_provider)]

        if not controller:
            if docker_available():
                controller_fallback = f'docker:{docker_fallback}', context, reason
                controller = DockerConfig(name=docker_fallback)
            else:
                controller_fallback = f'remote:{remote_fallback}', context, reason
                controller = PosixRemoteConfig(name=remote_fallback)
    else:  # local/unspecified
        # There are several changes in behavior from the legacy implementation when using no delegation (or the `--local` option).
        # These changes are due to ansible-test now maintaining consistency between its own Python and that of controller Python subprocesses.
        #
        # 1) The `--python-interpreter` option (if different from sys.executable) now affects controller subprocesses and triggers re-execution of ansible-test.
        #    Previously this option was completely ignored except when used with the `--docker` or `--remote` options.
        # 2) The `--python` option now triggers re-execution of ansible-test if it differs from sys.version_info.
        #    Previously it affected Python subprocesses, but not ansible-test itself.

        if controller_python(options.python) or not options.python:
            controller = OriginConfig(python=native_python(options))
            targets = controller_targets(mode, options, controller)
        else:
            controller_fallback = 'origin:python=default', f'--python {options.python}', FallbackReason.PYTHON
            controller = OriginConfig()
            targets = controller_targets(mode, options, controller)

    if controller_fallback:
        controller_option, context, reason = controller_fallback

        if mode.no_fallback:
            raise ControllerNotSupportedError(context)

        fallback_detail = FallbackDetail(
            reason=reason,
            message=f'Using `--controller {controller_option}` since `{context}` does not support the controller.',
        )
    else:
        fallback_detail = None

    if mode.one_host and any(not isinstance(target, ControllerConfig) for target in targets):
        raise ControllerNotSupportedError(controller_fallback[1])

    if mode == TargetMode.NO_TARGETS:
        targets = []
    else:
        targets = handle_non_posix_targets(mode, options, targets)

    return controller, targets, fallback_detail


def handle_non_posix_targets(
    mode,  # type: TargetMode
    options,  # type: LegacyHostOptions
    targets,  # type: t.List[HostConfig]
):  # type: (...) -> t.List[HostConfig]
    """Return a list of non-POSIX targets if the target mode is non-POSIX."""
    if mode == TargetMode.WINDOWS_INTEGRATION:
        if options.windows:
            targets = [WindowsRemoteConfig(name=f'windows/{version}', provider=options.remote_provider) for version in options.windows]
        else:
            targets = [WindowsInventoryConfig(path=options.inventory)]
    elif mode == TargetMode.NETWORK_INTEGRATION:
        if options.platform:
            targets = [NetworkRemoteConfig(name=platform, provider=options.remote_provider) for platform in options.platform]

            for platform, collection in options.platform_collection or []:
                for entry in targets:
                    if entry.platform == platform:
                        entry.collection = collection

            for platform, connection in options.platform_connection or []:
                for entry in targets:
                    if entry.platform == platform:
                        entry.connection = connection
        else:
            targets = [NetworkInventoryConfig(path=options.inventory)]

    return targets


def default_targets(
    mode,  # type: TargetMode
    controller,  # type: ControllerHostConfig
):  # type: (...) -> t.List[HostConfig]
    """Return a list of default targets for the given target mode."""
    if mode == TargetMode.WINDOWS_INTEGRATION:
        targets = [WindowsInventoryConfig(path=os.path.abspath(os.path.join(data_context().content.integration_path, 'inventory.winrm')))]
    elif mode == TargetMode.NETWORK_INTEGRATION:
        targets = [NetworkInventoryConfig(path=os.path.abspath(os.path.join(data_context().content.integration_path, 'inventory.networking')))]
    elif mode.multiple_pythons:
        targets = controller.get_default_targets(HostContext(controller_config=controller))
    else:
        targets = [ControllerConfig()]

    return targets
