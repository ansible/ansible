"""Execute Ansible tests."""

from __future__ import absolute_import, print_function

import json
import os
import collections
import datetime
import re
import time
import textwrap
import functools
import sys
import hashlib
import difflib
import filecmp
import random
import string
import shutil

import lib.pytar
import lib.thread

from lib.core_ci import (
    AnsibleCoreCI,
    SshKey,
)

from lib.manage_ci import (
    ManageWindowsCI,
    ManageNetworkCI,
)

from lib.cloud import (
    cloud_filter,
    cloud_init,
    get_cloud_environment,
    get_cloud_platforms,
    CloudEnvironmentConfig,
)

from lib.util import (
    ApplicationWarning,
    ApplicationError,
    SubprocessError,
    display,
    run_command,
    intercept_command,
    remove_tree,
    make_dirs,
    find_executable,
    raw_command,
    get_python_path,
    get_available_port,
    generate_pip_command,
    find_python,
    get_docker_completion,
    get_remote_completion,
    named_temporary_file,
    COVERAGE_OUTPUT_PATH,
    cmd_quote,
)

from lib.docker_util import (
    docker_pull,
    docker_run,
    docker_available,
    docker_rm,
    get_docker_container_id,
    get_docker_container_ip,
    get_docker_hostname,
    get_docker_preferred_network_name,
    is_docker_user_defined_network,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.target import (
    IntegrationTarget,
    walk_external_targets,
    walk_internal_targets,
    walk_posix_integration_targets,
    walk_network_integration_targets,
    walk_windows_integration_targets,
    walk_units_targets,
)

from lib.ci import (
    get_ci_provider,
)

from lib.classification import (
    categorize_changes,
)

from lib.config import (
    TestConfig,
    EnvironmentConfig,
    IntegrationConfig,
    NetworkIntegrationConfig,
    PosixIntegrationConfig,
    ShellConfig,
    UnitsConfig,
    WindowsIntegrationConfig,
)

from lib.metadata import (
    ChangeDescription,
)

from lib.integration import (
    integration_test_environment,
    integration_test_config_file,
    setup_common_temp_dir,
)

SUPPORTED_PYTHON_VERSIONS = (
    '2.6',
    '2.7',
    '3.5',
    '3.6',
    '3.7',
    '3.8',
)

HTTPTESTER_HOSTS = (
    'ansible.http.tests',
    'sni1.ansible.http.tests',
    'fail.ansible.http.tests',
)


def check_startup():
    """Checks to perform at startup before running commands."""
    check_legacy_modules()


def check_legacy_modules():
    """Detect conflicts with legacy core/extras module directories to avoid problems later."""
    for directory in 'core', 'extras':
        path = 'lib/ansible/modules/%s' % directory

        for root, _, file_names in os.walk(path):
            if file_names:
                # the directory shouldn't exist, but if it does, it must contain no files
                raise ApplicationError('Files prohibited in "%s". '
                                       'These are most likely legacy modules from version 2.2 or earlier.' % root)


def create_shell_command(command):
    """
    :type command: list[str]
    :rtype: list[str]
    """
    optional_vars = (
        'TERM',
    )

    cmd = ['/usr/bin/env']
    cmd += ['%s=%s' % (var, os.environ[var]) for var in optional_vars if var in os.environ]
    cmd += command

    return cmd


def install_command_requirements(args, python_version=None):
    """
    :type args: EnvironmentConfig
    :type python_version: str | None
    """
    if isinstance(args, ShellConfig):
        if args.raw:
            return

    generate_egg_info(args)

    if not args.requirements:
        return

    if isinstance(args, ShellConfig):
        return

    packages = []

    if isinstance(args, TestConfig):
        if args.coverage:
            packages.append('coverage')
        if args.junit:
            packages.append('junit-xml')

    if not python_version:
        python_version = args.python_version

    pip = generate_pip_command(find_python(python_version))

    commands = [generate_pip_install(pip, args.command, packages=packages)]

    if isinstance(args, IntegrationConfig):
        for cloud_platform in get_cloud_platforms(args):
            commands.append(generate_pip_install(pip, '%s.cloud.%s' % (args.command, cloud_platform)))

    commands = [cmd for cmd in commands if cmd]

    # only look for changes when more than one requirements file is needed
    detect_pip_changes = len(commands) > 1

    # first pass to install requirements, changes expected unless environment is already set up
    changes = run_pip_commands(args, pip, commands, detect_pip_changes)

    if changes:
        # second pass to check for conflicts in requirements, changes are not expected here
        changes = run_pip_commands(args, pip, commands, detect_pip_changes)

        if changes:
            raise ApplicationError('Conflicts detected in requirements. The following commands reported changes during verification:\n%s' %
                                   '\n'.join((' '.join(cmd_quote(c) for c in cmd) for cmd in changes)))

    # ask pip to check for conflicts between installed packages
    try:
        run_command(args, pip + ['check', '--disable-pip-version-check'], capture=True)
    except SubprocessError as ex:
        if ex.stderr.strip() == 'ERROR: unknown command "check"':
            display.warning('Cannot check pip requirements for conflicts because "pip check" is not supported.')
        else:
            raise


def run_pip_commands(args, pip, commands, detect_pip_changes=False):
    """
    :type args: EnvironmentConfig
    :type pip: list[str]
    :type commands: list[list[str]]
    :type detect_pip_changes: bool
    :rtype: list[list[str]]
    """
    changes = []

    after_list = pip_list(args, pip) if detect_pip_changes else None

    for cmd in commands:
        if not cmd:
            continue

        before_list = after_list

        run_command(args, cmd)

        after_list = pip_list(args, pip) if detect_pip_changes else None

        if before_list != after_list:
            changes.append(cmd)

    return changes


def pip_list(args, pip):
    """
    :type args: EnvironmentConfig
    :type pip: list[str]
    :rtype: str
    """
    stdout, _ = run_command(args, pip + ['list'], capture=True)
    return stdout


def generate_egg_info(args):
    """
    :type args: EnvironmentConfig
    """
    if os.path.isdir('lib/ansible.egg-info'):
        return

    run_command(args, [args.python_executable, 'setup.py', 'egg_info'], capture=args.verbosity < 3)


def generate_pip_install(pip, command, packages=None):
    """
    :type pip: list[str]
    :type command: str
    :type packages: list[str] | None
    :rtype: list[str] | None
    """
    constraints = 'test/runner/requirements/constraints.txt'
    requirements = 'test/runner/requirements/%s.txt' % command

    options = []

    if os.path.exists(requirements) and os.path.getsize(requirements):
        options += ['-r', requirements]

    if packages:
        options += packages

    if not options:
        return None

    return pip + ['install', '--disable-pip-version-check', '-c', constraints] + options


def command_shell(args):
    """
    :type args: ShellConfig
    """
    if args.delegate:
        raise Delegate()

    install_command_requirements(args)

    if args.inject_httptester:
        inject_httptester(args)

    cmd = create_shell_command(['bash', '-i'])
    run_command(args, cmd)


def command_posix_integration(args):
    """
    :type args: PosixIntegrationConfig
    """
    filename = 'test/integration/inventory'

    all_targets = tuple(walk_posix_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets)
    command_integration_filtered(args, internal_targets, all_targets, filename)


def command_network_integration(args):
    """
    :type args: NetworkIntegrationConfig
    """
    default_filename = 'test/integration/inventory.networking'

    if args.inventory:
        filename = os.path.join('test/integration', args.inventory)
    else:
        filename = default_filename

    if not args.explain and not args.platform and not os.path.exists(filename):
        if args.inventory:
            filename = os.path.abspath(filename)

        raise ApplicationError(
            'Inventory not found: %s\n'
            'Use --inventory to specify the inventory path.\n'
            'Use --platform to provision resources and generate an inventory file.\n'
            'See also inventory template: %s.template' % (filename, default_filename)
        )

    all_targets = tuple(walk_network_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets, init_callback=network_init)
    instances = []  # type: list [lib.thread.WrappedThread]

    if args.platform:
        get_python_path(args, args.python_executable)  # initialize before starting threads

        configs = dict((config['platform_version'], config) for config in args.metadata.instance_config)

        for platform_version in args.platform:
            platform, version = platform_version.split('/', 1)
            config = configs.get(platform_version)

            if not config:
                continue

            instance = lib.thread.WrappedThread(functools.partial(network_run, args, platform, version, config))
            instance.daemon = True
            instance.start()
            instances.append(instance)

        while any(instance.is_alive() for instance in instances):
            time.sleep(1)

        remotes = [instance.wait_for_result() for instance in instances]
        inventory = network_inventory(remotes)

        display.info('>>> Inventory: %s\n%s' % (filename, inventory.strip()), verbosity=3)

        if not args.explain:
            with open(filename, 'w') as inventory_fd:
                inventory_fd.write(inventory)

    success = False

    try:
        command_integration_filtered(args, internal_targets, all_targets, filename)
        success = True
    finally:
        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            for instance in instances:
                instance.result.stop()


def network_init(args, internal_targets):
    """
    :type args: NetworkIntegrationConfig
    :type internal_targets: tuple[IntegrationTarget]
    """
    if not args.platform:
        return

    if args.metadata.instance_config is not None:
        return

    platform_targets = set(a for t in internal_targets for a in t.aliases if a.startswith('network/'))

    instances = []  # type: list [lib.thread.WrappedThread]

    # generate an ssh key (if needed) up front once, instead of for each instance
    SshKey(args)

    for platform_version in args.platform:
        platform, version = platform_version.split('/', 1)
        platform_target = 'network/%s/' % platform

        if platform_target not in platform_targets:
            display.warning('Skipping "%s" because selected tests do not target the "%s" platform.' % (
                platform_version, platform))
            continue

        instance = lib.thread.WrappedThread(functools.partial(network_start, args, platform, version))
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

    manage = ManageNetworkCI(core_ci)
    manage.wait()

    return core_ci


def network_inventory(remotes):
    """
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
            ansible_network_os=remote.platform,
            ansible_connection='local'
        )

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


def command_windows_integration(args):
    """
    :type args: WindowsIntegrationConfig
    """
    filename = 'test/integration/inventory.winrm'

    if not args.explain and not args.windows and not os.path.isfile(filename):
        raise ApplicationError('Use the --windows option or provide an inventory file (see %s.template).' % filename)

    all_targets = tuple(walk_windows_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets, init_callback=windows_init)
    instances = []  # type: list [lib.thread.WrappedThread]
    pre_target = None
    post_target = None
    httptester_id = None

    if args.windows:
        get_python_path(args, args.python_executable)  # initialize before starting threads

        configs = dict((config['platform_version'], config) for config in args.metadata.instance_config)

        for version in args.windows:
            config = configs['windows/%s' % version]

            instance = lib.thread.WrappedThread(functools.partial(windows_run, args, version, config))
            instance.daemon = True
            instance.start()
            instances.append(instance)

        while any(instance.is_alive() for instance in instances):
            time.sleep(1)

        remotes = [instance.wait_for_result() for instance in instances]
        inventory = windows_inventory(remotes)

        display.info('>>> Inventory: %s\n%s' % (filename, inventory.strip()), verbosity=3)

        if not args.explain:
            with open(filename, 'w') as inventory_fd:
                inventory_fd.write(inventory)

        use_httptester = args.httptester and any('needs/httptester/' in t.aliases for t in internal_targets)
        # if running under Docker delegation, the httptester may have already been started
        docker_httptester = bool(os.environ.get("HTTPTESTER", False))

        if use_httptester and not docker_available() and not docker_httptester:
            display.warning('Assuming --disable-httptester since `docker` is not available.')
        elif use_httptester:
            if docker_httptester:
                # we are running in a Docker container that is linked to the httptester container, we just need to
                # forward these requests to the linked hostname
                first_host = HTTPTESTER_HOSTS[0]
                ssh_options = ["-R", "8080:%s:80" % first_host, "-R", "8443:%s:443" % first_host]
            else:
                # we are running directly and need to start the httptester container ourselves and forward the port
                # from there manually set so HTTPTESTER env var is set during the run
                args.inject_httptester = True
                httptester_id, ssh_options = start_httptester(args)

            # to get this SSH command to run in the background we need to set to run in background (-f) and disable
            # the pty allocation (-T)
            ssh_options.insert(0, "-fT")

            # create a script that will continue to run in the background until the script is deleted, this will
            # cleanup and close the connection
            def forward_ssh_ports(target):
                """
                :type target: IntegrationTarget
                """
                if 'needs/httptester/' not in target.aliases:
                    return

                for remote in [r for r in remotes if r.version != '2008']:
                    manage = ManageWindowsCI(remote)
                    manage.upload("test/runner/setup/windows-httptester.ps1", watcher_path)

                    # We cannot pass an array of string with -File so we just use a delimiter for multiple values
                    script = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\%s -Hosts \"%s\"" \
                             % (watcher_path, "|".join(HTTPTESTER_HOSTS))
                    if args.verbosity > 3:
                        script += " -Verbose"
                    manage.ssh(script, options=ssh_options, force_pty=False)

            def cleanup_ssh_ports(target):
                """
                :type target: IntegrationTarget
                """
                if 'needs/httptester/' not in target.aliases:
                    return

                for remote in [r for r in remotes if r.version != '2008']:
                    # delete the tmp file that keeps the http-tester alive
                    manage = ManageWindowsCI(remote)
                    manage.ssh("cmd.exe /c \"del %s /F /Q\"" % watcher_path, force_pty=False)

            watcher_path = "ansible-test-http-watcher-%s.ps1" % time.time()
            pre_target = forward_ssh_ports
            post_target = cleanup_ssh_ports

    success = False

    try:
        command_integration_filtered(args, internal_targets, all_targets, filename, pre_target=pre_target,
                                     post_target=post_target)
        success = True
    finally:
        if httptester_id:
            docker_rm(args, httptester_id)

        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            for instance in instances:
                instance.result.stop()


# noinspection PyUnusedLocal
def windows_init(args, internal_targets):  # pylint: disable=locally-disabled, unused-argument
    """
    :type args: WindowsIntegrationConfig
    :type internal_targets: tuple[IntegrationTarget]
    """
    if not args.windows:
        return

    if args.metadata.instance_config is not None:
        return

    instances = []  # type: list [lib.thread.WrappedThread]

    for version in args.windows:
        instance = lib.thread.WrappedThread(functools.partial(windows_start, args, version))
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

        hosts.append(
            '%s %s' % (
                remote.name.replace('/', '_'),
                ' '.join('%s="%s"' % (k, options[k]) for k in sorted(options)),
            )
        )

    template = """
    [windows]
    %s

    [windows:vars]
    ansible_connection=winrm
    ansible_winrm_server_cert_validation=ignore

    # support winrm connection tests (temporary solution, does not support testing enable/disable of pipelining)
    [winrm:children]
    windows

    # support winrm binary module tests (temporary solution)
    [testhost_binary_modules:children]
    windows
    """

    template = textwrap.dedent(template)
    inventory = template % ('\n'.join(hosts))

    return inventory


def command_integration_filter(args, targets, init_callback=None):
    """
    :type args: IntegrationConfig
    :type targets: collections.Iterable[IntegrationTarget]
    :type init_callback: (IntegrationConfig, tuple[IntegrationTarget]) -> None
    :rtype: tuple[IntegrationTarget]
    """
    targets = tuple(target for target in targets if 'hidden/' not in target.aliases)
    changes = get_changes_filter(args)

    # special behavior when the --changed-all-target target is selected based on changes
    if args.changed_all_target in changes:
        # act as though the --changed-all-target target was in the include list
        if args.changed_all_mode == 'include' and args.changed_all_target not in args.include:
            args.include.append(args.changed_all_target)
            args.delegate_args += ['--include', args.changed_all_target]
        # act as though the --changed-all-target target was in the exclude list
        elif args.changed_all_mode == 'exclude' and args.changed_all_target not in args.exclude:
            args.exclude.append(args.changed_all_target)

    require = args.require + changes
    exclude = args.exclude

    internal_targets = walk_internal_targets(targets, args.include, exclude, require)
    environment_exclude = get_integration_filter(args, internal_targets)

    environment_exclude += cloud_filter(args, internal_targets)

    if environment_exclude:
        exclude += environment_exclude
        internal_targets = walk_internal_targets(targets, args.include, exclude, require)

    if not internal_targets:
        raise AllTargetsSkipped()

    if args.start_at and not any(t.name == args.start_at for t in internal_targets):
        raise ApplicationError('Start at target matches nothing: %s' % args.start_at)

    if init_callback:
        init_callback(args, internal_targets)

    cloud_init(args, internal_targets)

    if args.delegate:
        raise Delegate(require=require, exclude=exclude, integration_targets=internal_targets)

    install_command_requirements(args)

    return internal_targets


def command_integration_filtered(args, targets, all_targets, inventory_path, pre_target=None, post_target=None):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :type all_targets: tuple[IntegrationTarget]
    :type inventory_path: str
    :type pre_target: (IntegrationTarget) -> None | None
    :type post_target: (IntegrationTarget) -> None | None
    """
    found = False
    passed = []
    failed = []

    targets_iter = iter(targets)
    all_targets_dict = dict((target.name, target) for target in all_targets)

    setup_errors = []
    setup_targets_executed = set()

    for target in all_targets:
        for setup_target in target.setup_once + target.setup_always:
            if setup_target not in all_targets_dict:
                setup_errors.append('Target "%s" contains invalid setup target: %s' % (target.name, setup_target))

    if setup_errors:
        raise ApplicationError('Found %d invalid setup aliases:\n%s' % (len(setup_errors), '\n'.join(setup_errors)))

    test_dir = os.path.expanduser('~/ansible_testing')

    if not args.explain and any('needs/ssh/' in target.aliases for target in targets):
        max_tries = 20
        display.info('SSH service required for tests. Checking to make sure we can connect.')
        for i in range(1, max_tries + 1):
            try:
                run_command(args, ['ssh', '-o', 'BatchMode=yes', 'localhost', 'id'], capture=True)
                display.info('SSH service responded.')
                break
            except SubprocessError:
                if i == max_tries:
                    raise
                seconds = 3
                display.warning('SSH service not responding. Waiting %d second(s) before checking again.' % seconds)
                time.sleep(seconds)

    # Windows is different as Ansible execution is done locally but the host is remote
    if args.inject_httptester and not isinstance(args, WindowsIntegrationConfig):
        inject_httptester(args)

    start_at_task = args.start_at_task

    results = {}

    current_environment = None  # type: EnvironmentDescription | None

    # common temporary directory path that will be valid on both the controller and the remote
    # it must be common because it will be referenced in environment variables that are shared across multiple hosts
    common_temp_path = '/tmp/ansible-test-%s' % ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

    setup_common_temp_dir(args, common_temp_path)

    try:
        for target in targets_iter:
            if args.start_at and not found:
                found = target.name == args.start_at

                if not found:
                    continue

            if args.list_targets:
                print(target.name)
                continue

            tries = 2 if args.retry_on_error else 1
            verbosity = args.verbosity

            cloud_environment = get_cloud_environment(args, target)

            original_environment = current_environment if current_environment else EnvironmentDescription(args)
            current_environment = None

            display.info('>>> Environment Description\n%s' % original_environment, verbosity=3)

            try:
                while tries:
                    tries -= 1

                    try:
                        if cloud_environment:
                            cloud_environment.setup_once()

                        run_setup_targets(args, test_dir, target.setup_once, all_targets_dict, setup_targets_executed, inventory_path, common_temp_path, False)

                        start_time = time.time()

                        run_setup_targets(args, test_dir, target.setup_always, all_targets_dict, setup_targets_executed, inventory_path, common_temp_path, True)

                        if not args.explain:
                            # create a fresh test directory for each test target
                            remove_tree(test_dir)
                            make_dirs(test_dir)

                        if pre_target:
                            pre_target(target)

                        try:
                            if target.script_path:
                                command_integration_script(args, target, test_dir, inventory_path, common_temp_path)
                            else:
                                command_integration_role(args, target, start_at_task, test_dir, inventory_path, common_temp_path)
                                start_at_task = None
                        finally:
                            if post_target:
                                post_target(target)

                        end_time = time.time()

                        results[target.name] = dict(
                            name=target.name,
                            type=target.type,
                            aliases=target.aliases,
                            modules=target.modules,
                            run_time_seconds=int(end_time - start_time),
                            setup_once=target.setup_once,
                            setup_always=target.setup_always,
                            coverage=args.coverage,
                            coverage_label=args.coverage_label,
                            python_version=args.python_version,
                        )

                        break
                    except SubprocessError:
                        if cloud_environment:
                            cloud_environment.on_failure(target, tries)

                        if not original_environment.validate(target.name, throw=False):
                            raise

                        if not tries:
                            raise

                        display.warning('Retrying test target "%s" with maximum verbosity.' % target.name)
                        display.verbosity = args.verbosity = 6

                start_time = time.time()
                current_environment = EnvironmentDescription(args)
                end_time = time.time()

                EnvironmentDescription.check(original_environment, current_environment, target.name, throw=True)

                results[target.name]['validation_seconds'] = int(end_time - start_time)

                passed.append(target)
            except Exception as ex:
                failed.append(target)

                if args.continue_on_error:
                    display.error(ex)
                    continue

                display.notice('To resume at this test target, use the option: --start-at %s' % target.name)

                next_target = next(targets_iter, None)

                if next_target:
                    display.notice('To resume after this test target, use the option: --start-at %s' % next_target.name)

                raise
            finally:
                display.verbosity = args.verbosity = verbosity

    finally:
        if not args.explain:
            if args.coverage:
                coverage_temp_path = os.path.join(common_temp_path, COVERAGE_OUTPUT_PATH)
                coverage_save_path = 'test/results/coverage'

                for filename in os.listdir(coverage_temp_path):
                    shutil.copy(os.path.join(coverage_temp_path, filename), os.path.join(coverage_save_path, filename))

            remove_tree(common_temp_path)

            results_path = 'test/results/data/%s-%s.json' % (args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.utcnow().replace(microsecond=0))))

            data = dict(
                targets=results,
            )

            with open(results_path, 'w') as results_fd:
                results_fd.write(json.dumps(data, sort_keys=True, indent=4))

    if failed:
        raise ApplicationError('The %d integration test(s) listed below (out of %d) failed. See error output above for details:\n%s' % (
            len(failed), len(passed) + len(failed), '\n'.join(target.name for target in failed)))


