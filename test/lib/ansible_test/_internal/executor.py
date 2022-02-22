"""Execute Ansible tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import json
import os
import datetime
import re
import time
import textwrap
import functools
import difflib
import filecmp
import random
import string
import shutil

from . import types as t

from .thread import (
    WrappedThread,
)

from .core_ci import (
    AnsibleCoreCI,
    SshKey,
)

from .manage_ci import (
    ManageWindowsCI,
    ManageNetworkCI,
    get_network_settings,
)

from .cloud import (
    cloud_filter,
    cloud_init,
    get_cloud_environment,
    get_cloud_platforms,
    CloudEnvironmentConfig,
)

from .io import (
    make_dirs,
    open_text_file,
    read_text_file,
    write_text_file,
)

from .util import (
    ApplicationWarning,
    ApplicationError,
    SubprocessError,
    display,
    remove_tree,
    find_executable,
    raw_command,
    get_available_port,
    generate_pip_command,
    find_python,
    cmd_quote,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_TEST_CONFIG_ROOT,
    get_ansible_version,
    tempdir,
    open_zipfile,
    SUPPORTED_PYTHON_VERSIONS,
    str_to_version,
    version_to_str,
    get_hash,
)

from .util_common import (
    get_docker_completion,
    get_remote_completion,
    get_python_path,
    intercept_command,
    named_temporary_file,
    run_command,
    write_json_test_results,
    ResultType,
    handle_layout_messages,
    CommonConfig,
)

from .docker_util import (
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

from .ansible_util import (
    ansible_environment,
    check_pyyaml,
)

from .target import (
    IntegrationTarget,
    walk_internal_targets,
    walk_posix_integration_targets,
    walk_network_integration_targets,
    walk_windows_integration_targets,
    TIntegrationTarget,
)

from .ci import (
    get_ci_provider,
)

from .classification import (
    categorize_changes,
)

from .config import (
    TestConfig,
    EnvironmentConfig,
    IntegrationConfig,
    NetworkIntegrationConfig,
    PosixIntegrationConfig,
    ShellConfig,
    WindowsIntegrationConfig,
    TIntegrationConfig,
    UnitsConfig,
    SanityConfig,
)

from .metadata import (
    ChangeDescription,
)

from .integration import (
    integration_test_environment,
    integration_test_config_file,
    setup_common_temp_dir,
    get_inventory_relative_path,
    check_inventory,
    delegate_inventory,
    IntegrationEnvironment,
)

from .data import (
    data_context,
)

from .http import (
    urlparse,
)

HTTPTESTER_HOSTS = (
    'ansible.http.tests',
    'sni1.ansible.http.tests',
    'fail.ansible.http.tests',
    'self-signed.ansible.http.tests',
)


def check_startup():
    """Checks to perform at startup before running commands."""
    check_legacy_modules()


def check_legacy_modules():
    """Detect conflicts with legacy core/extras module directories to avoid problems later."""
    for directory in 'core', 'extras':
        path = 'lib/ansible/modules/%s' % directory

        for root, _dir_names, file_names in os.walk(path):
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


def get_openssl_version(args, python, python_version):  # type: (EnvironmentConfig, str, str) -> t.Optional[t.Tuple[int, ...]]
    """Return the openssl version."""
    if not python_version.startswith('2.'):
        # OpenSSL version checking only works on Python 3.x.
        # This should be the most accurate, since it is the Python we will be using.
        version = json.loads(run_command(args, [python, os.path.join(ANSIBLE_TEST_DATA_ROOT, 'sslcheck.py')], capture=True, always=True)[0])['version']

        if version:
            display.info('Detected OpenSSL version %s under Python %s.' % (version_to_str(version), python_version), verbosity=1)

            return tuple(version)

    # Fall back to detecting the OpenSSL version from the CLI.
    # This should provide an adequate solution on Python 2.x.
    openssl_path = find_executable('openssl', required=False)

    if openssl_path:
        try:
            result = raw_command([openssl_path, 'version'], capture=True)[0]
        except SubprocessError:
            result = ''

        match = re.search(r'^OpenSSL (?P<version>[0-9]+\.[0-9]+\.[0-9]+)', result)

        if match:
            version = str_to_version(match.group('version'))

            display.info('Detected OpenSSL version %s using the openssl CLI.' % version_to_str(version), verbosity=1)

            return version

    display.info('Unable to detect OpenSSL version.', verbosity=1)

    return None


def get_setuptools_version(args, python):  # type: (EnvironmentConfig, str) -> t.Tuple[int]
    """Return the setuptools version for the given python."""
    try:
        return str_to_version(raw_command([python, '-c', 'import setuptools; print(setuptools.__version__)'], capture=True)[0])
    except SubprocessError:
        if args.explain:
            return tuple()  # ignore errors in explain mode in case setuptools is not aleady installed

        raise


def is_cryptography_available(python):  # type: (str) -> bool
    """Return True if cryptography is available for the given python."""
    try:
        raw_command([python, '-c', 'import cryptography'], capture=True)
    except SubprocessError:
        return False

    return True


def install_cryptography(args, python, python_version, pip):  # type: (EnvironmentConfig, str, str, t.List[str]) -> None
    """
    Install cryptography for the specified environment.
    """
    # make sure ansible-test's basic requirements are met before continuing
    # this is primarily to ensure that pip is new enough to facilitate further requirements installation
    install_ansible_test_requirements(args, pip)

    # make sure setuptools is available before trying to install cryptography
    # the installed version of setuptools affects the version of cryptography to install
    run_command(args, generate_pip_install(pip, '', packages=['setuptools']))

    # skip cryptography installation if it's already available
    # this avoids installing pyopenssl when cryptography is already present
    if is_cryptography_available(python):
        return

    # install the latest cryptography version that the current requirements can support
    # use a custom constraints file to avoid the normal constraints file overriding the chosen version of cryptography
    # if not installed here later install commands may try to install an unsupported version due to the presence of older setuptools
    # this is done instead of upgrading setuptools to allow tests to function with older distribution provided versions of setuptools
    run_command(args, generate_pip_install(pip, '',
                                           packages=get_cryptography_requirements(args, python, python_version),
                                           constraints=os.path.join(ANSIBLE_TEST_DATA_ROOT, 'cryptography-constraints.txt')))


def get_cryptography_requirements(args, python, python_version):  # type: (EnvironmentConfig, str, str) -> t.List[str]
    """
    Return the correct cryptography requirement for the given python version.
    The version of cryptography installed depends on the python version, setuptools version and openssl version.
    """
    setuptools_version = get_setuptools_version(args, python)
    openssl_version = get_openssl_version(args, python, python_version)

    if setuptools_version >= (18, 5):
        if python_version == '2.6':
            # cryptography 2.2+ requires python 2.7+
            # see https://github.com/pyca/cryptography/blob/master/CHANGELOG.rst#22---2018-03-19
            cryptography = 'cryptography < 2.2'
            # pyopenssl 18.0.0 requires cryptography 2.2.1 or later
            pyopenssl = 'pyopenssl < 18.0.0'
        elif openssl_version and openssl_version < (1, 1, 0):
            # cryptography 3.2 requires openssl 1.1.x or later
            # see https://cryptography.io/en/latest/changelog.html#v3-2
            cryptography = 'cryptography < 3.2'
            # pyopenssl 20.0.0 requires cryptography 3.2 or later
            pyopenssl = 'pyopenssl < 20.0.0'
        else:
            # cryptography 3.4+ fails to install on many systems
            # this is a temporary work-around until a more permanent solution is available
            cryptography = 'cryptography < 3.4'
            # pyopenssl 20.0.0 requires cryptography 35 or later
            pyopenssl = 'pyopenssl < 22.0.0'
    else:
        # cryptography 2.1+ requires setuptools 18.5+
        # see https://github.com/pyca/cryptography/blob/62287ae18383447585606b9d0765c0f1b8a9777c/setup.py#L26
        cryptography = 'cryptography < 2.1'
        # pyopenssl 17.5.0 requires cryptography 2.1.4 or later
        pyopenssl = 'pyopenssl < 17.5.0'

    requirements = [cryptography, pyopenssl]

    if args.command == 'sanity':
        requirements.remove(pyopenssl)  # sanity tests do not use pyopenssl

    return requirements


def install_command_requirements(args, python_version=None, context=None, enable_pyyaml_check=False):
    """
    :type args: EnvironmentConfig
    :type python_version: str | None
    :type context: str | None
    :type enable_pyyaml_check: bool
    """
    if not args.explain:
        make_dirs(ResultType.COVERAGE.path)
        make_dirs(ResultType.DATA.path)

    if isinstance(args, ShellConfig):
        if args.raw:
            return

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

    python = find_python(python_version)
    pip = generate_pip_command(python)

    # skip packages which have aleady been installed for python_version

    try:
        package_cache = install_command_requirements.package_cache
    except AttributeError:
        package_cache = install_command_requirements.package_cache = {}

    installed_packages = package_cache.setdefault(python_version, set())
    skip_packages = [package for package in packages if package in installed_packages]

    for package in skip_packages:
        packages.remove(package)

    installed_packages.update(packages)

    if args.command != 'sanity':
        install_cryptography(args, python, python_version, pip)

    commands = [generate_pip_install(pip, args.command, packages=packages, context=context)]

    if isinstance(args, IntegrationConfig):
        for cloud_platform in get_cloud_platforms(args):
            commands.append(generate_pip_install(pip, '%s.cloud.%s' % (args.command, cloud_platform)))

    commands = [cmd for cmd in commands if cmd]

    if not commands:
        return  # no need to detect changes or run pip check since we are not making any changes

    # only look for changes when more than one requirements file is needed
    detect_pip_changes = len(commands) > 1

    # first pass to install requirements, changes expected unless environment is already set up
    install_ansible_test_requirements(args, pip)
    changes = run_pip_commands(args, pip, commands, detect_pip_changes)

    if changes:
        # second pass to check for conflicts in requirements, changes are not expected here
        changes = run_pip_commands(args, pip, commands, detect_pip_changes)

        if changes:
            raise ApplicationError('Conflicts detected in requirements. The following commands reported changes during verification:\n%s' %
                                   '\n'.join((' '.join(cmd_quote(c) for c in cmd) for cmd in changes)))

    if args.pip_check:
        # ask pip to check for conflicts between installed packages
        try:
            run_command(args, pip + ['check', '--disable-pip-version-check'], capture=True)
        except SubprocessError as ex:
            if ex.stderr.strip() == 'ERROR: unknown command "check"':
                display.warning('Cannot check pip requirements for conflicts because "pip check" is not supported.')
            else:
                raise

    if enable_pyyaml_check:
        # pyyaml may have been one of the requirements that was installed, so perform an optional check for it
        check_pyyaml(args, python_version, required=False)


def install_ansible_test_requirements(args, pip):  # type: (EnvironmentConfig, t.List[str]) -> None
    """Install requirements for ansible-test for the given pip if not already installed."""
    try:
        installed = install_command_requirements.installed
    except AttributeError:
        installed = install_command_requirements.installed = set()

    if tuple(pip) in installed:
        return

    # make sure basic ansible-test requirements are met, including making sure that pip is recent enough to support constraints
    # virtualenvs created by older distributions may include very old pip versions, such as those created in the centos6 test container (pip 6.0.8)
    run_command(args, generate_pip_install(pip, 'ansible-test', use_constraints=False))

    installed.add(tuple(pip))


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
    stdout = run_command(args, pip + ['list'], capture=True)[0]
    return stdout


def generate_pip_install(pip, command, packages=None, constraints=None, use_constraints=True, context=None):
    """
    :type pip: list[str]
    :type command: str
    :type packages: list[str] | None
    :type constraints: str | None
    :type use_constraints: bool
    :type context: str | None
    :rtype: list[str] | None
    """
    constraints = constraints or os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'constraints.txt')
    requirements = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', '%s.txt' % ('%s.%s' % (command, context) if context else command))
    content_constraints = None

    options = []

    if os.path.exists(requirements) and os.path.getsize(requirements):
        options += ['-r', requirements]

    if command == 'sanity' and data_context().content.is_ansible:
        requirements = os.path.join(data_context().content.sanity_path, 'code-smell', '%s.requirements.txt' % context)

        if os.path.exists(requirements) and os.path.getsize(requirements):
            options += ['-r', requirements]

    if command == 'units':
        requirements = os.path.join(data_context().content.unit_path, 'requirements.txt')

        if os.path.exists(requirements) and os.path.getsize(requirements):
            options += ['-r', requirements]

        content_constraints = os.path.join(data_context().content.unit_path, 'constraints.txt')

    if command in ('integration', 'windows-integration', 'network-integration'):
        requirements = os.path.join(data_context().content.integration_path, 'requirements.txt')

        if os.path.exists(requirements) and os.path.getsize(requirements):
            options += ['-r', requirements]

        requirements = os.path.join(data_context().content.integration_path, '%s.requirements.txt' % command)

        if os.path.exists(requirements) and os.path.getsize(requirements):
            options += ['-r', requirements]

        content_constraints = os.path.join(data_context().content.integration_path, 'constraints.txt')

    if command.startswith('integration.cloud.'):
        content_constraints = os.path.join(data_context().content.integration_path, 'constraints.txt')

    if packages:
        options += packages

    if not options:
        return None

    if use_constraints:
        if content_constraints and os.path.exists(content_constraints) and os.path.getsize(content_constraints):
            # listing content constraints first gives them priority over constraints provided by ansible-test
            options.extend(['-c', content_constraints])

        options.extend(['-c', constraints])

    return pip + ['install', '--disable-pip-version-check'] + options


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
    handle_layout_messages(data_context().content.integration_messages)

    inventory_relative_path = get_inventory_relative_path(args)
    inventory_path = os.path.join(ANSIBLE_TEST_DATA_ROOT, os.path.basename(inventory_relative_path))

    all_targets = tuple(walk_posix_integration_targets(include_hidden=True))
    internal_targets = command_integration_filter(args, all_targets)
    command_integration_filtered(args, internal_targets, all_targets, inventory_path)


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
    pre_target = None
    post_target = None
    httptester_id = None

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

        use_httptester = args.httptester and any('needs/httptester/' in target.aliases for target in internal_targets)
        # if running under Docker delegation, the httptester may have already been started
        docker_httptester = bool(os.environ.get("HTTPTESTER", False))

        if use_httptester and not docker_available() and not docker_httptester:
            display.warning('Assuming --disable-httptester since `docker` is not available.')
        elif use_httptester:
            if docker_httptester:
                # we are running in a Docker container that is linked to the httptester container, we just need to
                # forward these requests to the linked hostname
                first_host = HTTPTESTER_HOSTS[0]
                ssh_options = [
                    "-R", "8080:%s:80" % first_host,
                    "-R", "8443:%s:443" % first_host,
                    "-R", "8444:%s:444" % first_host
                ]
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
                    manage.upload(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'setup', 'windows-httptester.ps1'), watcher_path)

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

    def run_playbook(playbook, run_playbook_vars):  # type: (str, t.Dict[str, t.Any]) -> None
        playbook_path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'playbooks', playbook)
        command = ['ansible-playbook', '-i', inventory_path, playbook_path, '-e', json.dumps(run_playbook_vars)]
        if args.verbosity:
            command.append('-%s' % ('v' * args.verbosity))

        env = ansible_environment(args)
        intercept_command(args, command, '', env, disable_coverage=True)

    remote_temp_path = None

    if args.coverage and not args.coverage_check:
        # Create the remote directory that is writable by everyone. Use Ansible to talk to the remote host.
        remote_temp_path = 'C:\\ansible_test_coverage_%s' % time.time()
        playbook_vars = {'remote_temp_path': remote_temp_path}
        run_playbook('windows_coverage_setup.yml', playbook_vars)

    success = False

    try:
        command_integration_filtered(args, internal_targets, all_targets, inventory_path, pre_target=pre_target,
                                     post_target=post_target, remote_temp_path=remote_temp_path)
        success = True
    finally:
        if httptester_id:
            docker_rm(args, httptester_id)

        if remote_temp_path:
            # Zip up the coverage files that were generated and fetch it back to localhost.
            with tempdir() as local_temp_path:
                playbook_vars = {'remote_temp_path': remote_temp_path, 'local_temp_path': local_temp_path}
                run_playbook('windows_coverage_teardown.yml', playbook_vars)

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

        if remote.name == 'windows-2008':
            options.update(
                # force 2008 to use PSRP for the connection plugin
                ansible_connection='psrp',
                ansible_psrp_auth='basic',
                ansible_psrp_cert_validation='ignore',
            )
        elif remote.name == 'windows-2016':
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


def command_integration_filter(args,  # type: TIntegrationConfig
                               targets,  # type: t.Iterable[TIntegrationTarget]
                               init_callback=None,  # type: t.Callable[[TIntegrationConfig, t.Tuple[TIntegrationTarget, ...]], None]
                               ):  # type: (...) -> t.Tuple[TIntegrationTarget, ...]
    """Filter the given integration test targets."""
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

    if args.start_at and not any(target.name == args.start_at for target in internal_targets):
        raise ApplicationError('Start at target matches nothing: %s' % args.start_at)

    if init_callback:
        init_callback(args, internal_targets)

    cloud_init(args, internal_targets)

    vars_file_src = os.path.join(data_context().content.root, data_context().content.integration_vars_path)

    if os.path.exists(vars_file_src):
        def integration_config_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """
            Add the integration config vars file to the payload file list.
            This will preserve the file during delegation even if the file is ignored by source control.
            """
            files.append((vars_file_src, data_context().content.integration_vars_path))

        data_context().register_payload_callback(integration_config_callback)

    if args.delegate:
        raise Delegate(require=require, exclude=exclude, integration_targets=internal_targets)

    install_command_requirements(args)

    return internal_targets


def command_integration_filtered(args, targets, all_targets, inventory_path, pre_target=None, post_target=None,
                                 remote_temp_path=None):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :type all_targets: tuple[IntegrationTarget]
    :type inventory_path: str
    :type pre_target: (IntegrationTarget) -> None | None
    :type post_target: (IntegrationTarget) -> None | None
    :type remote_temp_path: str | None
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

    check_pyyaml(args, args.python_version)

    test_dir = os.path.join(ResultType.TMP.path, 'output_dir')

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

    current_environment = None  # type: t.Optional[EnvironmentDescription]

    # common temporary directory path that will be valid on both the controller and the remote
    # it must be common because it will be referenced in environment variables that are shared across multiple hosts
    common_temp_path = '/tmp/ansible-test-%s' % ''.join(random.choice(string.ascii_letters + string.digits) for _idx in range(8))

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
                                command_integration_script(args, target, test_dir, inventory_path, common_temp_path,
                                                           remote_temp_path=remote_temp_path)
                            else:
                                command_integration_role(args, target, start_at_task, test_dir, inventory_path,
                                                         common_temp_path, remote_temp_path=remote_temp_path)
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
                coverage_temp_path = os.path.join(common_temp_path, ResultType.COVERAGE.name)
                coverage_save_path = ResultType.COVERAGE.path

                for filename in os.listdir(coverage_temp_path):
                    shutil.copy(os.path.join(coverage_temp_path, filename), os.path.join(coverage_save_path, filename))

            remove_tree(common_temp_path)

            result_name = '%s-%s.json' % (
                args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.utcnow().replace(microsecond=0))))

            data = dict(
                targets=results,
            )

            write_json_test_results(ResultType.DATA, result_name, data)

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
            remote=8088,
            container=88,
        ),
        dict(
            remote=8443,
            container=443,
        ),
        dict(
            remote=8444,
            container=444,
        ),
        dict(
            remote=8749,
            container=749,
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
        '--env', 'KRB5_PASSWORD=%s' % args.httptester_krb5_password,
    ]

    if ports:
        for localhost_port, container_port in ports.items():
            options += ['-p', '%d:%d' % (localhost_port, container_port)]

    network = get_docker_preferred_network_name(args)

    if is_docker_user_defined_network(network):
        # network-scoped aliases are only supported for containers in user defined networks
        for alias in HTTPTESTER_HOSTS:
            options.extend(['--network-alias', alias])

    httptester_id = docker_run(args, args.httptester, options=options)[0]

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
    hosts_path = '/etc/hosts'

    original_lines = read_text_file(hosts_path).splitlines(True)

    if not any(line.endswith(comment) for line in original_lines):
        write_text_file(hosts_path, ''.join(original_lines + append_lines))

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
rdr pass inet proto tcp from any to any port 88 -> 127.0.0.1 port 8088
rdr pass inet proto tcp from any to any port 443 -> 127.0.0.1 port 8443
rdr pass inet proto tcp from any to any port 444 -> 127.0.0.1 port 8444
rdr pass inet proto tcp from any to any port 749 -> 127.0.0.1 port 8749
'''
        cmd = ['pfctl', '-ef', '-']

        try:
            run_command(args, cmd, capture=True, data=rules)
        except SubprocessError:
            pass  # non-zero exit status on success

    elif iptables:
        ports = [
            (80, 8080),
            (88, 8088),
            (443, 8443),
            (444, 8444),
            (749, 8749),
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


def run_pypi_proxy(args):  # type: (EnvironmentConfig) -> t.Tuple[t.Optional[str], t.Optional[str]]
    """Run a PyPI proxy container, returning the container ID and proxy endpoint."""
    use_proxy = False

    if args.docker_raw == 'centos6':
        use_proxy = True  # python 2.6 is the only version available

    if args.docker_raw == 'default':
        if args.python == '2.6':
            use_proxy = True  # python 2.6 requested
        elif not args.python and isinstance(args, (SanityConfig, UnitsConfig, ShellConfig)):
            use_proxy = True  # multiple versions (including python 2.6) can be used

    if args.docker_raw and args.pypi_proxy:
        use_proxy = True  # manual override to force proxy usage

    if not use_proxy:
        return None, None

    proxy_image = 'quay.io/ansible/pypi-test-container:1.0.0'
    port = 3141

    options = [
        '--detach',
    ]

    docker_pull(args, proxy_image)

    container_id = docker_run(args, proxy_image, options=options)[0]

    if args.explain:
        container_id = 'pypi_id'
        container_ip = '127.0.0.1'
    else:
        container_id = container_id.strip()
        container_ip = get_docker_container_ip(args, container_id)

    endpoint = 'http://%s:%d/root/pypi/+simple/' % (container_ip, port)

    return container_id, endpoint


def configure_pypi_proxy(args):  # type: (CommonConfig) -> None
    """Configure the environment to use a PyPI proxy, if present."""
    if not isinstance(args, EnvironmentConfig):
        return

    if args.pypi_endpoint:
        configure_pypi_block_access()
        configure_pypi_proxy_pip(args)
        configure_pypi_proxy_easy_install(args)


def configure_pypi_block_access():  # type: () -> None
    """Block direct access to PyPI to ensure proxy configurations are always used."""
    if os.getuid() != 0:
        display.warning('Skipping custom hosts block for PyPI for non-root user.')
        return

    hosts_path = '/etc/hosts'
    hosts_block = '''
127.0.0.1 pypi.org pypi.python.org files.pythonhosted.org
'''

    def hosts_cleanup():
        display.info('Removing custom PyPI hosts entries: %s' % hosts_path, verbosity=1)

        with open(hosts_path) as hosts_file_read:
            content = hosts_file_read.read()

        content = content.replace(hosts_block, '')

        with open(hosts_path, 'w') as hosts_file_write:
            hosts_file_write.write(content)

    display.info('Injecting custom PyPI hosts entries: %s' % hosts_path, verbosity=1)
    display.info('Config: %s\n%s' % (hosts_path, hosts_block), verbosity=3)

    with open(hosts_path, 'a') as hosts_file:
        hosts_file.write(hosts_block)

    atexit.register(hosts_cleanup)


def configure_pypi_proxy_pip(args):  # type: (EnvironmentConfig) -> None
    """Configure a custom index for pip based installs."""
    pypi_hostname = urlparse(args.pypi_endpoint)[1].split(':')[0]

    pip_conf_path = os.path.expanduser('~/.pip/pip.conf')
    pip_conf = '''
[global]
index-url = {0}
trusted-host = {1}
'''.format(args.pypi_endpoint, pypi_hostname).strip()

    def pip_conf_cleanup():
        display.info('Removing custom PyPI config: %s' % pip_conf_path, verbosity=1)
        os.remove(pip_conf_path)

    if os.path.exists(pip_conf_path):
        raise ApplicationError('Refusing to overwrite existing file: %s' % pip_conf_path)

    display.info('Injecting custom PyPI config: %s' % pip_conf_path, verbosity=1)
    display.info('Config: %s\n%s' % (pip_conf_path, pip_conf), verbosity=3)

    write_text_file(pip_conf_path, pip_conf, True)
    atexit.register(pip_conf_cleanup)


def configure_pypi_proxy_easy_install(args):  # type: (EnvironmentConfig) -> None
    """Configure a custom index for easy_install based installs."""
    pydistutils_cfg_path = os.path.expanduser('~/.pydistutils.cfg')
    pydistutils_cfg = '''
[easy_install]
index_url = {0}
'''.format(args.pypi_endpoint).strip()

    if os.path.exists(pydistutils_cfg_path):
        raise ApplicationError('Refusing to overwrite existing file: %s' % pydistutils_cfg_path)

    def pydistutils_cfg_cleanup():
        display.info('Removing custom PyPI config: %s' % pydistutils_cfg_path, verbosity=1)
        os.remove(pydistutils_cfg_path)

    display.info('Injecting custom PyPI config: %s' % pydistutils_cfg_path, verbosity=1)
    display.info('Config: %s\n%s' % (pydistutils_cfg_path, pydistutils_cfg), verbosity=3)

    write_text_file(pydistutils_cfg_path, pydistutils_cfg, True)
    atexit.register(pydistutils_cfg_cleanup)


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


def integration_environment(args, target, test_dir, inventory_path, ansible_config, env_config, test_env):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type test_dir: str
    :type inventory_path: str
    :type ansible_config: str | None
    :type env_config: CloudEnvironmentConfig | None
    :type test_env: IntegrationEnvironment
    :rtype: dict[str, str]
    """
    env = ansible_environment(args, ansible_config=ansible_config)

    if args.inject_httptester:
        env.update(dict(
            HTTPTESTER='1',
            KRB5_PASSWORD=args.httptester_krb5_password,
        ))

    callback_plugins = ['junit'] + (env_config.callback_plugins or [] if env_config else [])

    integration = dict(
        JUNIT_OUTPUT_DIR=ResultType.JUNIT.path,
        JUNIT_TASK_RELATIVE_PATH=test_env.test_dir,
        JUNIT_REPLACE_OUT_OF_TREE_PATH='out-of-tree:',
        ANSIBLE_CALLBACKS_ENABLED=','.join(sorted(set(callback_plugins))),
        ANSIBLE_TEST_CI=args.metadata.ci_provider or get_ci_provider().code,
        ANSIBLE_TEST_COVERAGE='check' if args.coverage_check else ('yes' if args.coverage else ''),
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


def command_integration_script(args, target, test_dir, inventory_path, temp_path, remote_temp_path=None):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type test_dir: str
    :type inventory_path: str
    :type temp_path: str
    :type remote_temp_path: str | None
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

        env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config, test_env)
        cwd = os.path.join(test_env.targets_dir, target.relative_path)

        env.update(dict(
            # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
            ANSIBLE_PLAYBOOK_DIR=cwd,
        ))

        if env_config and env_config.env_vars:
            env.update(env_config.env_vars)

        with integration_test_config_file(args, env_config, test_env.integration_dir) as config_path:
            if config_path:
                cmd += ['-e', '@%s' % config_path]

            module_coverage = 'non_local/' not in target.aliases
            intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd, temp_path=temp_path,
                              remote_temp_path=remote_temp_path, module_coverage=module_coverage)


