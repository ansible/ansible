"""Python requirements management"""
from __future__ import annotations

import json
import os
import re
import shlex
import typing as t

from .io import (
    make_dirs,
)

from .util import (
    ApplicationError,
    SubprocessError,
    display,
    find_executable,
    raw_command,
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_TEST_TOOLS_ROOT,
    str_to_version,
    version_to_str,
)

from .util_common import (
    run_command,
    ResultType,
    check_pyyaml,
)

from .config import (
    TestConfig,
    EnvironmentConfig,
)

from .data import (
    data_context,
)

from .host_configs import (
    PythonConfig,
)


def generate_pip_command(python):
    """
    :type python: str
    :rtype: list[str]
    """
    return [python, os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'quiet_pip.py')]


def get_openssl_version(args, python):  # type: (EnvironmentConfig, PythonConfig) -> t.Optional[t.Tuple[int, ...]]
    """Return the openssl version."""
    if not python.version.startswith('2.'):
        # OpenSSL version checking only works on Python 3.x.
        # This should be the most accurate, since it is the Python we will be using.
        version = json.loads(run_command(args, [python.path, os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'sslcheck.py')], capture=True, always=True)[0])['version']

        if version:
            display.info('Detected OpenSSL version %s under Python %s.' % (version_to_str(version), python.version), verbosity=1)

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


def install_cryptography(args, python, pip):  # type: (EnvironmentConfig, PythonConfig, t.List[str]) -> None
    """
    Install cryptography for the specified environment.
    """
    # skip cryptography install if it is already available
    # this avoids downgrading cryptography when OS packages provide a newer version than we are able to install using pip
    if is_cryptography_available(python.path):
        return

    # install the latest cryptography version that the current requirements can support
    # use a custom constraints file to avoid the normal constraints file overriding the chosen version of cryptography
    # if not installed here later install commands may try to install a version of cryptography which cannot be installed
    run_command(args, generate_pip_install(pip, '',
                                           packages=get_cryptography_requirements(args, python),
                                           constraints=os.path.join(ANSIBLE_TEST_DATA_ROOT, 'cryptography-constraints.txt')),
                capture=True)


def get_cryptography_requirements(args, python):  # type: (EnvironmentConfig, PythonConfig) -> t.List[str]
    """
    Return the correct cryptography and pyopenssl requirements for the given python version.
    The version of cryptography installed depends on the python version and openssl version.
    """
    openssl_version = get_openssl_version(args, python)

    if openssl_version and openssl_version < (1, 1, 0):
        # cryptography 3.2 requires openssl 1.1.x or later
        # see https://cryptography.io/en/latest/changelog.html#v3-2
        cryptography = 'cryptography < 3.2'
        # pyopenssl 20.0.0 requires cryptography 3.2 or later
        pyopenssl = 'pyopenssl < 20.0.0'
    else:
        # cryptography 3.4+ fails to install on many systems
        # this is a temporary work-around until a more permanent solution is available
        cryptography = 'cryptography < 3.4'
        # no specific version of pyopenssl required, don't install it
        pyopenssl = None

    requirements = [
        cryptography,
        pyopenssl,
    ]

    requirements = [requirement for requirement in requirements if requirement]

    return requirements


def create_required_directories(args):  # type: (EnvironmentConfig) -> None
    """Create required directories."""
    if args.explain:
        return

    make_dirs(ResultType.COVERAGE.path)
    make_dirs(ResultType.DATA.path)


def install_command_requirements(args, python, context=None, enable_pyyaml_check=False, extra_requirements=None, skip_coverage=False):
    """
    :type args: EnvironmentConfig
    :type python: PythonConfig
    :type context: str | None
    :type enable_pyyaml_check: bool
    :type extra_requirements: list[str] | None
    :type skip_coverage: bool
    """
    create_required_directories(args)

    if not args.requirements:
        return

    packages = []

    if isinstance(args, TestConfig):
        if args.coverage and not skip_coverage:
            packages.append('coverage')

    pip = generate_pip_command(python.path)

    # skip packages which have aleady been installed for this python

    try:
        package_cache = install_command_requirements.package_cache
    except AttributeError:
        package_cache = install_command_requirements.package_cache = {}

    installed_packages = package_cache.setdefault(python.path, set())
    skip_packages = [package for package in packages if package in installed_packages]

    for package in skip_packages:
        packages.remove(package)

    installed_packages.update(packages)

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
    changes = run_pip_commands(args, pip, commands, detect_pip_changes)

    if changes:
        # second pass to check for conflicts in requirements, changes are not expected here
        changes = run_pip_commands(args, pip, commands, detect_pip_changes)

        if changes:
            raise ApplicationError('Conflicts detected in requirements. The following commands reported changes during verification:\n%s' %
                                   '\n'.join((' '.join(shlex.quote(c) for c in cmd) for cmd in changes)))

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
        check_pyyaml(args, python, required=False)


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


def install_controller_requirements(args, python):  # type: (EnvironmentConfig, PythonConfig) -> None
    """Install the Ansible controller requirements if not already installed."""
    try:
        cache = install_controller_requirements.cache
    except AttributeError:
        cache = install_controller_requirements.cache = {}

    installed = cache.get(python.path)

    if installed:
        return

    pip = generate_pip_command(python.path)
    install_cryptography(args, python, pip)
    run_command(args, generate_pip_install(pip, '', controller=True), capture=True)
    check_pyyaml(args, python)

    cache[python.path] = True


def generate_pip_install(pip, command, packages=None, constraints=None, use_constraints=True, context=None, controller=False):
    """
    :type pip: list[str]
    :type command: str
    :type packages: list[str] | None
    :type constraints: str | None
    :type use_constraints: bool
    :type context: str | None
    :type controller: bool
    :rtype: list[str] | None
    """
    constraints = constraints or os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'constraints.txt')
    requirements = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', '%s.txt' % ('%s.%s' % (command, context) if context else command))
    content_constraints = None

    options = []

    if os.path.exists(requirements) and os.path.getsize(requirements):
        options += ['-r', requirements]

    if controller:
        requirements = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'controller.txt')

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
