"""Network integration testing."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import textwrap
import functools

from ... import types as t

from ...thread import (
    WrappedThread,
)

from ...core_ci import (
    AnsibleCoreCI,
    SshKey,
)

from ...manage_ci import (
    ManageNetworkCI,
    get_network_settings,
)

from ...io import (
    write_text_file,
)

from ...util import (
    ApplicationError,
    display,
    ANSIBLE_TEST_CONFIG_ROOT,
)

from ...util_common import (
    get_python_path,
    handle_layout_messages,
)

from ...target import (
    IntegrationTarget,
    walk_network_integration_targets,
)

from ...config import (
    NetworkIntegrationConfig,
)

from . import (
    command_integration_filter,
    command_integration_filtered,
    get_inventory_relative_path,
    check_inventory,
    delegate_inventory,
)

from ...data import (
    data_context,
)


def command_network_integration(args):
    """
    :type args: NetworkIntegrationConfig
    """
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    template_path = os.path.join(ANSIBLE_TEST_CONFIG_ROOT, os.path.basename(inventory_relative_path)) + '.template'

    if args.inventory:
        inventory_path = os.path.join(data_context().content.root, data_context().content.integration_path, args.inventory)
    else:
        inventory_path = os.path.join(data_context().content.root, inventory_relative_path)

    if args.no_temp_workdir:
        # temporary solution to keep DCI tests working
        inventory_exists = os.path.exists(inventory_path)
    else:
        inventory_exists = os.path.isfile(inventory_path)

    if not args.explain and not args.platform and not inventory_exists:
        raise ApplicationError(
            'Inventory not found: %s\n'
            'Use --inventory to specify the inventory path.\n'
            'Use --platform to provision resources and generate an inventory file.\n'
            'See also inventory template: %s' % (inventory_path, template_path)
        )

    check_inventory(args, inventory_path)
    delegate_inventory(args, inventory_path)

    all_targets = tuple(walk_network_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets, init_callback=network_init)
    instances = []  # type: t.List[WrappedThread]

    if args.platform:
        get_python_path(args, args.python_executable)  # initialize before starting threads

        configs = dict((config['platform_version'], config) for config in args.metadata.instance_config)

        for platform_version in args.platform:
            platform, version = platform_version.split('/', 1)
            config = configs.get(platform_version)

            if not config:
                continue

            instance = WrappedThread(functools.partial(network_run, args, platform, version, config))
            instance.daemon = True
            instance.start()
            instances.append(instance)

        while any(instance.is_alive() for instance in instances):
            time.sleep(1)

        remotes = [instance.wait_for_result() for instance in instances]
        inventory = network_inventory(args, remotes)

        display.info('>>> Inventory: %s\n%s' % (inventory_path, inventory.strip()), verbosity=3)

        if not args.explain:
            write_text_file(inventory_path, inventory)

    success = False

    try:
        command_integration_filtered(args, internal_targets, all_targets, inventory_path)
        success = True
    finally:
        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            for instance in instances:
                instance.result.stop()


def network_init(args, internal_targets):  # type: (NetworkIntegrationConfig, t.Tuple[IntegrationTarget, ...]) -> None
    """Initialize platforms for network integration tests."""
    if not args.platform:
        return

    if args.metadata.instance_config is not None:
        return

    platform_targets = set(a for target in internal_targets for a in target.aliases if a.startswith('network/'))

    instances = []  # type: t.List[WrappedThread]

    # generate an ssh key (if needed) up front once, instead of for each instance
    SshKey(args)

    for platform_version in args.platform:
        platform, version = platform_version.split('/', 1)
        platform_target = 'network/%s/' % platform

        if platform_target not in platform_targets:
            display.warning('Skipping "%s" because selected tests do not target the "%s" platform.' % (
                platform_version, platform))
            continue

        instance = WrappedThread(functools.partial(network_start, args, platform, version))
        instance.daemon = True
        instance.start()
        instances.append(instance)

    while any(instance.is_alive() for instance in instances):
        time.sleep(1)

    args.metadata.instance_config = [instance.wait_for_result() for instance in instances]


def network_start(args, platform, version):
    """
    :type args: NetworkIntegrationConfig
    :type platform: str
    :type version: str
    :rtype: AnsibleCoreCI
    """
    core_ci = AnsibleCoreCI(args, platform, version, stage=args.remote_stage, provider=args.remote_provider)
    core_ci.start()

    return core_ci.save()


def network_run(args, platform, version, config):
    """
    :type args: NetworkIntegrationConfig
    :type platform: str
    :type version: str
    :type config: dict[str, str]
    :rtype: AnsibleCoreCI
    """
    core_ci = AnsibleCoreCI(args, platform, version, stage=args.remote_stage, provider=args.remote_provider, load=False)
    core_ci.load(config)
    core_ci.wait()

    manage = ManageNetworkCI(args, core_ci)
    manage.wait()

    return core_ci


def network_inventory(args, remotes):
    """
    :type args: NetworkIntegrationConfig
    :type remotes: list[AnsibleCoreCI]
    :rtype: str
    """
    groups = dict([(remote.platform, []) for remote in remotes])
    net = []

    for remote in remotes:
        options = dict(
            ansible_host=remote.connection.hostname,
            ansible_user=remote.connection.username,
            ansible_ssh_private_key_file=os.path.abspath(remote.ssh_key.key),
        )

        settings = get_network_settings(args, remote.platform, remote.version)

        options.update(settings.inventory_vars)

        groups[remote.platform].append(
            '%s %s' % (
                remote.name.replace('.', '-'),
                ' '.join('%s="%s"' % (k, options[k]) for k in sorted(options)),
            )
        )

        net.append(remote.platform)

    groups['net:children'] = net

    template = ''

    for group in groups:
        hosts = '\n'.join(groups[group])

        template += textwrap.dedent("""
        [%s]
        %s
        """) % (group, hosts)

    inventory = template

    return inventory