def start_httptester(args):
    """
    :type args: EnvironmentConfig
    :rtype: str, list[str]
    """

    # map ports from remote -> localhost -> container
    # passing through localhost is only used when ansible-test is not already running inside a docker container
    ports = [
        dict(
            remote=8080,
            container=80,
        ),
        dict(
            remote=8443,
            container=443,
        ),
    ]

    container_id = get_docker_container_id()

    if not container_id:
        for item in ports:
            item['localhost'] = get_available_port()

    docker_pull(args, args.httptester)

    httptester_id = run_httptester(args, dict((port['localhost'], port['container']) for port in ports if 'localhost' in port))

    if container_id:
        container_host = get_docker_container_ip(args, httptester_id)
        display.info('Found httptester container address: %s' % container_host, verbosity=1)
    else:
        container_host = get_docker_hostname()

    ssh_options = []

    for port in ports:
        ssh_options += ['-R', '%d:%s:%d' % (port['remote'], container_host, port.get('localhost', port['container']))]

    return httptester_id, ssh_options


def run_httptester(args, ports=None):
    """
    :type args: EnvironmentConfig
    :type ports: dict[int, int] | None
    :rtype: str
    """
    options = [
        '--detach',
    ]

    if ports:
        for localhost_port, container_port in ports.items():
            options += ['-p', '%d:%d' % (localhost_port, container_port)]

    network = get_docker_preferred_network_name(args)

    if is_docker_user_defined_network(network):
        # network-scoped aliases are only supported for containers in user defined networks
        for alias in HTTPTESTER_HOSTS:
            options.extend(['--network-alias', alias])

    httptester_id, _ = docker_run(args, args.httptester, options=options)

    if args.explain:
        httptester_id = 'httptester_id'
    else:
        httptester_id = httptester_id.strip()

    return httptester_id


