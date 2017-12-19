"""Execute Ansible tests."""

from __future__ import absolute_import, print_function

import json
import os
import collections
import datetime
import re
import tempfile
import time
import textwrap
import functools
import pipes
import hashlib

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
    is_shippable,
    is_binary_file,
    find_pip,
    find_executable,
    raw_command,
    get_coverage_path,
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
    walk_compile_targets,
)

from lib.changes import (
    ShippableChanges,
    LocalChanges,
)

from lib.git import (
    Git,
)

from lib.classification import (
    categorize_changes,
)

from lib.config import (
    TestConfig,
    EnvironmentConfig,
    CompileConfig,
    IntegrationConfig,
    NetworkIntegrationConfig,
    PosixIntegrationConfig,
    ShellConfig,
    UnitsConfig,
    WindowsIntegrationConfig,
)

from lib.test import (
    TestMessage,
    TestSuccess,
    TestFailure,
    TestSkipped,
)

SUPPORTED_PYTHON_VERSIONS = (
    '2.6',
    '2.7',
    '3.5',
    '3.6',
    '3.7',
)

COMPILE_PYTHON_VERSIONS = SUPPORTED_PYTHON_VERSIONS


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


def install_command_requirements(args):
    """
    :type args: EnvironmentConfig
    """
    generate_egg_info(args)

    if not args.requirements:
        return

    packages = []

    if isinstance(args, TestConfig):
        if args.coverage:
            packages.append('coverage')
        if args.junit:
            packages.append('junit-xml')

    pip = find_pip(version=args.python_version)

    commands = [generate_pip_install(pip, args.command, packages=packages)]

    if isinstance(args, IntegrationConfig):
        for cloud_platform in get_cloud_platforms(args):
            commands.append(generate_pip_install(pip, '%s.cloud.%s' % (args.command, cloud_platform)))

    commands = [cmd for cmd in commands if cmd]

    # only look for changes when more than one requirements file is needed
    detect_pip_changes = len(commands) > 1

    # first pass to install requirements, changes expected unless environment is already set up
    changes = run_pip_commands(args, pip, commands, detect_pip_changes)

    if not changes:
        return  # no changes means we can stop early

    # second pass to check for conflicts in requirements, changes are not expected here
    changes = run_pip_commands(args, pip, commands, detect_pip_changes)

    if not changes:
        return  # no changes means no conflicts

    raise ApplicationError('Conflicts detected in requirements. The following commands reported changes during verification:\n%s' %
                           '\n'.join((' '.join(pipes.quote(c) for c in cmd) for cmd in changes)))


def run_pip_commands(args, pip, commands, detect_pip_changes=False):
    """
    :type args: EnvironmentConfig
    :type pip: str
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

        try:
            run_command(args, cmd)
        except SubprocessError as ex:
            if ex.status != 2:
                raise

            # If pip is too old it won't understand the arguments we passed in, so we'll need to upgrade it.

            # Installing "coverage" on ubuntu 16.04 fails with the error:
            # AttributeError: 'Requirement' object has no attribute 'project_name'
            # See: https://bugs.launchpad.net/ubuntu/xenial/+source/python-pip/+bug/1626258
            # Upgrading pip works around the issue.
            run_command(args, [pip, 'install', '--upgrade', 'pip'])
            run_command(args, cmd)

        after_list = pip_list(args, pip) if detect_pip_changes else None

        if before_list != after_list:
            changes.append(cmd)

    return changes


def pip_list(args, pip):
    """
    :type args: EnvironmentConfig
    :type pip: str
    :rtype: str
    """
    stdout, _ = run_command(args, [pip, 'list'], capture=True)
    return stdout


def generate_egg_info(args):
    """
    :type args: EnvironmentConfig
    """
    if os.path.isdir('lib/ansible.egg-info'):
        return

    run_command(args, ['python%s' % args.python_version, 'setup.py', 'egg_info'], capture=args.verbosity < 3)


def generate_pip_install(pip, command, packages=None):
    """
    :type pip: str
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

    return [pip, 'install', '--disable-pip-version-check', '-c', constraints] + options


