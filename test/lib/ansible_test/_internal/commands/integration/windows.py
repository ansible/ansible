"""Windows integration testing."""
from __future__ import annotations

import os

from ...util import (
    ApplicationError,
    ANSIBLE_TEST_CONFIG_ROOT,
)

from ...util_common import (
    handle_layout_messages,
)

from ...containers import (
    create_container_hooks,
    local_ssh,
    root_ssh,
)

from ...target import (
    walk_windows_integration_targets,
)

from ...config import (
    WindowsIntegrationConfig,
)

from ...host_configs import (
    WindowsInventoryConfig,
    WindowsRemoteConfig,
)

from . import (
    command_integration_filter,
    command_integration_filtered,
    get_inventory_absolute_path,
    get_inventory_relative_path,
    check_inventory,
    delegate_inventory,
)

from ...data import (
    data_context,
)


def command_windows_integration(args: WindowsIntegrationConfig) -> None:
    """Entry point for the `windows-integration` command."""
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    template_path = os.path.join(ANSIBLE_TEST_CONFIG_ROOT, os.path.basename(inventory_relative_path)) + '.template'

    if issubclass(args.target_type, WindowsInventoryConfig):
        target = args.only_target(WindowsInventoryConfig)
        inventory_path = get_inventory_absolute_path(args, target)

        if args.delegate or not target.path:
            target.path = inventory_relative_path
    else:
        inventory_path = os.path.join(data_context().content.root, inventory_relative_path)

    if not args.explain and not issubclass(args.target_type, WindowsRemoteConfig) and not os.path.isfile(inventory_path):
        raise ApplicationError(
            'Inventory not found: %s\n'
            'Use --inventory to specify the inventory path.\n'
            'Use --windows to provision resources and generate an inventory file.\n'
            'See also inventory template: %s' % (inventory_path, template_path)
        )

    check_inventory(args, inventory_path)
    delegate_inventory(args, inventory_path)

    all_targets = tuple(walk_windows_integration_targets(include_hidden=True))
    host_state, internal_targets = command_integration_filter(args, all_targets)
    control_connections = [local_ssh(args, host_state.controller_profile.python)]
    managed_connections = [root_ssh(ssh) for ssh in host_state.get_controller_target_connections()]
    pre_target, post_target = create_container_hooks(args, control_connections, managed_connections)

    command_integration_filtered(args, host_state, internal_targets, all_targets, inventory_path, pre_target=pre_target, post_target=post_target)