def inject_httptester(args):
    """
    :type args: CommonConfig
    """
    comment = ' # ansible-test httptester\n'
    append_lines = ['127.0.0.1 %s%s' % (host, comment) for host in HTTPTESTER_HOSTS]

    with open('/etc/hosts', 'r+') as hosts_fd:
        original_lines = hosts_fd.readlines()

        if not any(line.endswith(comment) for line in original_lines):
            hosts_fd.writelines(append_lines)

    # determine which forwarding mechanism to use
    pfctl = find_executable('pfctl', required=False)
    iptables = find_executable('iptables', required=False)

    if pfctl:
        kldload = find_executable('kldload', required=False)

        if kldload:
            try:
                run_command(args, ['kldload', 'pf'], capture=True)
            except SubprocessError:
                pass  # already loaded

        rules = '''
rdr pass inet proto tcp from any to any port 80 -> 127.0.0.1 port 8080
rdr pass inet proto tcp from any to any port 443 -> 127.0.0.1 port 8443
'''
        cmd = ['pfctl', '-ef', '-']

        try:
            run_command(args, cmd, capture=True, data=rules)
        except SubprocessError:
            pass  # non-zero exit status on success

    elif iptables:
        ports = [
            (80, 8080),
            (443, 8443),
        ]

        for src, dst in ports:
            rule = ['-o', 'lo', '-p', 'tcp', '--dport', str(src), '-j', 'REDIRECT', '--to-port', str(dst)]

            try:
                # check for existing rule
                cmd = ['iptables', '-t', 'nat', '-C', 'OUTPUT'] + rule
                run_command(args, cmd, capture=True)
            except SubprocessError:
                # append rule when it does not exist
                cmd = ['iptables', '-t', 'nat', '-A', 'OUTPUT'] + rule
                run_command(args, cmd, capture=True)
    else:
        raise ApplicationError('No supported port forwarding mechanism detected.')


