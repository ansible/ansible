"""Command line parsing for test environments."""
from __future__ import annotations

import argparse
import enum
import functools
import typing as t

from ..constants import (
    CONTROLLER_PYTHON_VERSIONS,
    REMOTE_PROVIDERS,
    SECCOMP_CHOICES,
    SUPPORTED_PYTHON_VERSIONS,
)

from ..util import (
    REMOTE_ARCHITECTURES,
)

from ..completion import (
    docker_completion,
    network_completion,
    remote_completion,
    windows_completion,
    filter_completion,
)

from ..cli.argparsing import (
    CompositeAction,
    CompositeActionCompletionFinder,
)

from ..cli.argparsing.actions import (
    EnumAction,
)

from ..cli.actions import (
    DelegatedControllerAction,
    NetworkSshTargetAction,
    NetworkTargetAction,
    OriginControllerAction,
    PosixSshTargetAction,
    PosixTargetAction,
    SanityPythonTargetAction,
    UnitsPythonTargetAction,
    WindowsSshTargetAction,
    WindowsTargetAction,
)

from ..cli.compat import (
    TargetMode,
)

from ..config import (
    TerminateMode,
)

from .completers import (
    complete_choices,
    register_completer,
)

from .converters import (
    key_value_type,
)

from .epilog import (
    get_epilog,
)

from ..ci import (
    get_ci_provider,
)


class ControllerMode(enum.Enum):
    """Type of provisioning to use for the controller."""

    NO_DELEGATION = enum.auto()
    ORIGIN = enum.auto()
    DELEGATED = enum.auto()


def add_environments(
    parser: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
    controller_mode: ControllerMode,
    target_mode: TargetMode,
) -> None:
    """Add arguments for the environments used to run ansible-test and commands it invokes."""
    no_environment = controller_mode == ControllerMode.NO_DELEGATION and target_mode == TargetMode.NO_TARGETS

    parser.set_defaults(no_environment=no_environment)

    if no_environment:
        return

    parser.set_defaults(target_mode=target_mode)

    add_global_options(parser, controller_mode)
    add_legacy_environment_options(parser, controller_mode, target_mode)
    action_types = add_composite_environment_options(parser, completer, controller_mode, target_mode)

    sections = [f'{heading}\n{content}'
                for action_type, documentation_state in CompositeAction.documentation_state.items() if action_type in action_types
                for heading, content in documentation_state.sections.items()]

    if not get_ci_provider().supports_core_ci_auth():
        sections.append('Remote provisioning options have been hidden since no Ansible Core CI API key was found.')

    sections.append(get_epilog(completer))

    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.epilog = '\n\n'.join(sections)


def add_global_options(
    parser: argparse.ArgumentParser,
    controller_mode: ControllerMode,
):
    """Add global options for controlling the test environment that work with both the legacy and composite options."""
    global_parser = t.cast(argparse.ArgumentParser, parser.add_argument_group(title='global environment arguments'))

    global_parser.add_argument(
        '--containers',
        metavar='JSON',
        help=argparse.SUPPRESS,
    )

    global_parser.add_argument(
        '--pypi-proxy',
        action='store_true',
        help=argparse.SUPPRESS,
    )

    global_parser.add_argument(
        '--pypi-endpoint',
        metavar='URI',
        help=argparse.SUPPRESS,
    )

    global_parser.add_argument(
        '--requirements',
        action='store_true',
        default=False,
        help='install command requirements',
    )

    add_global_remote(global_parser, controller_mode)
    add_global_docker(global_parser, controller_mode)