def command_shell(args):
    """
    :type args: ShellConfig
    """
    if args.delegate:
        raise Delegate()

    install_command_requirements(args)

    cmd = create_shell_command(['bash', '-i'])
    run_command(args, cmd)


def command_posix_integration(args):
    """
    :type args: PosixIntegrationConfig
    """
    all_targets = tuple(walk_posix_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets)
    command_integration_filtered(args, internal_targets, all_targets)


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
        get_coverage_path(args)  # initialize before starting threads

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
        command_integration_filtered(args, internal_targets, all_targets)
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

        if platform_target not in platform_targets and 'network/basics/' not in platform_targets:
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

    if args.windows:
        get_coverage_path(args)  # initialize before starting threads

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

    success = False

    try:
        command_integration_filtered(args, internal_targets, all_targets)
        success = True
    finally:
        if args.remote_terminate == 'always' or (args.remote_terminate == 'success' and success):
            for instance in instances:
                instance.result.stop()


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
    require = (args.require or []) + changes
    exclude = (args.exclude or [])

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
        raise Delegate(require=changes, exclude=exclude)

    install_command_requirements(args)

    return internal_targets


def command_integration_filtered(args, targets, all_targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :type all_targets: tuple[IntegrationTarget]
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

    start_at_task = args.start_at_task

    results = {}

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

        original_environment = EnvironmentDescription(args)

        display.info('>>> Environment Description\n%s' % original_environment, verbosity=3)

        try:
            while tries:
                tries -= 1

                try:
                    run_setup_targets(args, test_dir, target.setup_once, all_targets_dict, setup_targets_executed, False)

                    start_time = time.time()

                    run_setup_targets(args, test_dir, target.setup_always, all_targets_dict, setup_targets_executed, True)

                    if not args.explain:
                        # create a fresh test directory for each test target
                        remove_tree(test_dir)
                        make_dirs(test_dir)

                    if target.script_path:
                        command_integration_script(args, target)
                    else:
                        command_integration_role(args, target, start_at_task)
                        start_at_task = None

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

            original_environment.validate(target.name, throw=True)
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

    if not args.explain:
        results_path = 'test/results/data/%s-%s.json' % (args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.utcnow().replace(microsecond=0))))

        data = dict(
            targets=results,
        )

        with open(results_path, 'w') as results_fd:
            results_fd.write(json.dumps(data, sort_keys=True, indent=4))

    if failed:
        raise ApplicationError('The %d integration test(s) listed below (out of %d) failed. See error output above for details:\n%s' % (
            len(failed), len(passed) + len(failed), '\n'.join(target.name for target in failed)))


def run_setup_targets(args, test_dir, target_names, targets_dict, targets_executed, always):
    """
    :param args: IntegrationConfig
    :param test_dir: str
    :param target_names: list[str]
    :param targets_dict: dict[str, IntegrationTarget]
    :param targets_executed: set[str]
    :param always: bool
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
            command_integration_script(args, target)
        else:
            command_integration_role(args, target, None)

        targets_executed.add(target_name)


def integration_environment(args, target, cmd):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type cmd: list[str]
    :rtype: dict[str, str]
    """
    env = ansible_environment(args)

    integration = dict(
        JUNIT_OUTPUT_DIR=os.path.abspath('test/results/junit'),
        ANSIBLE_CALLBACK_WHITELIST='junit',
        ANSIBLE_TEST_CI=args.metadata.ci_provider,
    )

    if args.debug_strategy:
        env.update(dict(ANSIBLE_STRATEGY='debug'))

    if 'non_local/' in target.aliases:
        if args.coverage:
            display.warning('Skipping coverage reporting for non-local test: %s' % target.name)

        env.update(dict(ANSIBLE_TEST_REMOTE_INTERPRETER=''))

    env.update(integration)

    cloud_environment = get_cloud_environment(args, target)

    if cloud_environment:
        cloud_environment.configure_environment(env, cmd)

    return env