def run_setup_targets(args, test_dir, target_names, targets_dict, targets_executed, inventory_path, temp_path, always):
    """
    :type args: IntegrationConfig
    :type test_dir: str
    :type target_names: list[str]
    :type targets_dict: dict[str, IntegrationTarget]
    :type targets_executed: set[str]
    :type inventory_path: str
    :type temp_path: str
    :type always: bool
    """
    for target_name in target_names:
        if not always and target_name in targets_executed:
            continue

        target = targets_dict[target_name]

        if not args.explain:
            # create a fresh test directory for each test target
            remove_tree(test_dir)
            make_dirs(test_dir)

        if target.script_path:
            command_integration_script(args, target, test_dir, inventory_path, temp_path)
        else:
            command_integration_role(args, target, None, test_dir, inventory_path, temp_path)

        targets_executed.add(target_name)


def integration_environment(args, target, test_dir, inventory_path, ansible_config, env_config):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type test_dir: str
    :type inventory_path: str
    :type ansible_config: str | None
    :type env_config: CloudEnvironmentConfig | None
    :rtype: dict[str, str]
    """
    env = ansible_environment(args, ansible_config=ansible_config)

    if args.inject_httptester:
        env.update(dict(
            HTTPTESTER='1',
        ))

    callback_plugins = ['junit'] + (env_config.callback_plugins or [] if env_config else [])

    integration = dict(
        JUNIT_OUTPUT_DIR=os.path.abspath('test/results/junit'),
        ANSIBLE_CALLBACK_WHITELIST=','.join(sorted(set(callback_plugins))),
        ANSIBLE_TEST_CI=args.metadata.ci_provider or get_ci_provider().code,
        OUTPUT_DIR=test_dir,
        INVENTORY_PATH=os.path.abspath(inventory_path),
    )

    if args.debug_strategy:
        env.update(dict(ANSIBLE_STRATEGY='debug'))

    if 'non_local/' in target.aliases:
        if args.coverage:
            display.warning('Skipping coverage reporting on Ansible modules for non-local test: %s' % target.name)

        env.update(dict(ANSIBLE_TEST_REMOTE_INTERPRETER=''))

    env.update(integration)

    return env


def command_integration_script(args, target, test_dir, inventory_path, temp_path):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type test_dir: str
    :type inventory_path: str
    :type temp_path: str
    """
    display.info('Running %s integration test script' % target.name)

    env_config = None

    if isinstance(args, PosixIntegrationConfig):
        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            env_config = cloud_environment.get_environment_config()

    with integration_test_environment(args, target, inventory_path) as test_env:
        cmd = ['./%s' % os.path.basename(target.script_path)]

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config)
        cwd = os.path.join(test_env.integration_dir, 'targets', target.name)

        if env_config and env_config.env_vars:
            env.update(env_config.env_vars)

        with integration_test_config_file(args, env_config, test_env.integration_dir) as config_path:
            if config_path:
                cmd += ['-e', '@%s' % config_path]

            module_coverage = 'non_local/' not in target.aliases
            intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd, temp_path=temp_path, module_coverage=module_coverage)


