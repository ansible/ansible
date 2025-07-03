"""Inventory creation from host profiles."""

from __future__ import annotations

import shutil
import sys
import typing as t

from .config import (
    EnvironmentConfig,
)

from .util import (
    sanitize_host_name,
    exclude_none_values,
)

from .host_configs import (
    ControllerConfig,
    PosixRemoteConfig,
)

from .host_profiles import (
    ControllerHostProfile,
    ControllerProfile,
    HostProfile,
    Inventory,
    NetworkInventoryProfile,
    NetworkRemoteProfile,
    SshTargetHostProfile,
    WindowsInventoryProfile,
    WindowsRemoteProfile,
    DebuggableProfile,
)

from .ssh import (
    ssh_options_to_str,
)


def get_common_variables(target_profile: HostProfile, controller: bool = False) -> dict[str, t.Any]:
    """Get variables common to all scenarios, but dependent on the target profile."""
    target_config = target_profile.config

    if controller or isinstance(target_config, ControllerConfig):
        # The current process is running on the controller, so consult the controller directly when it is the target.
        macos = sys.platform == 'darwin'
    elif isinstance(target_config, PosixRemoteConfig):
        # The target is not the controller, so consult the remote config for that target.
        macos = target_config.name.startswith('macos/')
    else:
        # The target is a type which either cannot be macOS or for which the OS is unknown.
        # There is currently no means for the user to override this for user provided hosts.
        macos = False

    common_variables: dict[str, t.Any] = {}

    if macos:
        # When using sudo on macOS we may encounter permission denied errors when dropping privileges due to inability to access the current working directory.
        # To compensate for this we'll perform a `cd /` before running any commands after `sudo` succeeds.
        common_variables.update(ansible_sudo_chdir='/')

    if isinstance(target_profile, DebuggableProfile):
        common_variables.update(target_profile.get_ansiballz_inventory_variables())

    return common_variables


def create_controller_inventory(args: EnvironmentConfig, path: str, controller_host: ControllerHostProfile) -> None:
    """Create and return inventory for use in controller-only integration tests."""
    inventory = Inventory(
        host_groups=dict(
            testgroup=dict(
                testhost=get_common_variables(controller_host, controller=True) | dict(
                    ansible_connection='local',
                    ansible_pipelining='yes',
                    ansible_python_interpreter=controller_host.python.path,
                ),
            ),
        ),
    )

    inventory.write(args, path)


def create_windows_inventory(args: EnvironmentConfig, path: str, target_hosts: list[HostProfile]) -> None:
    """Create and return inventory for use in target Windows integration tests."""
    first = target_hosts[0]

    if isinstance(first, WindowsInventoryProfile):
        if args.explain:
            return

        try:
            shutil.copyfile(first.config.path, path)
        except shutil.SameFileError:
            pass

        return

    target_hosts = t.cast(list[WindowsRemoteProfile], target_hosts)
    hosts = [(target_host, target_host.wait_for_instance().connection) for target_host in target_hosts]
    windows_hosts = {sanitize_host_name(host.config.name): host.get_inventory_variables() for host, connection in hosts}

    inventory = Inventory(
        host_groups=dict(
            windows=windows_hosts,
        ),
        # The `testhost` group is needed to support the `binary_modules_winrm` integration test.
        # The test should be updated to remove the need for this.
        extra_groups={
            'testhost:children': [
                'windows',
            ],
        },
    )

    inventory.write(args, path)


def create_network_inventory(args: EnvironmentConfig, path: str, target_hosts: list[HostProfile]) -> None:
    """Create and return inventory for use in target network integration tests."""
    first = target_hosts[0]

    if isinstance(first, NetworkInventoryProfile):
        if args.explain:
            return

        try:
            shutil.copyfile(first.config.path, path)
        except shutil.SameFileError:
            pass

        return

    target_hosts = t.cast(list[NetworkRemoteProfile], target_hosts)
    host_groups: dict[str, dict[str, dict[str, t.Union[str, int]]]] = {target_host.config.platform: {} for target_host in target_hosts}

    for target_host in target_hosts:
        host_groups[target_host.config.platform][sanitize_host_name(target_host.config.name)] = target_host.get_inventory_variables()

    inventory = Inventory(
        host_groups=host_groups,
        # The `net` group was added to support platform agnostic testing. It may not longer be needed.
        # see: https://github.com/ansible/ansible/pull/34661
        # see: https://github.com/ansible/ansible/pull/34707
        extra_groups={
            'net:children': sorted(host_groups),
        },
    )

    inventory.write(args, path)


def create_posix_inventory(args: EnvironmentConfig, path: str, target_hosts: list[HostProfile], needs_ssh: bool = False) -> None:
    """Create and return inventory for use in POSIX integration tests."""
    target_hosts = t.cast(list[SshTargetHostProfile], target_hosts)

    if len(target_hosts) != 1:
        raise Exception()

    target_host = target_hosts[0]

    if isinstance(target_host, ControllerProfile) and not needs_ssh:
        inventory = Inventory(
            host_groups=dict(
                testgroup=dict(
                    testhost=get_common_variables(target_host) | dict(
                        ansible_connection='local',
                        ansible_pipelining='yes',
                        ansible_python_interpreter=target_host.python.path,
                    ),
                ),
            ),
        )
    else:
        connections = target_host.get_controller_target_connections()

        if len(connections) != 1:
            raise Exception()

        ssh = connections[0]

        testhost: dict[str, t.Optional[t.Union[str, int]]] = get_common_variables(target_host) | dict(
            ansible_connection='ssh',
            ansible_pipelining='yes',
            ansible_python_interpreter=ssh.settings.python_interpreter,
            ansible_host=ssh.settings.host,
            ansible_port=ssh.settings.port,
            ansible_user=ssh.settings.user,
            ansible_ssh_private_key_file=ssh.settings.identity_file,
            ansible_ssh_extra_args=ssh_options_to_str(ssh.settings.options),
        )

        if ssh.become:
            testhost.update(
                ansible_become='yes',
                ansible_become_method=ssh.become.method,
            )

        testhost = exclude_none_values(testhost)

        inventory = Inventory(
            host_groups=dict(
                testgroup=dict(
                    testhost=testhost,
                ),
            ),
        )

    inventory.write(args, path)