def command_integration_script(args, target):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    """
    display.info('Running %s integration test script' % target.name)

    cmd = ['./%s' % os.path.basename(target.script_path)]

    if args.verbosity:
        cmd.append('-' + ('v' * args.verbosity))

    env = integration_environment(args, target, cmd)
    cwd = target.path

    intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd)


def command_integration_role(args, target, start_at_task):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type start_at_task: str | None
    """
    display.info('Running %s integration test role' % target.name)

    vars_file = 'integration_config.yml'

    if isinstance(args, WindowsIntegrationConfig):
        inventory = 'inventory.winrm'
        hosts = 'windows'
        gather_facts = False
    elif isinstance(args, NetworkIntegrationConfig):
        inventory = args.inventory or 'inventory.networking'
        hosts = target.name[:target.name.find('_')]
        gather_facts = False
    else:
        inventory = 'inventory'
        hosts = 'testhost'
        gather_facts = True

        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            hosts = cloud_environment.inventory_hosts or hosts

    playbook = '''
- hosts: %s
  gather_facts: %s
  roles:
    - { role: %s }
    ''' % (hosts, gather_facts, target.name)

    with tempfile.NamedTemporaryFile(dir='test/integration', prefix='%s-' % target.name, suffix='.yml') as pb_fd:
        pb_fd.write(playbook.encode('utf-8'))
        pb_fd.flush()

        filename = os.path.basename(pb_fd.name)

        display.info('>>> Playbook: %s\n%s' % (filename, playbook.strip()), verbosity=3)

        cmd = ['ansible-playbook', filename, '-i', inventory, '-e', '@%s' % vars_file]

        if start_at_task:
            cmd += ['--start-at-task', start_at_task]

        if args.tags:
            cmd += ['--tags', args.tags]

        if args.skip_tags:
            cmd += ['--skip-tags', args.skip_tags]

        if args.diff:
            cmd += ['--diff']

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        env = integration_environment(args, target, cmd)
        cwd = 'test/integration'

        env['ANSIBLE_ROLES_PATH'] = os.path.abspath('test/integration/targets')

        intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd)


def command_units(args):
    """
    :type args: UnitsConfig
    """
    changes = get_changes_filter(args)
    require = (args.require or []) + changes
    include, exclude = walk_external_targets(walk_units_targets(), args.include, args.exclude, require)

    if not include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes)

    install_command_requirements(args)

    version_commands = []

    for version in SUPPORTED_PYTHON_VERSIONS:
        # run all versions unless version given, in which case run only that version
        if args.python and version != args.python_version:
            continue

        env = ansible_environment(args)

        cmd = [
            'pytest',
            '--boxed',
            '-r', 'a',
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

    for version, command, env in version_commands:
        display.info('Unit test with Python %s' % version)

        try:
            intercept_command(args, command, target_name='units', env=env, python_version=version)
        except SubprocessError as ex:
            # pytest exits with status code 5 when all tests are skipped, which isn't an error for our use case
            if ex.status != 5:
                raise


def command_compile(args):
    """
    :type args: CompileConfig
    """
    changes = get_changes_filter(args)
    require = (args.require or []) + changes
    include, exclude = walk_external_targets(walk_compile_targets(), args.include, args.exclude, require)

    if not include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes)

    install_command_requirements(args)

    total = 0
    failed = []

    for version in COMPILE_PYTHON_VERSIONS:
        # run all versions unless version given, in which case run only that version
        if args.python and version != args.python_version:
            continue

        display.info('Compile with Python %s' % version)

        result = compile_version(args, version, include, exclude)
        result.write(args)

        total += 1

        if isinstance(result, TestFailure):
            failed.append('compile --python %s' % version)

    if failed:
        message = 'The %d compile test(s) listed below (out of %d) failed. See error output above for details.\n%s' % (
            len(failed), total, '\n'.join(failed))

        if args.failure_ok:
            display.error(message)
        else:
            raise ApplicationError(message)


