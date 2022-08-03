"""POSIX integration testing."""
from __future__ import annotations

import os

from ...util_common import (
    handle_layout_messages,
)

from ...containers import (
    create_container_hooks,
    local_ssh,
    root_ssh,
)

from ...target import (
    walk_posix_integration_targets,
)

from ...config import (
    PosixIntegrationConfig,
)

from . import (
    command_integration_filter,
    command_integration_filtered,
    get_inventory_relative_path,
)

from ...data import (
    data_context,
)


def command_posix_integration(args: PosixIntegrationConfig) -> None:
    """Entry point for the `integration` command."""
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    inventory_path = os.path.join(data_context().content.root, inventory_relative_path)

    all_targets = tuple(walk_posix_integration_targets(include_hidden=True))
    host_state, internal_targets = command_integration_filter(args, all_targets)
    control_connections = [local_ssh(args, host_state.controller_profile.python)]
    managed_connections = [root_ssh(ssh) for ssh in host_state.get_controller_target_connections()]
    pre_target, post_target = create_container_hooks(args, control_connections, managed_connections)

    command_integration_filtered(args, host_state, internal_targets, all_targets, inventory_path, pre_target=pre_target, post_target=post_target)