def add_composite_environment_options(
    parser: argparse.ArgumentParser,
    completer: CompositeActionCompletionFinder,
    controller_mode: ControllerMode,
    target_mode: TargetMode,
) -> list[t.Type[CompositeAction]]:
    """Add composite options for controlling the test environment."""
    composite_parser = t.cast(argparse.ArgumentParser, parser.add_argument_group(
        title='composite environment arguments (mutually exclusive with "environment arguments" above)'))

    composite_parser.add_argument(
        '--host-path',
        help=argparse.SUPPRESS,
    )

    action_types: list[t.Type[CompositeAction]] = []

    def register_action_type(action_type: t.Type[CompositeAction]) -> t.Type[CompositeAction]:
        """Register the provided composite action type and return it."""
        action_types.append(action_type)
        return action_type

    if controller_mode == ControllerMode.NO_DELEGATION:
        composite_parser.set_defaults(controller=None)
    else:
        register_completer(composite_parser.add_argument(
            '--controller',
            metavar='OPT',
            action=register_action_type(DelegatedControllerAction if controller_mode == ControllerMode.DELEGATED else OriginControllerAction),
            help='configuration for the controller',
        ), completer.completer)

    if target_mode == TargetMode.NO_TARGETS:
        composite_parser.set_defaults(targets=[])
    elif target_mode == TargetMode.SHELL:
        group = composite_parser.add_mutually_exclusive_group()

        register_completer(group.add_argument(
            '--target-posix',
            metavar='OPT',
            action=register_action_type(PosixSshTargetAction),
            help='configuration for the target',
        ), completer.completer)

        suppress = None if get_ci_provider().supports_core_ci_auth() else argparse.SUPPRESS

        register_completer(group.add_argument(
            '--target-windows',
            metavar='OPT',
            action=WindowsSshTargetAction if suppress else register_action_type(WindowsSshTargetAction),
            help=suppress or 'configuration for the target',
        ), completer.completer)

        register_completer(group.add_argument(
            '--target-network',
            metavar='OPT',
            action=NetworkSshTargetAction if suppress else register_action_type(NetworkSshTargetAction),
            help=suppress or 'configuration for the target',
        ), completer.completer)
    else:
        if target_mode.multiple_pythons:
            target_option = '--target-python'
            target_help = 'configuration for the target python interpreter(s)'
        elif target_mode == TargetMode.POSIX_INTEGRATION:
            target_option = '--target'
            target_help = 'configuration for the target'
        else:
            target_option = '--target'
            target_help = 'configuration for the target(s)'

        target_actions = {
            TargetMode.POSIX_INTEGRATION: PosixTargetAction,
            TargetMode.WINDOWS_INTEGRATION: WindowsTargetAction,
            TargetMode.NETWORK_INTEGRATION: NetworkTargetAction,
            TargetMode.SANITY: SanityPythonTargetAction,
            TargetMode.UNITS: UnitsPythonTargetAction,
        }

        target_action = target_actions[target_mode]

        register_completer(composite_parser.add_argument(
            target_option,
            metavar='OPT',
            action=register_action_type(target_action),
            help=target_help,
        ), completer.completer)

    return action_types


def add_legacy_environment_options(
    parser: argparse.ArgumentParser,
    controller_mode: ControllerMode,
    target_mode: TargetMode,
):
    """Add legacy options for controlling the test environment."""
    environment: argparse.ArgumentParser = parser.add_argument_group(  # type: ignore[assignment]  # real type private
        title='environment arguments (mutually exclusive with "composite environment arguments" below)',
    )

    add_environments_python(environment, target_mode)
    add_environments_host(environment, controller_mode, target_mode)


def add_environments_python(
    environments_parser: argparse.ArgumentParser,
    target_mode: TargetMode,
) -> None:
    """Add environment arguments to control the Python version(s) used."""
    python_versions: tuple[str, ...]

    if target_mode.has_python:
        python_versions = SUPPORTED_PYTHON_VERSIONS
    else:
        python_versions = CONTROLLER_PYTHON_VERSIONS

    environments_parser.add_argument(
        '--python',
        metavar='X.Y',
        choices=python_versions + ('default',),
        help='python version: %s' % ', '.join(python_versions),
    )

    environments_parser.add_argument(
        '--python-interpreter',
        metavar='PATH',
        help='path to the python interpreter',
    )


def add_environments_host(
    environments_parser: argparse.ArgumentParser,
    controller_mode: ControllerMode,
    target_mode: TargetMode,
) -> None:
    """Add environment arguments for the given host and argument modes."""
    environments_exclusive_group: argparse.ArgumentParser = environments_parser.add_mutually_exclusive_group()  # type: ignore[assignment]  # real type private

    add_environment_local(environments_exclusive_group)
    add_environment_venv(environments_exclusive_group, environments_parser)

    if controller_mode == ControllerMode.DELEGATED:
        add_environment_remote(environments_exclusive_group, environments_parser, target_mode)
        add_environment_docker(environments_exclusive_group, environments_parser, target_mode)

    if target_mode == TargetMode.WINDOWS_INTEGRATION:
        add_environment_windows(environments_parser)

    if target_mode == TargetMode.NETWORK_INTEGRATION:
        add_environment_network(environments_parser)