def command_integration_role(args, target, start_at_task, test_dir, inventory_path, temp_path, remote_temp_path=None):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type start_at_task: str | None
    :type test_dir: str
    :type inventory_path: str
    :type temp_path: str
    :type remote_temp_path: str | None
    """
    display.info('Running %s integration test role' % target.name)

    env_config = None

    vars_files = []
    variables = dict(
        output_dir=test_dir,
    )

    if isinstance(args, WindowsIntegrationConfig):
        hosts = 'windows'
        gather_facts = False
        variables.update(dict(
            win_output_dir=r'C:\ansible_testing',
        ))
    elif isinstance(args, NetworkIntegrationConfig):
        hosts = target.network_platform
        gather_facts = False
    else:
        hosts = 'testhost'
        gather_facts = True

        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            env_config = cloud_environment.get_environment_config()

    with integration_test_environment(args, target, inventory_path) as test_env:
        if os.path.exists(test_env.vars_file):
            vars_files.append(os.path.relpath(test_env.vars_file, test_env.integration_dir))

        play = dict(
            hosts=hosts,
            gather_facts=gather_facts,
            vars_files=vars_files,
            vars=variables,
            roles=[
                target.name,
            ],
        )

        if env_config:
            if env_config.ansible_vars:
                variables.update(env_config.ansible_vars)

            play.update(dict(
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

            env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config, test_env)
            cwd = test_env.integration_dir

            env.update(dict(
                # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
                ANSIBLE_PLAYBOOK_DIR=cwd,
            ))

            env['ANSIBLE_ROLES_PATH'] = test_env.targets_dir

            module_coverage = 'non_local/' not in target.aliases
            intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd, temp_path=temp_path,
                              remote_temp_path=remote_temp_path, module_coverage=module_coverage)


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
            paths += read_text_file(args.changed_from).splitlines()
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
    remote = args.parsed_remote

    exclude = []

    common_integration_filter(args, targets, exclude)

    skips = {
        'skip/%s' % remote.platform: remote.platform,
        'skip/%s/%s' % (remote.platform, remote.version): '%s %s' % (remote.platform, remote.version),
        'skip/%s%s' % (remote.platform, remote.version): '%s %s' % (remote.platform, remote.version),  # legacy syntax, use above format
    }

    if remote.arch:
        skips.update({
            'skip/%s/%s' % (remote.arch, remote.platform): '%s on %s' % (remote.platform, remote.arch),
            'skip/%s/%s/%s' % (remote.arch, remote.platform, remote.version): '%s %s on %s' % (remote.platform, remote.version, remote.arch),
        })

    for skip, description in skips.items():
        skipped = [target.name for target in targets if skip in target.skips]
        if skipped:
            exclude.append(skip + '/')
            display.warning('Excluding tests marked "%s" which are not supported on %s: %s' % (skip, description, ', '.join(skipped)))

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


class EnvironmentDescription:
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

        version_check = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'versions.py')
        python_paths = dict((v, find_executable('python%s' % v, required=False)) for v in sorted(versions))
        pip_paths = dict((v, find_executable('pip%s' % v, required=False)) for v in sorted(versions))
        program_versions = dict((v, self.get_version([python_paths[v], version_check], warnings)) for v in sorted(python_paths) if python_paths[v])
        pip_interpreters = dict((v, self.get_shebang(pip_paths[v])) for v in sorted(pip_paths) if pip_paths[v])
        known_hosts_hash = get_hash(os.path.expanduser('~/.ssh/known_hosts'))

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

        if not python_path or not pip_path:
            # skip checks when either python or pip are missing for this version
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
        :type warnings: list[text]
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
        with open_text_file(path) as script_fd:
            return script_fd.readline().strip()


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