def command_integration_role(args, target, start_at_task, test_dir, inventory_path, temp_path):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type start_at_task: str | None
    :type test_dir: str
    :type inventory_path: str
    :type temp_path: str
    """
    display.info('Running %s integration test role' % target.name)

    env_config = None

    if isinstance(args, WindowsIntegrationConfig):
        hosts = 'windows'
        gather_facts = False
    elif isinstance(args, NetworkIntegrationConfig):
        hosts = target.name[:target.name.find('_')]
        gather_facts = False
    else:
        hosts = 'testhost'
        gather_facts = True

        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            env_config = cloud_environment.get_environment_config()

    with integration_test_environment(args, target, inventory_path) as test_env:
        play = dict(
            hosts=hosts,
            gather_facts=gather_facts,
            vars_files=[
                os.path.relpath(test_env.vars_file, test_env.integration_dir),
            ],
            roles=[
                target.name,
            ],
        )

        if env_config:
            play.update(dict(
                vars=env_config.ansible_vars,
                environment=env_config.env_vars,
                module_defaults=env_config.module_defaults,
            ))

        playbook = json.dumps([play], indent=4, sort_keys=True)

        with named_temporary_file(args=args, directory=test_env.integration_dir, prefix='%s-' % target.name, suffix='.yml', content=playbook) as playbook_path:
            filename = os.path.basename(playbook_path)

            display.info('>>> Playbook: %s\n%s' % (filename, playbook.strip()), verbosity=3)

            cmd = ['ansible-playbook', filename, '-i', os.path.relpath(test_env.inventory_path, test_env.integration_dir)]

            if start_at_task:
                cmd += ['--start-at-task', start_at_task]

            if args.tags:
                cmd += ['--tags', args.tags]

            if args.skip_tags:
                cmd += ['--skip-tags', args.skip_tags]

            if args.diff:
                cmd += ['--diff']

            if isinstance(args, NetworkIntegrationConfig):
                if args.testcase:
                    cmd += ['-e', 'testcase=%s' % args.testcase]

            if args.verbosity:
                cmd.append('-' + ('v' * args.verbosity))

            env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config)
            cwd = test_env.integration_dir

            env['ANSIBLE_ROLES_PATH'] = os.path.abspath(os.path.join(test_env.integration_dir, 'targets'))

            module_coverage = 'non_local/' not in target.aliases
            intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd, temp_path=temp_path, module_coverage=module_coverage)


def command_units(args):
    """
    :type args: UnitsConfig
    """
    changes = get_changes_filter(args)
    require = args.require + changes
    include, exclude = walk_external_targets(walk_units_targets(), args.include, args.exclude, require)

    if not include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes, exclude=args.exclude)

    version_commands = []

    for version in SUPPORTED_PYTHON_VERSIONS:
        # run all versions unless version given, in which case run only that version
        if args.python and version != args.python_version:
            continue

        if args.requirements_mode != 'skip':
            install_command_requirements(args, version)

        env = ansible_environment(args)

        cmd = [
            'pytest',
            '--boxed',
            '-r', 'a',
            '-n', 'auto',
            '--color',
            'yes' if args.color else 'no',
            '--junit-xml',
            'test/results/junit/python%s-units.xml' % version,
        ]

        if args.collect_only:
            cmd.append('--collect-only')

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        if exclude:
            cmd += ['--ignore=%s' % target.path for target in exclude]

        cmd += [target.path for target in include]

        version_commands.append((version, cmd, env))

    if args.requirements_mode == 'only':
        sys.exit()

    for version, command, env in version_commands:
        display.info('Unit test with Python %s' % version)

        try:
            intercept_command(args, command, target_name='units', env=env, python_version=version)
        except SubprocessError as ex:
            # pytest exits with status code 5 when all tests are skipped, which isn't an error for our use case
            if ex.status != 5:
                raise


def get_changes_filter(args):
    """
    :type args: TestConfig
    :rtype: list[str]
    """
    paths = detect_changes(args)

    if not args.metadata.change_description:
        if paths:
            changes = categorize_changes(args, paths, args.command)
        else:
            changes = ChangeDescription()

        args.metadata.change_description = changes

    if paths is None:
        return []  # change detection not enabled, do not filter targets

    if not paths:
        raise NoChangesDetected()

    if args.metadata.change_description.targets is None:
        raise NoTestsForChanges()

    return args.metadata.change_description.targets


def detect_changes(args):
    """
    :type args: TestConfig
    :rtype: list[str] | None
    """
    if args.changed:
        paths = get_ci_provider().detect_changes(args)
    elif args.changed_from or args.changed_path:
        paths = args.changed_path or []
        if args.changed_from:
            with open(args.changed_from, 'r') as changes_fd:
                paths += changes_fd.read().splitlines()
    else:
        return None  # change detection not enabled

    if paths is None:
        return None  # act as though change detection not enabled, do not filter targets

    display.info('Detected changes in %d file(s).' % len(paths))

    for path in paths:
        display.info(path, verbosity=1)

    return paths


def get_integration_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    if args.tox:
        # tox has the same exclusions as the local environment
        return get_integration_local_filter(args, targets)

    if args.docker:
        return get_integration_docker_filter(args, targets)

    if args.remote:
        return get_integration_remote_filter(args, targets)

    return get_integration_local_filter(args, targets)


def common_integration_filter(args, targets, exclude):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :type exclude: list[str]
    """
    override_disabled = set(target for target in args.include if target.startswith('disabled/'))

    if not args.allow_disabled:
        skip = 'disabled/'
        override = [target.name for target in targets if override_disabled & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-disabled or prefixing with "disabled/": %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    override_unsupported = set(target for target in args.include if target.startswith('unsupported/'))

    if not args.allow_unsupported:
        skip = 'unsupported/'
        override = [target.name for target in targets if override_unsupported & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-unsupported or prefixing with "unsupported/": %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    override_unstable = set(target for target in args.include if target.startswith('unstable/'))

    if args.allow_unstable_changed:
        override_unstable |= set(args.metadata.change_description.focused_targets or [])

    if not args.allow_unstable:
        skip = 'unstable/'
        override = [target.name for target in targets if override_unstable & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-unstable or prefixing with "unstable/": %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    # only skip a Windows test if using --windows and all the --windows versions are defined in the aliases as skip/windows/%s
    if isinstance(args, WindowsIntegrationConfig) and args.windows:
        all_skipped = []
        not_skipped = []

        for target in targets:
            if "skip/windows/" not in target.aliases:
                continue

            skip_valid = []
            skip_missing = []
            for version in args.windows:
                if "skip/windows/%s/" % version in target.aliases:
                    skip_valid.append(version)
                else:
                    skip_missing.append(version)

            if skip_missing and skip_valid:
                not_skipped.append((target.name, skip_valid, skip_missing))
            elif skip_valid:
                all_skipped.append(target.name)

        if all_skipped:
            exclude.extend(all_skipped)
            skip_aliases = ["skip/windows/%s/" % w for w in args.windows]
            display.warning('Excluding tests marked "%s" which are set to skip with --windows %s: %s'
                            % ('", "'.join(skip_aliases), ', '.join(args.windows), ', '.join(all_skipped)))

        if not_skipped:
            for target, skip_valid, skip_missing in not_skipped:
                # warn when failing to skip due to lack of support for skipping only some versions
                display.warning('Including test "%s" which was marked to skip for --windows %s but not %s.'
                                % (target, ', '.join(skip_valid), ', '.join(skip_missing)))


def get_integration_local_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    exclude = []

    common_integration_filter(args, targets, exclude)

    if not args.allow_root and os.getuid() != 0:
        skip = 'needs/root/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require --allow-root or running as root: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    override_destructive = set(target for target in args.include if target.startswith('destructive/'))

    if not args.allow_destructive:
        skip = 'destructive/'
        override = [target.name for target in targets if override_destructive & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-destructive or prefixing with "destructive/" to run locally: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    exclude_targets_by_python_version(targets, args.python_version, exclude)

    return exclude


def get_integration_docker_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    exclude = []

    common_integration_filter(args, targets, exclude)

    skip = 'skip/docker/'
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which cannot run under docker: %s'
                        % (skip.rstrip('/'), ', '.join(skipped)))

    if not args.docker_privileged:
        skip = 'needs/privileged/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require --docker-privileged to run under docker: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    python_version = get_python_version(args, get_docker_completion(), args.docker_raw)

    exclude_targets_by_python_version(targets, python_version, exclude)

    return exclude


def get_integration_remote_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    parts = args.remote.split('/', 1)

    platform = parts[0]

    exclude = []

    common_integration_filter(args, targets, exclude)

    skip = 'skip/%s/' % platform
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on %s: %s'
                        % (skip.rstrip('/'), platform, ', '.join(skipped)))

    skip = 'skip/%s/' % args.remote.replace('/', '')
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on %s: %s'
                        % (skip.rstrip('/'), args.remote.replace('/', ' '), ', '.join(skipped)))

    python_version = get_python_version(args, get_remote_completion(), args.remote)

    exclude_targets_by_python_version(targets, python_version, exclude)

    return exclude


def exclude_targets_by_python_version(targets, python_version, exclude):
    """
    :type targets: tuple[IntegrationTarget]
    :type python_version: str
    :type exclude: list[str]
    """
    if not python_version:
        display.warning('Python version unknown. Unable to skip tests based on Python version.')
        return

    python_major_version = python_version.split('.')[0]

    skip = 'skip/python%s/' % python_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %s: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))

    skip = 'skip/python%s/' % python_major_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %s: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))


