"""Execute Ansible tests."""

from __future__ import absolute_import, print_function

import glob
import os
import tempfile
import sys
import time
import textwrap
import functools
import shutil
import stat
import random
import pipes
import string
import atexit

import lib.pytar
import lib.thread

from lib.core_ci import (
    AnsibleCoreCI,
)

from lib.manage_ci import (
    ManageWindowsCI,
    ManageNetworkCI,
)

from lib.util import (
    CommonConfig,
    ApplicationWarning,
    ApplicationError,
    SubprocessError,
    display,
    run_command,
    deepest_path,
    common_environment,
    remove_tree,
    make_dirs,
    is_shippable,
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
    walk_sanity_targets,
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

SUPPORTED_PYTHON_VERSIONS = (
    '2.6',
    '2.7',
    '3.5',
    '3.6',
)

COMPILE_PYTHON_VERSIONS = tuple(sorted(SUPPORTED_PYTHON_VERSIONS + ('2.4',)))

coverage_path = ''  # pylint: disable=locally-disabled, invalid-name


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

    cmd = generate_pip_install(args.command)

    if not cmd:
        return

    if isinstance(args, TestConfig):
        if args.coverage:
            cmd += ['coverage']

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
        run_command(args, ['pip', 'install', '--upgrade', 'pip'])
        run_command(args, cmd)


def generate_egg_info(args):
    """
    :type args: EnvironmentConfig
    """
    if os.path.isdir('lib/ansible.egg-info'):
        return

    run_command(args, ['python', 'setup.py', 'egg_info'], capture=args.verbosity < 3)


def generate_pip_install(command):
    """
    :type command: str
    :return: list[str] | None
    """
    constraints = 'test/runner/requirements/constraints.txt'
    requirements = 'test/runner/requirements/%s.txt' % command

    if not os.path.exists(requirements) or not os.path.getsize(requirements):
        return None

    return ['pip', 'install', '--disable-pip-version-check', '-r', requirements, '-c', constraints]


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
    internal_targets = command_integration_filter(args, walk_posix_integration_targets())
    command_integration_filtered(args, internal_targets)


def command_network_integration(args):
    """
    :type args: NetworkIntegrationConfig
    """
    internal_targets = command_integration_filter(args, walk_network_integration_targets())

    if args.platform:
        instances = []  # type: list [lib.thread.WrappedThread]

        for platform_version in args.platform:
            platform, version = platform_version.split('/', 1)
            instance = lib.thread.WrappedThread(functools.partial(network_run, args, platform, version))
            instance.daemon = True
            instance.start()
            instances.append(instance)

        install_command_requirements(args)

        while any(instance.is_alive() for instance in instances):
            time.sleep(1)

        remotes = [instance.wait_for_result() for instance in instances]
        inventory = network_inventory(remotes)

        if not args.explain:
            with open('test/integration/inventory.networking', 'w') as inventory_fd:
                display.info('>>> Inventory: %s\n%s' % (inventory_fd.name, inventory.strip()), verbosity=3)
                inventory_fd.write(inventory)
    else:
        install_command_requirements(args)

    command_integration_filtered(args, internal_targets)


def network_run(args, platform, version):
    """
    :type args: NetworkIntegrationConfig
    :type platform: str
    :type version: str
    :rtype: AnsibleCoreCI
    """

    core_ci = AnsibleCoreCI(args, platform, version, stage=args.remote_stage)
    core_ci.start()
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
        groups[remote.platform].append(
            '%s ansible_host=%s ansible_user=%s ansible_connection=network_cli ansible_ssh_private_key_file=%s' % (
                remote.name.replace('.', '_'),
                remote.connection.hostname,
                remote.connection.username,
                remote.ssh_key.key,
            )
        )

    template = ''

    for group in groups:
        hosts = '\n'.join(groups[group])

        template += """
        [%s]
        %s
        """ % (group, hosts)

    inventory = textwrap.dedent(template)

    return inventory


def command_windows_integration(args):
    """
    :type args: WindowsIntegrationConfig
    """
    internal_targets = command_integration_filter(args, walk_windows_integration_targets())

    if args.windows:
        instances = []  # type: list [lib.thread.WrappedThread]

        for version in args.windows:
            instance = lib.thread.WrappedThread(functools.partial(windows_run, args, version))
            instance.daemon = True
            instance.start()
            instances.append(instance)

        install_command_requirements(args)

        while any(instance.is_alive() for instance in instances):
            time.sleep(1)

        remotes = [instance.wait_for_result() for instance in instances]
        inventory = windows_inventory(remotes)

        if not args.explain:
            with open('test/integration/inventory.winrm', 'w') as inventory_fd:
                display.info('>>> Inventory: %s\n%s' % (inventory_fd.name, inventory.strip()), verbosity=3)
                inventory_fd.write(inventory)
    else:
        install_command_requirements(args)

    try:
        command_integration_filtered(args, internal_targets)
    finally:
        pass


def windows_run(args, version):
    """
    :type args: WindowsIntegrationConfig
    :type version: str
    :rtype: AnsibleCoreCI
    """
    core_ci = AnsibleCoreCI(args, 'windows', version, stage=args.remote_stage)
    core_ci.start()
    core_ci.wait()

    manage = ManageWindowsCI(core_ci)
    manage.wait()

    return core_ci


def windows_inventory(remotes):
    """
    :type remotes: list[AnsibleCoreCI]
    :rtype: str
    """
    hosts = ['%s ansible_host=%s ansible_user=%s ansible_password="%s" ansible_port=%s' %
             (
                 remote.name.replace('/', '_'),
                 remote.connection.hostname,
                 remote.connection.username,
                 remote.connection.password,
                 remote.connection.port,
             )
             for remote in remotes]

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


def command_integration_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: collections.Iterable[IntegrationTarget]
    :rtype: tuple[IntegrationTarget]
    """
    targets = tuple(targets)
    changes = get_changes_filter(args)
    require = (args.require or []) + changes
    exclude = (args.exclude or [])

    internal_targets = walk_internal_targets(targets, args.include, exclude, require)
    environment_exclude = get_integration_filter(args, internal_targets)

    if environment_exclude:
        exclude += environment_exclude
        internal_targets = walk_internal_targets(targets, args.include, exclude, require)

    if not internal_targets:
        raise AllTargetsSkipped()

    if args.start_at and not any(t.name == args.start_at for t in internal_targets):
        raise ApplicationError('Start at target matches nothing: %s' % args.start_at)

    if args.delegate:
        raise Delegate(require=changes, exclude=exclude)

    install_command_requirements(args)

    return internal_targets


def command_integration_filtered(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    """
    found = False

    targets_iter = iter(targets)

    test_dir = os.path.expanduser('~/ansible_testing')

    if not args.explain:
        remove_tree(test_dir)
        make_dirs(test_dir)

    if any('needs/ssh/' in target.aliases for target in targets):
        max_tries = 20
        display.info('SSH service required for tests. Checking to make sure we can connect.')
        for i in range(1, max_tries + 1):
            try:
                run_command(args, ['ssh', '-o', 'BatchMode=yes', 'localhost', 'id'], capture=True)
                display.info('SSH service responded.')
                break
            except SubprocessError as ex:
                if i == max_tries:
                    raise ex
                seconds = 3
                display.warning('SSH service not responding. Waiting %d second(s) before checking again.' % seconds)
                time.sleep(seconds)

    start_at_task = args.start_at_task

    for target in targets_iter:
        if args.start_at and not found:
            found = target.name == args.start_at

            if not found:
                continue

        tries = 2 if args.retry_on_error else 1
        verbosity = args.verbosity

        try:
            while tries:
                tries -= 1

                try:
                    if target.script_path:
                        command_integration_script(args, target)
                    else:
                        command_integration_role(args, target, start_at_task)
                        start_at_task = None
                    break
                except SubprocessError:
                    if not tries:
                        raise

                    display.warning('Retrying test target "%s" with maximum verbosity.' % target.name)
                    display.verbosity = args.verbosity = 6
        except:
            display.notice('To resume at this test target, use the option: --start-at %s' % target.name)

            next_target = next(targets_iter, None)

            if next_target:
                display.notice('To resume after this test target, use the option: --start-at %s' % next_target.name)

            raise
        finally:
            display.verbosity = args.verbosity = verbosity


def integration_environment(args):
    """
    :type args: IntegrationConfig
    :rtype: dict[str, str]
    """
    env = ansible_environment(args)

    integration = dict(
        JUNIT_OUTPUT_DIR=os.path.abspath('test/results/junit'),
        ANSIBLE_CALLBACK_WHITELIST='junit',
    )

    env.update(integration)

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

    env = integration_environment(args)
    cwd = target.path

    intercept_command(args, cmd, env=env, cwd=cwd)


def command_integration_role(args, target, start_at_task):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type start_at_task: str
    """
    display.info('Running %s integration test role' % target.name)

    vars_file = 'integration_config.yml'

    if 'windows/' in target.aliases:
        inventory = 'inventory.winrm'
        hosts = 'windows'
        gather_facts = False
    elif 'network/' in target.aliases:
        inventory = 'inventory.networking'
        hosts = target.name[:target.name.find('_')]
        gather_facts = False
        if hosts == 'net':
            hosts = 'all'
    else:
        inventory = 'inventory'
        hosts = 'testhost'
        gather_facts = True

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

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        env = integration_environment(args)
        cwd = 'test/integration'

        env['ANSIBLE_ROLES_PATH'] = os.path.abspath('test/integration/targets')

        intercept_command(args, cmd, env=env, cwd=cwd)


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
        if args.python and version != args.python:
            continue

        env = ansible_environment(args)

        cmd = [
            'pytest',
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
            intercept_command(args, command, env=env, python_version=version)
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

    version_commands = []

    for version in COMPILE_PYTHON_VERSIONS:
        # run all versions unless version given, in which case run only that version
        if args.python and version != args.python:
            continue

        # optional list of regex patterns to exclude from tests
        skip_file = 'test/compile/python%s-skip.txt' % version

        if os.path.exists(skip_file):
            with open(skip_file, 'r') as skip_fd:
                skip_paths = skip_fd.read().splitlines()
        else:
            skip_paths = []

        # augment file exclusions
        skip_paths += [e.path for e in exclude]
        skip_paths.append('/.tox/')

        skip_paths = sorted(skip_paths)

        python = 'python%s' % version
        cmd = [python, '-m', 'compileall', '-fq']

        if skip_paths:
            cmd += ['-x', '|'.join(skip_paths)]

        cmd += [target.path if target.path == '.' else './%s' % target.path for target in include]

        version_commands.append((version, cmd))

    for version, command in version_commands:
        display.info('Compile with Python %s' % version)
        run_command(args, command)


def command_sanity(args):
    """
    :type args: SanityConfig
    """
    changes = get_changes_filter(args)
    require = (args.require or []) + changes
    targets = SanityTargets(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes)

    install_command_requirements(args)

    tests = SANITY_TESTS

    if args.test:
        tests = [t for t in tests if t.name in args.test]

    if args.skip_test:
        tests = [t for t in tests if t.name not in args.skip_test]

    for test in tests:
        if args.list_tests:
            display.info(test.name)
            continue

        if test.intercept:
            versions = SUPPORTED_PYTHON_VERSIONS
        else:
            versions = None,

        for version in versions:
            if args.python and version and version != args.python:
                continue

            display.info('Sanity check using %s%s' % (test.name, ' with Python %s' % version if version else ''))

            if test.intercept:
                test.func(args, targets, python_version=version)
            else:
                test.func(args, targets)


def command_sanity_code_smell(args, _):
    """
    :type args: SanityConfig
    :type _: SanityTargets
    """
    with open('test/sanity/code-smell/skip.txt', 'r') as skip_fd:
        skip_tests = skip_fd.read().splitlines()

    tests = glob.glob('test/sanity/code-smell/*')
    tests = sorted(p for p in tests
                   if os.access(p, os.X_OK)
                   and os.path.isfile(p)
                   and os.path.basename(p) not in skip_tests)

    for test in tests:
        display.info('Code smell check using %s' % os.path.basename(test))
        run_command(args, [test])


def command_sanity_validate_modules(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    env = ansible_environment(args)

    paths = [deepest_path(i.path, 'lib/ansible/modules/') for i in targets.include_external]
    paths = sorted(set(p for p in paths if p))

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    cmd = ['test/sanity/validate-modules/validate-modules'] + paths

    with open('test/sanity/validate-modules/skip.txt', 'r') as skip_fd:
        skip_paths = skip_fd.read().splitlines()

    skip_paths += [e.path for e in targets.exclude_external]

    if skip_paths:
        cmd += ['--exclude', '^(%s)' % '|'.join(skip_paths)]

    run_command(args, cmd, env=env)


def command_sanity_shellcheck(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    with open('test/sanity/shellcheck/skip.txt', 'r') as skip_fd:
        skip_paths = set(skip_fd.read().splitlines())

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.sh' and i.path not in skip_paths)

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    run_command(args, ['shellcheck'] + paths)


def command_sanity_yamllint(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    """
    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml'))

    if not paths:
        display.info('No tests applicable.', verbosity=1)
        return

    run_command(args, ['yamllint'] + paths)


def command_sanity_ansible_doc(args, targets, python_version):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :type python_version: str
    """
    with open('test/sanity/ansible-doc/skip.txt', 'r') as skip_fd:
        skip_modules = set(skip_fd.read().splitlines())

    modules = sorted(set(m for i in targets.include_external for m in i.modules) -
                     set(m for i in targets.exclude_external for m in i.modules) -
                     skip_modules)

    if not modules:
        display.info('No tests applicable.', verbosity=1)
        return

    env = ansible_environment(args)
    cmd = ['ansible-doc'] + modules

    stdout, stderr = intercept_command(args, cmd, env=env, capture=True, python_version=python_version)

    if stderr:
        display.error('Output on stderr from ansible-doc is considered an error.')
        raise SubprocessError(cmd, stderr=stderr)

    if stdout:
        display.info(stdout.strip(), verbosity=3)


def intercept_command(args, cmd, capture=False, env=None, data=None, cwd=None, python_version=None):
    """
    :type args: TestConfig
    :type cmd: collections.Iterable[str]
    :type capture: bool
    :type env: dict[str, str] | None
    :type data: str | None
    :type cwd: str | None
    :type python_version: str | None
    :rtype: str | None, str | None
    """
    if not env:
        env = common_environment()

    cmd = list(cmd)
    escaped_cmd = ' '.join(pipes.quote(c) for c in cmd)
    inject_path = get_coverage_path(args)

    env['PATH'] = inject_path + os.pathsep + env['PATH']
    env['ANSIBLE_TEST_COVERAGE'] = 'coverage' if args.coverage else 'version'
    env['ANSIBLE_TEST_PYTHON_VERSION'] = python_version or args.python_version
    env['ANSIBLE_TEST_CMD'] = escaped_cmd

    return run_command(args, cmd, capture=capture, env=env, data=data, cwd=cwd)


def get_coverage_path(args):
    """
    :type args: TestConfig
    :rtype: str
    """
    global coverage_path  # pylint: disable=locally-disabled, global-statement, invalid-name

    if coverage_path:
        return os.path.join(coverage_path, 'coverage')

    prefix = 'ansible-test-coverage-'
    tmp_dir = '/tmp'

    if args.explain:
        return os.path.join(tmp_dir, '%stmp' % prefix, 'coverage')

    src = os.path.abspath(os.path.join(os.getcwd(), 'test/runner/injector/'))

    coverage_path = tempfile.mkdtemp('', prefix, dir=tmp_dir)
    os.chmod(coverage_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    shutil.copytree(src, os.path.join(coverage_path, 'coverage'))
    shutil.copy('.coveragerc', os.path.join(coverage_path, 'coverage', '.coveragerc'))

    for directory in 'output', 'logs':
        os.mkdir(os.path.join(coverage_path, directory))
        os.chmod(os.path.join(coverage_path, directory), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    atexit.register(cleanup_coverage_dir)

    return os.path.join(coverage_path, 'coverage')


def cleanup_coverage_dir():
    """Copy over coverage data from temporary directory and purge temporary directory."""
    output_dir = os.path.join(coverage_path, 'output')

    for filename in os.listdir(output_dir):
        src = os.path.join(output_dir, filename)
        dst = os.path.join(os.getcwd(), 'test', 'results', 'coverage')
        shutil.copy(src, dst)

    logs_dir = os.path.join(coverage_path, 'logs')

    for filename in os.listdir(logs_dir):
        random_suffix = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        new_name = '%s.%s.log' % (os.path.splitext(os.path.basename(filename))[0], random_suffix)
        src = os.path.join(logs_dir, filename)
        dst = os.path.join(os.getcwd(), 'test', 'results', 'logs', new_name)
        shutil.copy(src, dst)

    shutil.rmtree(coverage_path)


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

    commands = categorize_changes(paths, args.command)

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
    if is_shippable():
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

    display.info('Detected changes in %d file(s).' % len(paths))

    for path in paths:
        display.info(path, verbosity=1)

    return paths


def detect_changes_shippable(args):
    """Initialize change detection on Shippable.
    :type args: CommonConfig
    :rtype: list[str]
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

    return sorted(names)


def docker_qualify_image(name):
    """
    :type name: str
    :rtype: str
    """
    if not name or any((c in name) for c in ('/', ':')):
        return name

    return 'ansible/ansible:%s' % name


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

    if args.docker.endswith('py3'):
        skip = 'skip/python3/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which are not yet supported on python 3: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

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
        display.warning('Excluding tests marked "%s" which are not yet supported on %s: %s'
                        % (skip.rstrip('/'), platform, ', '.join(skipped)))

    return exclude


class NoChangesDetected(ApplicationWarning):
    """Exception when change detection was performed, but no changes were found."""
    def __init__(self):
        super(NoChangesDetected, self).__init__('No changes detected.')


class NoTestsForChanges(ApplicationWarning):
    """Exception when changes detected, but no tests trigger as a result."""
    def __init__(self):
        super(NoTestsForChanges, self).__init__('No tests found for detected changes.')


class SanityTargets(object):
    """Sanity test target information."""
    def __init__(self, include, exclude, require):
        """
        :type include: list[str]
        :type exclude: list[str]
        :type require: list[str]
        """
        self.all = not include
        self.targets = tuple(sorted(walk_sanity_targets()))
        self.include = walk_internal_targets(self.targets, include, exclude, require)
        self.include_external, self.exclude_external = walk_external_targets(self.targets, include, exclude, require)


class SanityTest(object):
    """Sanity test base class."""
    def __init__(self, name):
        self.name = name


class SanityFunc(SanityTest):
    """Sanity test function information."""
    def __init__(self, name, func, intercept=True):
        """
        :type name: str
        :type func: (SanityConfig, SanityTargets) -> None
        :type intercept: bool
        """
        super(SanityFunc, self).__init__(name)

        self.func = func
        self.intercept = intercept


class EnvironmentConfig(CommonConfig):
    """Configuration common to all commands which execute in an environment."""
    def __init__(self, args, command):
        """
        :type args: any
        """
        super(EnvironmentConfig, self).__init__(args)

        self.command = command

        self.local = args.local is True

        if args.tox is True or args.tox is False or args.tox is None:
            self.tox = args.tox is True
            self.tox_args = 0
            self.python = args.python if 'python' in args else None  # type: str
        else:
            self.tox = True
            self.tox_args = 1
            self.python = args.tox  # type: str

        self.docker = docker_qualify_image(args.docker)  # type: str
        self.remote = args.remote  # type: str

        self.docker_privileged = args.docker_privileged if 'docker_privileged' in args else False  # type: bool
        self.docker_util = docker_qualify_image(args.docker_util if 'docker_util' in args else '')  # type: str
        self.docker_pull = args.docker_pull if 'docker_pull' in args else False  # type: bool

        self.tox_sitepackages = args.tox_sitepackages  # type: bool

        self.remote_stage = args.remote_stage  # type: str

        self.requirements = args.requirements  # type: bool

        self.python_version = self.python or '.'.join(str(i) for i in sys.version_info[:2])

        self.delegate = self.tox or self.docker or self.remote

        if self.delegate:
            self.requirements = True


class TestConfig(EnvironmentConfig):
    """Configuration common to all test commands."""
    def __init__(self, args, command):
        """
        :type args: any
        :type command: str
        """
        super(TestConfig, self).__init__(args, command)

        self.coverage = args.coverage  # type: bool
        self.include = args.include  # type: list [str]
        self.exclude = args.exclude  # type: list [str]
        self.require = args.require  # type: list [str]

        self.changed = args.changed  # type: bool
        self.tracked = args.tracked  # type: bool
        self.untracked = args.untracked  # type: bool
        self.committed = args.committed  # type: bool
        self.staged = args.staged  # type: bool
        self.unstaged = args.unstaged  # type: bool
        self.changed_from = args.changed_from  # type: str
        self.changed_path = args.changed_path  # type: list [str]


class ShellConfig(EnvironmentConfig):
    """Configuration for the shell command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(ShellConfig, self).__init__(args, 'shell')


class SanityConfig(TestConfig):
    """Configuration for the sanity command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(SanityConfig, self).__init__(args, 'sanity')

        self.test = args.test  # type: list [str]
        self.skip_test = args.skip_test  # type: list [str]
        self.list_tests = args.list_tests  # type: bool


class IntegrationConfig(TestConfig):
    """Configuration for the integration command."""
    def __init__(self, args, command):
        """
        :type args: any
        :type command: str
        """
        super(IntegrationConfig, self).__init__(args, command)

        self.start_at = args.start_at  # type: str
        self.start_at_task = args.start_at_task  # type: str
        self.allow_destructive = args.allow_destructive if 'allow_destructive' in args else False  # type: bool
        self.retry_on_error = args.retry_on_error  # type: bool


class PosixIntegrationConfig(IntegrationConfig):
    """Configuration for the posix integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(PosixIntegrationConfig, self).__init__(args, 'integration')


class WindowsIntegrationConfig(IntegrationConfig):
    """Configuration for the windows integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(WindowsIntegrationConfig, self).__init__(args, 'windows-integration')

        self.windows = args.windows  # type: list [str]


class NetworkIntegrationConfig(IntegrationConfig):
    """Configuration for the network integration command."""

    def __init__(self, args):
        """
        :type args: any
        """
        super(NetworkIntegrationConfig, self).__init__(args, 'network-integration')

        self.platform = args.platform  # type list [str]


class UnitsConfig(TestConfig):
    """Configuration for the units command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(UnitsConfig, self).__init__(args, 'units')

        self.collect_only = args.collect_only  # type: bool


class CompileConfig(TestConfig):
    """Configuration for the compile command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CompileConfig, self).__init__(args, 'compile')


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


SANITY_TESTS = (
    # tests which ignore include/exclude (they're so fast it doesn't matter)
    SanityFunc('code-smell', command_sanity_code_smell, intercept=False),
    # tests which honor include/exclude
    SanityFunc('shellcheck', command_sanity_shellcheck, intercept=False),
    SanityFunc('yamllint', command_sanity_yamllint, intercept=False),
    SanityFunc('validate-modules', command_sanity_validate_modules, intercept=False),
    SanityFunc('ansible-doc', command_sanity_ansible_doc),
)
