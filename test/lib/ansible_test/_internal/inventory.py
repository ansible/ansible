"""Inventory creation from host profiles."""
from __future__ import annotations

import shutil
import typing as t

from .config import (
    EnvironmentConfig,
)

from .util import (
    sanitize_host_name,
    exclude_none_values,
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
)

from .ssh import (
    ssh_options_to_str,
)


def create_controller_inventory(args: EnvironmentConfig, path: str, controller_host: ControllerHostProfile) -> None:
    """Create and return inventory for use in controller-only integration tests."""
    inventory = Inventory(
        host_groups=dict(
            testgroup=dict(
                testhost=dict(
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
                    testhost=dict(
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

        testhost: dict[str, t.Optional[t.Union[str, int]]] = dict(
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
