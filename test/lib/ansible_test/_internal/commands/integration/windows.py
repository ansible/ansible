"""Windows integration testing."""
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
    ManageWindowsCI,
)

from ...io import (
    write_text_file,
)

from ...util import (
    ApplicationError,
    display,
    ANSIBLE_TEST_CONFIG_ROOT,
    tempdir,
    open_zipfile,
)

from ...util_common import (
    get_python_path,
    ResultType,
    handle_layout_messages,
)

from ...containers import (
    SshConnectionDetail,
    create_container_hooks,
)

from ...ansible_util import (
    run_playbook,
)

from ...target import (
    IntegrationTarget,
    walk_windows_integration_targets,
)

from ...config import (
    WindowsIntegrationConfig,
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

from ...executor import (
    parse_inventory,
    get_hosts,
)


def command_windows_integration(args):
    """
    :type args: WindowsIntegrationConfig
    """
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    template_path = os.path.join(ANSIBLE_TEST_CONFIG_ROOT, os.path.basename(inventory_relative_path)) + '.template'

    if args.inventory:
        inventory_path = os.path.join(data_context().content.root, data_context().content.integration_path, args.inventory)
    else:
        inventory_path = os.path.join(data_context().content.root, inventory_relative_path)

    if not args.explain and not args.windows and not os.path.isfile(inventory_path):
        raise ApplicationError(
            'Inventory not found: %s\n'
            'Use --inventory to specify the inventory path.\n'
            'Use --windows to provision resources and generate an inventory file.\n'
            'See also inventory template: %s' % (inventory_path, template_path)
        )

    check_inventory(args, inventory_path)
    delegate_inventory(args, inventory_path)

    all_targets = tuple(walk_windows_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets, init_callback=windows_init)
    instances = []  # type: t.List[WrappedThread]
    managed_connections = []  # type: t.List[SshConnectionDetail]

    if args.windows:
        get_python_path(args, args.python_executable)  # initialize before starting threads

        configs = dict((config['platform_version'], config) for config in args.metadata.instance_config)

        for version in args.windows:
            config = configs['windows/%s' % version]

            instance = WrappedThread(functools.partial(windows_run, args, version, config))
            instance.daemon = True
            instance.start()
            instances.append(instance)

        while any(instance.is_alive() for instance in instances):
            time.sleep(1)

        remotes = [instance.wait_for_result() for instance in instances]
        inventory = windows_inventory(remotes)

        display.info('>>> Inventory: %s\n%s' % (inventory_path, inventory.strip()), verbosity=3)

        if not args.explain:
            write_text_file(inventory_path, inventory)

        for core_ci in remotes:
            ssh_con = core_ci.connection
            ssh = SshConnectionDetail(core_ci.name, ssh_con.hostname, 22, ssh_con.username, core_ci.ssh_key.key, shell_type='powershell')
            managed_connections.append(ssh)
    elif args.explain:
        identity_file = SshKey(args).key

        # mock connection details to prevent tracebacks in explain mode
        managed_connections = [SshConnectionDetail(
            name='windows',
            host='windows',
            port=22,
            user='administrator',
            identity_file=identity_file,
            shell_type='powershell',
        )]
    else:
        inventory = parse_inventory(args, inventory_path)
        hosts = get_hosts(inventory, 'windows')
        identity_file = SshKey(args).key

        managed_connections = [SshConnectionDetail(
            name=name,
            host=config['ansible_host'],
            port=22,
            user=config['ansible_user'],
            identity_file=identity_file,
            shell_type='powershell',
        ) for name, config in hosts.items()]

        if managed_connections:
            display.info('Generated SSH connection details from inventory:\n%s' % (
                '\n'.join('%s %s@%s:%d' % (ssh.name, ssh.user, ssh.host, ssh.port) for ssh in managed_connections)), verbosity=1)

    pre_target, post_target = create_container_hooks(args, managed_connections)

    remote_temp_path = None

    if args.coverage and not args.coverage_check:
        # Create the remote directory that is writable by everyone. Use Ansible to talk to the remote host.
        remote_temp_path = 'C:\\ansible_test_coverage_%s' % time.time()
        playbook_vars = {'remote_temp_path': remote_temp_path}
        run_playbook(args, inventory_path, 'windows_coverage_setup.yml', playbook_vars)

    success = False

    try:
        command_integration_filtered(args, internal_targets, all_targets, inventory_path, pre_target=pre_target,
                                     post_target=post_target, remote_temp_path=remote_temp_path)
        success = True
    finally:
        if remote_temp_path:
            # Zip up the coverage files that were generated and fetch it back to localhost.
            with tempdir() as local_temp_path:
                playbook_vars = {'remote_temp_path': remote_temp_path, 'local_temp_path': local_temp_path}
                run_playbook(args, inventory_path, 'windows_coverage_teardown.yml', playbook_vars)

                for filename in os.listdir(local_temp_path):
                    with open_zipfile(os.path.join(local_temp_path, filename)) as coverage_zip:
                        coverage_zip.extractall(ResultType.COVERAGE.path)

        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            for instance in instances:
                instance.result.stop()


# noinspection PyUnusedLocal
def windows_init(args, internal_targets):  # pylint: disable=locally-disabled, unused-argument
    """
    :type args: WindowsIntegrationConfig
    :type internal_targets: tuple[IntegrationTarget]
    """
    # generate an ssh key (if needed) up front once, instead of for each instance
    SshKey(args)

    if not args.windows:
        return

    if args.metadata.instance_config is not None:
        return

    instances = []  # type: t.List[WrappedThread]

    for version in args.windows:
        instance = WrappedThread(functools.partial(windows_start, args, version))
        instance.daemon = True
        instance.start()
        instances.append(instance)

    while any(instance.is_alive() for instance in instances):
        time.sleep(1)

    args.metadata.instance_config = [instance.wait_for_result() for instance in instances]


def windows_start(args, version):
    """
    :type args: WindowsIntegrationConfig
    :type version: str
    :rtype: AnsibleCoreCI
    """
    core_ci = AnsibleCoreCI(args, 'windows', version, stage=args.remote_stage, provider=args.remote_provider)
    core_ci.start()

    return core_ci.save()


def windows_run(args, version, config):
    """
    :type args: WindowsIntegrationConfig
    :type version: str
    :type config: dict[str, str]
    :rtype: AnsibleCoreCI
    """
    core_ci = AnsibleCoreCI(args, 'windows', version, stage=args.remote_stage, provider=args.remote_provider, load=False)
    core_ci.load(config)
    core_ci.wait()

    manage = ManageWindowsCI(core_ci)
    manage.wait()

    return core_ci


def windows_inventory(remotes):
    """
    :type remotes: list[AnsibleCoreCI]
    :rtype: str
    """
    hosts = []

    for remote in remotes:
        options = dict(
            ansible_host=remote.connection.hostname,
            ansible_user=remote.connection.username,
            ansible_password=remote.connection.password,
            ansible_port=remote.connection.port,
        )

        # used for the connection_windows_ssh test target
        if remote.ssh_key:
            options["ansible_ssh_private_key_file"] = os.path.abspath(remote.ssh_key.key)

        if remote.name == 'windows-2016':
            options.update(
                # force 2016 to use NTLM + HTTP message encryption
                ansible_connection='winrm',
                ansible_winrm_server_cert_validation='ignore',
                ansible_winrm_transport='ntlm',
                ansible_winrm_scheme='http',
                ansible_port='5985',
            )
        else:
            options.update(
                ansible_connection='winrm',
                ansible_winrm_server_cert_validation='ignore',
            )

        hosts.append(
            '%s %s' % (
                remote.name.replace('/', '_'),
                ' '.join('%s="%s"' % (k, options[k]) for k in sorted(options)),
            )
        )

    template = """
    [windows]
    %s

    # support winrm binary module tests (temporary solution)
    [testhost:children]
    windows
    """

    template = textwrap.dedent(template)
    inventory = template % ('\n'.join(hosts))

    return inventory