def get_python_version(args, configs, name):
    """
    :type args: EnvironmentConfig
    :type configs: dict[str, dict[str, str]]
    :type name: str
    """
    config = configs.get(name, {})
    config_python = config.get('python')

    if not config or not config_python:
        if args.python:
            return args.python

        display.warning('No Python version specified. '
                        'Use completion config or the --python option to specify one.', unique=True)

        return ''  # failure to provide a version may result in failures or reduced functionality later

    supported_python_versions = config_python.split(',')
    default_python_version = supported_python_versions[0]

    if args.python and args.python not in supported_python_versions:
        raise ApplicationError('Python %s is not supported by %s. Supported Python version(s) are: %s' % (
            args.python, name, ', '.join(sorted(supported_python_versions))))

    python_version = args.python or default_python_version

    return python_version


def get_python_interpreter(args, configs, name):
    """
    :type args: EnvironmentConfig
    :type configs: dict[str, dict[str, str]]
    :type name: str
    """
    if args.python_interpreter:
        return args.python_interpreter

    config = configs.get(name, {})

    if not config:
        if args.python:
            guess = 'python%s' % args.python
        else:
            guess = 'python'

        display.warning('Using "%s" as the Python interpreter. '
                        'Use completion config or the --python-interpreter option to specify the path.' % guess, unique=True)

        return guess

    python_version = get_python_version(args, configs, name)

    python_dir = config.get('python_dir', '/usr/bin')
    python_interpreter = os.path.join(python_dir, 'python%s' % python_version)
    python_interpreter = config.get('python%s' % python_version, python_interpreter)

    return python_interpreter


