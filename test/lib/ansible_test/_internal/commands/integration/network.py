"""Network integration testing."""
from __future__ import annotations

import os

from ...util import (
    ApplicationError,
    ANSIBLE_TEST_CONFIG_ROOT,
)

from ...util_common import (
    handle_layout_messages,
)

from ...target import (
    walk_network_integration_targets,
)

from ...config import (
    NetworkIntegrationConfig,
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

from ...host_configs import (
    NetworkInventoryConfig,
    NetworkRemoteConfig,
)


def command_network_integration(args: NetworkIntegrationConfig) -> None:
    """Entry point for the `network-integration` command."""
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    template_path = os.path.join(ANSIBLE_TEST_CONFIG_ROOT, os.path.basename(inventory_relative_path)) + '.template'

    if issubclass(args.target_type, NetworkInventoryConfig):
        target = args.only_target(NetworkInventoryConfig)
        inventory_path = get_inventory_absolute_path(args, target)

        if args.delegate or not target.path:
            target.path = inventory_relative_path
    else:
        inventory_path = os.path.join(data_context().content.root, inventory_relative_path)

    if args.no_temp_workdir:
        # temporary solution to keep DCI tests working
        inventory_exists = os.path.exists(inventory_path)
    else:
        inventory_exists = os.path.isfile(inventory_path)

    if not args.explain and not issubclass(args.target_type, NetworkRemoteConfig) and not inventory_exists:
        raise ApplicationError(
            'Inventory not found: %s\n'
            'Use --inventory to specify the inventory path.\n'
            'Use --platform to provision resources and generate an inventory file.\n'
            'See also inventory template: %s' % (inventory_path, template_path)
        )

    check_inventory(args, inventory_path)
    delegate_inventory(args, inventory_path)

    all_targets = tuple(walk_network_integration_targets(include_hidden=True))
    host_state, internal_targets = command_integration_filter(args, all_targets)
    command_integration_filtered(args, host_state, internal_targets, all_targets, inventory_path)