def compile_version(args, python_version, include, exclude):
    """
    :type args: CompileConfig
    :type python_version: str
    :type include: tuple[CompletionTarget]
    :type exclude: tuple[CompletionTarget]
    :rtype: TestResult
    """
    command = 'compile'
    test = ''

    # optional list of regex patterns to exclude from tests
    skip_file = 'test/compile/python%s-skip.txt' % python_version

    if os.path.exists(skip_file):
        with open(skip_file, 'r') as skip_fd:
            skip_paths = skip_fd.read().splitlines()
    else:
        skip_paths = []

    # augment file exclusions
    skip_paths += [e.path for e in exclude]

    skip_paths = sorted(skip_paths)

    python = 'python%s' % python_version
    cmd = [python, 'test/compile/compile.py']

    if skip_paths:
        cmd += ['-x', '|'.join(skip_paths)]

    cmd += [target.path if target.path == '.' else './%s' % target.path for target in include]

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return TestSkipped(command, test, python_version=python_version)

    pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

    results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

    results = [TestMessage(
        message=r['message'],
        path=r['path'].replace('./', ''),
        line=int(r['line']),
        column=int(r['column']),
    ) for r in results]

    if results:
        return TestFailure(command, test, messages=results, python_version=python_version)

    return TestSuccess(command, test, python_version=python_version)


def get_changes_filter(args):
    """
    :type args: TestConfig
    :rtype: list[str]
    """
    paths = detect_changes(args)

    if paths is None:
        return []  # change detection not enabled, do not filter targets

    if not paths:
        raise NoChangesDetected()

    commands = categorize_changes(args, paths, args.command)

    targets = commands.get(args.command)

    if targets is None:
        raise NoTestsForChanges()

    if targets == ['all']:
        return []  # changes require testing all targets, do not filter targets

    return targets


def detect_changes(args):
    """
    :type args: TestConfig
    :rtype: list[str] | None
    """
    if args.changed and is_shippable():
        display.info('Shippable detected, collecting parameters from environment.')
        paths = detect_changes_shippable(args)
    elif args.changed_from or args.changed_path:
        paths = args.changed_path or []
        if args.changed_from:
            with open(args.changed_from, 'r') as changes_fd:
                paths += changes_fd.read().splitlines()
    elif args.changed:
        paths = detect_changes_local(args)
    else:
        return None  # change detection not enabled

    if paths is None:
        return None  # act as though change detection not enabled, do not filter targets

    display.info('Detected changes in %d file(s).' % len(paths))

    for path in paths:
        display.info(path, verbosity=1)

    return paths


def detect_changes_shippable(args):
    """Initialize change detection on Shippable.
    :type args: TestConfig
    :rtype: list[str] | None
    """
    git = Git(args)
    result = ShippableChanges(args, git)

    if result.is_pr:
        job_type = 'pull request'
    elif result.is_tag:
        job_type = 'tag'
    else:
        job_type = 'merge commit'

    display.info('Processing %s for branch %s commit %s' % (job_type, result.branch, result.commit))

    if not args.metadata.changes:
        args.metadata.populate_changes(result.diff)

    return result.paths


def detect_changes_local(args):
    """
    :type args: TestConfig
    :rtype: list[str]
    """
    git = Git(args)
    result = LocalChanges(args, git)

    display.info('Detected branch %s forked from %s at commit %s' % (
        result.current_branch, result.fork_branch, result.fork_point))

    if result.untracked and not args.untracked:
        display.warning('Ignored %s untracked file(s). Use --untracked to include them.' %
                        len(result.untracked))

    if result.committed and not args.committed:
        display.warning('Ignored %s committed change(s). Omit --ignore-committed to include them.' %
                        len(result.committed))

    if result.staged and not args.staged:
        display.warning('Ignored %s staged change(s). Omit --ignore-staged to include them.' %
                        len(result.staged))

    if result.unstaged and not args.unstaged:
        display.warning('Ignored %s unstaged change(s). Omit --ignore-unstaged to include them.' %
                        len(result.unstaged))

    names = set()

    if args.tracked:
        names |= set(result.tracked)
    if args.untracked:
        names |= set(result.untracked)
    if args.committed:
        names |= set(result.committed)
    if args.staged:
        names |= set(result.staged)
    if args.unstaged:
        names |= set(result.unstaged)

    if not args.metadata.changes:
        args.metadata.populate_changes(result.diff)

        for path in result.untracked:
            if is_binary_file(path):
                args.metadata.changes[path] = ((0, 0),)
                continue

            with open(path, 'r') as source_fd:
                line_count = len(source_fd.read().splitlines())

            args.metadata.changes[path] = ((1, line_count),)

    return sorted(names)


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