def add_environment_network(
    environments_parser: argparse.ArgumentParser,
) -> None:
    """Add environment arguments for running on a windows host."""
    register_completer(environments_parser.add_argument(
        '--platform',
        metavar='PLATFORM',
        action='append',
        help='network platform/version',
    ), complete_network_platform)

    register_completer(environments_parser.add_argument(
        '--platform-collection',
        type=key_value_type,
        metavar='PLATFORM=COLLECTION',
        action='append',
        help='collection used to test platform',
    ), complete_network_platform_collection)

    register_completer(environments_parser.add_argument(
        '--platform-connection',
        type=key_value_type,
        metavar='PLATFORM=CONNECTION',
        action='append',
        help='connection used to test platform',
    ), complete_network_platform_connection)

    environments_parser.add_argument(
        '--inventory',
        metavar='PATH',
        help='path to inventory used for tests',
    )


def add_environment_windows(
    environments_parser: argparse.ArgumentParser,
) -> None:
    """Add environment arguments for running on a windows host."""
    register_completer(environments_parser.add_argument(
        '--windows',
        metavar='VERSION',
        action='append',
        help='windows version',
    ), complete_windows)

    environments_parser.add_argument(
        '--inventory',
        metavar='PATH',
        help='path to inventory used for tests',
    )


def add_environment_local(
    exclusive_parser: argparse.ArgumentParser,
) -> None:
    """Add environment arguments for running on the local (origin) host."""
    exclusive_parser.add_argument(
        '--local',
        action='store_true',
        help='run from the local environment',
    )


def add_environment_venv(
    exclusive_parser: argparse.ArgumentParser,
    environments_parser: argparse.ArgumentParser,
) -> None:
    """Add environment arguments for running in ansible-test managed virtual environments."""
    exclusive_parser.add_argument(
        '--venv',
        action='store_true',
        help='run from a virtual environment',
    )

    environments_parser.add_argument(
        '--venv-system-site-packages',
        action='store_true',
        help='enable system site packages',
    )


def add_global_docker(
    parser: argparse.ArgumentParser,
    controller_mode: ControllerMode,
) -> None:
    """Add global options for Docker."""
    if controller_mode != ControllerMode.DELEGATED:
        parser.set_defaults(
            docker_network=None,
            docker_terminate=None,
            prime_containers=False,
            dev_systemd_debug=False,
            dev_probe_cgroups=None,
        )

        return

    parser.add_argument(
        '--docker-network',
        metavar='NET',
        help='run using the specified network',
    )

    parser.add_argument(
        '--docker-terminate',
        metavar='T',
        default=TerminateMode.ALWAYS,
        type=TerminateMode,
        action=EnumAction,
        help='terminate the container: %(choices)s (default: %(default)s)',
    )

    parser.add_argument(
        '--prime-containers',
        action='store_true',
        help='download containers without running tests',
    )

    # Docker support isn't related to ansible-core-ci.
    # However, ansible-core-ci support is a reasonable indicator that the user may need the `--dev-*` options.
    suppress = None if get_ci_provider().supports_core_ci_auth() else argparse.SUPPRESS

    parser.add_argument(
        '--dev-systemd-debug',
        action='store_true',
        help=suppress or 'enable systemd debugging in containers',
    )

    parser.add_argument(
        '--dev-probe-cgroups',
        metavar='DIR',
        nargs='?',
        const='',
        help=suppress or 'probe container cgroups, with optional log dir',
    )


def add_environment_docker(
    exclusive_parser: argparse.ArgumentParser,
    environments_parser: argparse.ArgumentParser,
    target_mode: TargetMode,
) -> None:
    """Add environment arguments for running in docker containers."""
    if target_mode in (TargetMode.POSIX_INTEGRATION, TargetMode.SHELL):
        docker_images = sorted(filter_completion(docker_completion()))
    else:
        docker_images = sorted(filter_completion(docker_completion(), controller_only=True))

    register_completer(exclusive_parser.add_argument(
        '--docker',
        metavar='IMAGE',
        nargs='?',
        const='default',
        help='run from a docker container',
    ), functools.partial(complete_choices, docker_images))

    environments_parser.add_argument(
        '--docker-privileged',
        action='store_true',
        help='run docker container in privileged mode',
    )

    environments_parser.add_argument(
        '--docker-seccomp',
        metavar='SC',
        choices=SECCOMP_CHOICES,
        help='set seccomp confinement for the test container: %(choices)s',
    )

    environments_parser.add_argument(
        '--docker-memory',
        metavar='INT',
        type=int,
        help='memory limit for docker in bytes',
    )


