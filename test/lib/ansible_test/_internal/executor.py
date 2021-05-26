"""Execute Ansible tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import json
import os
import re

from . import types as t

from .io import (
    make_dirs,
    read_text_file,
    write_text_file,
)

from .util import (
    ApplicationWarning,
    ApplicationError,
    SubprocessError,
    display,
    find_executable,
    raw_command,
    generate_pip_command,
    find_python,
    cmd_quote,
    ANSIBLE_TEST_DATA_ROOT,
    str_to_version,
    version_to_str,
)

from .util_common import (
    intercept_command,
    run_command,
    ResultType,
    CommonConfig,
)

from .docker_util import (
    docker_pull,
    docker_run,
    docker_inspect,
)

from .ansible_util import (
    ansible_environment,
    check_pyyaml,
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
    ShellConfig,
    UnitsConfig,
    SanityConfig,
)

from .metadata import (
    ChangeDescription,
)

from .data import (
    data_context,
)

from .http import (
    urlparse,
)


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


def is_cryptography_available(python):  # type: (str) -> bool
    """Return True if cryptography is available for the given python."""
    try:
        raw_command([python, '-c', 'import cryptography'], capture=True)
    except SubprocessError:
        return False

    return True


def get_setuptools_version(args, python):  # type: (EnvironmentConfig, str) -> t.Tuple[int]
    """Return the setuptools version for the given python."""
    try:
        return str_to_version(raw_command([python, '-c', 'import setuptools; print(setuptools.__version__)'], capture=True)[0])
    except SubprocessError:
        if args.explain:
            return tuple()  # ignore errors in explain mode in case setuptools is not aleady installed

        raise


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

    # skip cryptography install if it is already available
    # this avoids downgrading cryptography when OS packages provide a newer version than we are able to install using pip
    if is_cryptography_available(python):
        return

    # install the latest cryptography version that the current requirements can support
    # use a custom constraints file to avoid the normal constraints file overriding the chosen version of cryptography
    # if not installed here later install commands may try to install an unsupported version due to the presence of older setuptools
    # this is done instead of upgrading setuptools to allow tests to function with older distribution provided versions of setuptools
    run_command(args, generate_pip_install(pip, '',
                                           packages=[get_cryptography_requirement(args, python, python_version)],
                                           constraints=os.path.join(ANSIBLE_TEST_DATA_ROOT, 'cryptography-constraints.txt')))


def get_cryptography_requirement(args, python, python_version):  # type: (EnvironmentConfig, str, str) -> str
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
        elif openssl_version and openssl_version < (1, 1, 0):
            # cryptography 3.2 requires openssl 1.1.x or later
            # see https://cryptography.io/en/latest/changelog.html#v3-2
            cryptography = 'cryptography < 3.2'
        else:
            # cryptography 3.4+ fails to install on many systems
            # this is a temporary work-around until a more permanent solution is available
            cryptography = 'cryptography < 3.4'
    else:
        # cryptography 2.1+ requires setuptools 18.5+
        # see https://github.com/pyca/cryptography/blob/62287ae18383447585606b9d0765c0f1b8a9777c/setup.py#L26
        cryptography = 'cryptography < 2.1'

    return cryptography


def install_command_requirements(args, python_version=None, context=None, enable_pyyaml_check=False, extra_requirements=None):
    """
    :type args: EnvironmentConfig
    :type python_version: str | None
    :type context: str | None
    :type enable_pyyaml_check: bool
    :type extra_requirements: list[str] | None
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

    if extra_requirements:
        for extra_requirement in extra_requirements:
            commands.append(generate_pip_install(pip, extra_requirement))

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


def parse_inventory(args, inventory_path):  # type: (IntegrationConfig, str) -> t.Dict[str, t.Any]
    """Return a dict parsed from the given inventory file."""
    cmd = ['ansible-inventory', '-i', inventory_path, '--list']
    env = ansible_environment(args)
    inventory = json.loads(intercept_command(args, cmd, '', env, capture=True, disable_coverage=True)[0])
    return inventory


def get_hosts(inventory, group_name):  # type: (t.Dict[str, t.Any], str) -> t.Dict[str, t.Dict[str, t.Any]]
    """Return a dict of hosts from the specified group in the given inventory."""
    hostvars = inventory.get('_meta', {}).get('hostvars', {})
    group = inventory.get(group_name, {})
    host_names = group.get('hosts', [])
    hosts = dict((name, hostvars[name]) for name in host_names)
    return hosts


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

    container_id = docker_run(args, proxy_image, options=options)

    container = docker_inspect(args, container_id)

    container_ip = container.get_ip_address()

    if not container_ip:
        raise Exception('PyPI container IP not available.')

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