def get_integration_local_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    exclude = []

    if os.getuid() != 0:
        skip = 'needs/root/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require running as root: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    # consider explicit testing of destructive as though --allow-destructive was given
    include_destructive = any(target.startswith('destructive/') for target in args.include)

    if not args.allow_destructive and not include_destructive:
        skip = 'destructive/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require --allow-destructive to run locally: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    if args.python_version.startswith('3'):
        python_version = 3
    else:
        python_version = 2

    skip = 'skip/python%d/' % python_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %d: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))

    return exclude


def get_integration_docker_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    exclude = []

    if not args.docker_privileged:
        skip = 'needs/privileged/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require --docker-privileged to run under docker: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    python_version = 2  # images are expected to default to python 2 unless otherwise specified

    if args.docker.endswith('py3'):
        python_version = 3  # docker images ending in 'py3' are expected to default to python 3

    if args.docker.endswith(':default'):
        python_version = 3  # docker images tagged 'default' are expected to default to python 3

    if args.python:  # specifying a numeric --python option overrides the default python
        if args.python.startswith('3'):
            python_version = 3
        elif args.python.startswith('2'):
            python_version = 2

    skip = 'skip/python%d/' % python_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %d: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))

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

    skip = 'skip/%s/' % platform
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on %s: %s'
                        % (skip.rstrip('/'), platform, ', '.join(skipped)))

    python_version = 2  # remotes are expected to default to python 2

    skip = 'skip/python%d/' % python_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %d: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))

    return exclude


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

        versions = ['']
        versions += SUPPORTED_PYTHON_VERSIONS
        versions += list(set(v.split('.')[0] for v in SUPPORTED_PYTHON_VERSIONS))

        python_paths = dict((v, find_executable('python%s' % v, required=False)) for v in sorted(versions))
        python_versions = dict((v, self.get_version([python_paths[v], '-V'])) for v in sorted(python_paths) if python_paths[v])

        pip_paths = dict((v, find_executable('pip%s' % v, required=False)) for v in sorted(versions))
        pip_versions = dict((v, self.get_version([pip_paths[v], '--version'])) for v in sorted(pip_paths) if pip_paths[v])
        pip_interpreters = dict((v, self.get_shebang(pip_paths[v])) for v in sorted(pip_paths) if pip_paths[v])
        known_hosts_hash = self.get_hash(os.path.expanduser('~/.ssh/known_hosts'))

        self.data = dict(
            python_paths=python_paths,
            python_versions=python_versions,
            pip_paths=pip_paths,
            pip_versions=pip_versions,
            pip_interpreters=pip_interpreters,
            known_hosts_hash=known_hosts_hash,
        )

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

        original_json = str(self)
        current_json = str(current)

        if original_json == current_json:
            return True

        message = ('Test target "%s" has changed the test environment!\n'
                   'If these changes are necessary, they must be reverted before the test finishes.\n'
                   '>>> Original Environment\n'
                   '%s\n'
                   '>>> Current Environment\n'
                   '%s' % (target_name, original_json, current_json))

        if throw:
            raise ApplicationError(message)

        display.error(message)

        return False

    @staticmethod
    def get_version(command):
        """
        :type command: list[str]
        :rtype: str
        """
        try:
            stdout, stderr = raw_command(command, capture=True, cmd_verbosity=2)
        except SubprocessError:
            return None  # all failures are equal, we don't care why it failed, only that it did

        return (stdout or '').strip() + (stderr or '').strip()

    @staticmethod
    def get_shebang(path):
        """
        :type path: str
        :rtype: str
        """
        with open(path) as script_fd:
            return script_fd.readline()

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
    def __init__(self, exclude=None, require=None):
        """
        :type exclude: list[str] | None
        :type require: list[str] | None
        """
        super(Delegate, self).__init__()

        self.exclude = exclude or []
        self.require = require or []


class AllTargetsSkipped(ApplicationWarning):
    """All targets skipped."""
    def __init__(self):
        super(AllTargetsSkipped, self).__init__('All targets skipped.')