def add_global_remote(
    parser: argparse.ArgumentParser,
    controller_mode: ControllerMode,
) -> None:
    """Add global options for remote instances."""
    if controller_mode != ControllerMode.DELEGATED:
        parser.set_defaults(
            remote_stage=None,
            remote_endpoint=None,
            remote_terminate=None,
        )

        return

    suppress = None if get_ci_provider().supports_core_ci_auth() else argparse.SUPPRESS

    register_completer(parser.add_argument(
        '--remote-stage',
        metavar='STAGE',
        default='prod',
        help=suppress or 'remote stage to use: prod, dev',
    ), complete_remote_stage)

    parser.add_argument(
        '--remote-endpoint',
        metavar='EP',
        help=suppress or 'remote provisioning endpoint to use',
    )

    parser.add_argument(
        '--remote-terminate',
        metavar='T',
        default=TerminateMode.NEVER,
        type=TerminateMode,
        action=EnumAction,
        help=suppress or 'terminate the remote instance: %(choices)s (default: %(default)s)',
    )


def add_environment_remote(
    exclusive_parser: argparse.ArgumentParser,
    environments_parser: argparse.ArgumentParser,
    target_mode: TargetMode,
) -> None:
    """Add environment arguments for running in ansible-core-ci provisioned remote virtual machines."""
    if target_mode == TargetMode.POSIX_INTEGRATION:
        remote_platforms = get_remote_platform_choices()
    elif target_mode == TargetMode.SHELL:
        remote_platforms = sorted(set(get_remote_platform_choices()) | set(get_windows_platform_choices()))
    else:
        remote_platforms = get_remote_platform_choices(True)

    suppress = None if get_ci_provider().supports_core_ci_auth() else argparse.SUPPRESS

    register_completer(exclusive_parser.add_argument(
        '--remote',
        metavar='NAME',
        help=suppress or 'run from a remote instance',
    ), functools.partial(complete_choices, remote_platforms))

    environments_parser.add_argument(
        '--remote-provider',
        metavar='PR',
        choices=REMOTE_PROVIDERS,
        help=suppress or 'remote provider to use: %(choices)s',
    )

    environments_parser.add_argument(
        '--remote-arch',
        metavar='ARCH',
        choices=REMOTE_ARCHITECTURES,
        help=suppress or 'remote arch to use: %(choices)s',
    )


def complete_remote_stage(prefix: str, **_) -> list[str]:
    """Return a list of supported stages matching the given prefix."""
    return [stage for stage in ('prod', 'dev') if stage.startswith(prefix)]


def complete_windows(prefix: str, parsed_args: argparse.Namespace, **_) -> list[str]:
    """Return a list of supported Windows versions matching the given prefix, excluding versions already parsed from the command line."""
    return [i for i in get_windows_version_choices() if i.startswith(prefix) and (not parsed_args.windows or i not in parsed_args.windows)]


def complete_network_platform(prefix: str, parsed_args: argparse.Namespace, **_) -> list[str]:
    """Return a list of supported network platforms matching the given prefix, excluding platforms already parsed from the command line."""
    images = sorted(filter_completion(network_completion()))

    return [i for i in images if i.startswith(prefix) and (not parsed_args.platform or i not in parsed_args.platform)]


def complete_network_platform_collection(prefix: str, parsed_args: argparse.Namespace, **_) -> list[str]:
    """Return a list of supported network platforms matching the given prefix, excluding collection platforms already parsed from the command line."""
    left = prefix.split('=')[0]
    images = sorted(set(image.platform for image in filter_completion(network_completion()).values()))

    return [i + '=' for i in images if i.startswith(left) and (not parsed_args.platform_collection or i not in [x[0] for x in parsed_args.platform_collection])]


def complete_network_platform_connection(prefix: str, parsed_args: argparse.Namespace, **_) -> list[str]:
    """Return a list of supported network platforms matching the given prefix, excluding connection platforms already parsed from the command line."""
    left = prefix.split('=')[0]
    images = sorted(set(image.platform for image in filter_completion(network_completion()).values()))

    return [i + '=' for i in images if i.startswith(left) and (not parsed_args.platform_connection or i not in [x[0] for x in parsed_args.platform_connection])]


def get_remote_platform_choices(controller: bool = False) -> list[str]:
    """Return a list of supported remote platforms matching the given prefix."""
    return sorted(filter_completion(remote_completion(), controller_only=controller))


def get_windows_platform_choices() -> list[str]:
    """Return a list of supported Windows versions matching the given prefix."""
    return sorted(f'windows/{windows.version}' for windows in filter_completion(windows_completion()).values())


def get_windows_version_choices() -> list[str]:
    """Return a list of supported Windows versions."""
    return sorted(windows.version for windows in filter_completion(windows_completion()).values())
