"""POSIX integration testing."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ... import types as t

from ...util import (
    ANSIBLE_TEST_DATA_ROOT,
)

from ...util_common import (
    handle_layout_messages,
)

from ...containers import (
    SshConnectionDetail,
    create_container_hooks,
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


def command_posix_integration(args):
    """
    :type args: PosixIntegrationConfig
    """
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    inventory_path = os.path.join(ANSIBLE_TEST_DATA_ROOT, os.path.basename(inventory_relative_path))

    all_targets = tuple(walk_posix_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets)

    managed_connections = None  # type: t.Optional[t.List[SshConnectionDetail]]

    pre_target, post_target = create_container_hooks(args, managed_connections)

    command_integration_filtered(args, internal_targets, all_targets, inventory_path, pre_target=pre_target, post_target=post_target)