class EnvironmentDescription(object):
    """Description of current running environment."""
    def __init__(self, args):
        """Initialize snapshot of environment configuration.
        :type args: IntegrationConfig
        """
        self.args = args

        if self.args.explain:
            self.data = {}
            return

        warnings = []

        versions = ['']
        versions += SUPPORTED_PYTHON_VERSIONS
        versions += list(set(v.split('.')[0] for v in SUPPORTED_PYTHON_VERSIONS))

        python_paths = dict((v, find_executable('python%s' % v, required=False)) for v in sorted(versions))
        pip_paths = dict((v, find_executable('pip%s' % v, required=False)) for v in sorted(versions))
        program_versions = dict((v, self.get_version([python_paths[v], 'test/runner/versions.py'], warnings)) for v in sorted(python_paths) if python_paths[v])
        pip_interpreters = dict((v, self.get_shebang(pip_paths[v])) for v in sorted(pip_paths) if pip_paths[v])
        known_hosts_hash = self.get_hash(os.path.expanduser('~/.ssh/known_hosts'))

        for version in sorted(versions):
            self.check_python_pip_association(version, python_paths, pip_paths, pip_interpreters, warnings)

        for warning in warnings:
            display.warning(warning, unique=True)

        self.data = dict(
            python_paths=python_paths,
            pip_paths=pip_paths,
            program_versions=program_versions,
            pip_interpreters=pip_interpreters,
            known_hosts_hash=known_hosts_hash,
            warnings=warnings,
        )

    @staticmethod
    def check_python_pip_association(version, python_paths, pip_paths, pip_interpreters, warnings):
        """
        :type version: str
        :param python_paths: dict[str, str]
        :param pip_paths:  dict[str, str]
        :param pip_interpreters:  dict[str, str]
        :param warnings: list[str]
        """
        python_label = 'Python%s' % (' %s' % version if version else '')

        pip_path = pip_paths.get(version)
        python_path = python_paths.get(version)

        if not python_path and not pip_path:
            # neither python or pip is present for this version
            return

        if not python_path:
            warnings.append('A %s interpreter was not found, yet a matching pip was found at "%s".' % (python_label, pip_path))
            return

        if not pip_path:
            warnings.append('A %s interpreter was found at "%s", yet a matching pip was not found.' % (python_label, python_path))
            return

        pip_shebang = pip_interpreters.get(version)

        match = re.search(r'#!\s*(?P<command>[^\s]+)', pip_shebang)

        if not match:
            warnings.append('A %s pip was found at "%s", but it does not have a valid shebang: %s' % (python_label, pip_path, pip_shebang))
            return

        pip_interpreter = os.path.realpath(match.group('command'))
        python_interpreter = os.path.realpath(python_path)

        if pip_interpreter == python_interpreter:
            return

        try:
            identical = filecmp.cmp(pip_interpreter, python_interpreter)
        except OSError:
            identical = False

        if identical:
            return

        warnings.append('A %s pip was found at "%s", but it uses interpreter "%s" instead of "%s".' % (
            python_label, pip_path, pip_interpreter, python_interpreter))

    def __str__(self):
        """
        :rtype: str
        """
        return json.dumps(self.data, sort_keys=True, indent=4)

    def validate(self, target_name, throw):
        """
        :type target_name: str
        :type throw: bool
        :rtype: bool
        """
        current = EnvironmentDescription(self.args)

        return self.check(self, current, target_name, throw)

    @staticmethod
    def check(original, current, target_name, throw):
        """
        :type original: EnvironmentDescription
        :type current: EnvironmentDescription
        :type target_name: str
        :type throw: bool
        :rtype: bool
        """
        original_json = str(original)
        current_json = str(current)

        if original_json == current_json:
            return True

        unified_diff = '\n'.join(difflib.unified_diff(
            a=original_json.splitlines(),
            b=current_json.splitlines(),
            fromfile='original.json',
            tofile='current.json',
            lineterm='',
        ))

        message = ('Test target "%s" has changed the test environment!\n'
                   'If these changes are necessary, they must be reverted before the test finishes.\n'
                   '>>> Original Environment\n'
                   '%s\n'
                   '>>> Current Environment\n'
                   '%s\n'
                   '>>> Environment Diff\n'
                   '%s'
                   % (target_name, original_json, current_json, unified_diff))

        if throw:
            raise ApplicationError(message)

        display.error(message)

        return False

    @staticmethod
    def get_version(command, warnings):
        """
        :type command: list[str]
        :type warnings: list[str]
        :rtype: list[str]
        """
        try:
            stdout, stderr = raw_command(command, capture=True, cmd_verbosity=2)
        except SubprocessError as ex:
            warnings.append(u'%s' % ex)
            return None  # all failures are equal, we don't care why it failed, only that it did

        return [line.strip() for line in ((stdout or '').strip() + (stderr or '').strip()).splitlines()]

    @staticmethod
    def get_shebang(path):
        """
        :type path: str
        :rtype: str
        """
        with open(path) as script_fd:
            return script_fd.readline().strip()

    @staticmethod
    def get_hash(path):
        """
        :type path: str
        :rtype: str | None
        """
        if not os.path.exists(path):
            return None

        file_hash = hashlib.md5()

        with open(path, 'rb') as file_fd:
            file_hash.update(file_fd.read())

        return file_hash.hexdigest()


class NoChangesDetected(ApplicationWarning):
    """Exception when change detection was performed, but no changes were found."""
    def __init__(self):
        super(NoChangesDetected, self).__init__('No changes detected.')


class NoTestsForChanges(ApplicationWarning):
    """Exception when changes detected, but no tests trigger as a result."""
    def __init__(self):
        super(NoTestsForChanges, self).__init__('No tests found for detected changes.')


class Delegate(Exception):
    """Trigger command delegation."""
    def __init__(self, exclude=None, require=None, integration_targets=None):
        """
        :type exclude: list[str] | None
        :type require: list[str] | None
        :type integration_targets: tuple[IntegrationTarget] | None
        """
        super(Delegate, self).__init__()

        self.exclude = exclude or []
        self.require = require or []
        self.integration_targets = integration_targets or tuple()


class AllTargetsSkipped(ApplicationWarning):
    """All targets skipped."""
    def __init__(self):
        super(AllTargetsSkipped, self).__init__('All targets skipped.')
