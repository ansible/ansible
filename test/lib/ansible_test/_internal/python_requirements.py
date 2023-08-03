"""Python requirements management"""
from __future__ import annotations

import base64
import dataclasses
import json
import os
import re
import typing as t

from .encoding import (
    to_text,
    to_bytes,
)

from .io import (
    read_text_file,
)

from .util import (
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_TEST_TARGET_ROOT,
    ANSIBLE_TEST_TOOLS_ROOT,
    ApplicationError,
    SubprocessError,
    display,
    find_executable,
    raw_command,
    str_to_version,
    version_to_str,
)

from .util_common import (
    check_pyyaml,
    create_result_directories,
)

from .config import (
    EnvironmentConfig,
    IntegrationConfig,
    UnitsConfig,
)

from .data import (
    data_context,
)

from .host_configs import (
    PosixConfig,
    PythonConfig,
    VirtualPythonConfig,
)

from .connections import (
    LocalConnection,
    Connection,
)

from .coverage_util import (
    get_coverage_version,
)

QUIET_PIP_SCRIPT_PATH = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'quiet_pip.py')
REQUIREMENTS_SCRIPT_PATH = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'requirements.py')

# IMPORTANT: Keep this in sync with the ansible-test.txt requirements file.
VIRTUALENV_VERSION = '16.7.12'

# Pip Abstraction


class PipUnavailableError(ApplicationError):
    """Exception raised when pip is not available."""

    def __init__(self, python: PythonConfig) -> None:
        super().__init__(f'Python {python.version} at "{python.path}" does not have pip available.')


@dataclasses.dataclass(frozen=True)
class PipCommand:
    """Base class for pip commands."""

    def serialize(self) -> tuple[str, dict[str, t.Any]]:
        """Return a serialized representation of this command."""
        name = type(self).__name__[3:].lower()
        return name, self.__dict__


@dataclasses.dataclass(frozen=True)
class PipInstall(PipCommand):
    """Details required to perform a pip install."""

    requirements: list[tuple[str, str]]
    constraints: list[tuple[str, str]]
    packages: list[str]

    def has_package(self, name: str) -> bool:
        """Return True if the specified package will be installed, otherwise False."""
        name = name.lower()

        return (any(name in package.lower() for package in self.packages) or
                any(name in contents.lower() for path, contents in self.requirements))


@dataclasses.dataclass(frozen=True)
class PipUninstall(PipCommand):
    """Details required to perform a pip uninstall."""

    packages: list[str]
    ignore_errors: bool


@dataclasses.dataclass(frozen=True)
class PipVersion(PipCommand):
    """Details required to get the pip version."""


@dataclasses.dataclass(frozen=True)
class PipBootstrap(PipCommand):
    """Details required to bootstrap pip."""

    pip_version: str
    packages: list[str]


# Entry Points


def install_requirements(
    args: EnvironmentConfig,
    python: PythonConfig,
    ansible: bool = False,
    command: bool = False,
    coverage: bool = False,
    virtualenv: bool = False,
    controller: bool = True,
    connection: t.Optional[Connection] = None,
) -> None:
    """Install requirements for the given Python using the specified arguments."""
    create_result_directories(args)

    if not requirements_allowed(args, controller):
        return

    if command and isinstance(args, (UnitsConfig, IntegrationConfig)) and args.coverage:
        coverage = True

    cryptography = False

    if ansible:
        try:
            ansible_cache = install_requirements.ansible_cache  # type: ignore[attr-defined]
        except AttributeError:
            ansible_cache = install_requirements.ansible_cache = {}  # type: ignore[attr-defined]

        ansible_installed = ansible_cache.get(python.path)

        if ansible_installed:
            ansible = False
        else:
            ansible_cache[python.path] = True

            # Install the latest cryptography version that the current requirements can support if it is not already available.
            # This avoids downgrading cryptography when OS packages provide a newer version than we are able to install using pip.
            # If not installed here, later install commands may try to install a version of cryptography which cannot be installed.
            cryptography = not is_cryptography_available(python.path)

    commands = collect_requirements(
        python=python,
        controller=controller,
        ansible=ansible,
        cryptography=cryptography,
        command=args.command if command else None,
        coverage=coverage,
        virtualenv=virtualenv,
        minimize=False,
        sanity=None,
    )

    if not commands:
        return

    run_pip(args, python, commands, connection)

    # false positive: pylint: disable=no-member
    if any(isinstance(command, PipInstall) and command.has_package('pyyaml') for command in commands):
        check_pyyaml(python)


def collect_bootstrap(python: PythonConfig) -> list[PipCommand]:
    """Return the details necessary to bootstrap pip into an empty virtual environment."""
    infrastructure_packages = get_venv_packages(python)
    pip_version = infrastructure_packages['pip']
    packages = [f'{name}=={version}' for name, version in infrastructure_packages.items()]

    bootstrap = PipBootstrap(
        pip_version=pip_version,
        packages=packages,
    )

    return [bootstrap]


def collect_requirements(
    python: PythonConfig,
    controller: bool,
    ansible: bool,
    cryptography: bool,
    coverage: bool,
    virtualenv: bool,
    minimize: bool,
    command: t.Optional[str],
    sanity: t.Optional[str],
) -> list[PipCommand]:
    """Collect requirements for the given Python using the specified arguments."""
    commands: list[PipCommand] = []

    if virtualenv:
        # sanity tests on Python 2.x install virtualenv when it is too old or is not already installed and the `--requirements` option is given
        # the last version of virtualenv with no dependencies is used to minimize the changes made outside a virtual environment
        commands.extend(collect_package_install(packages=[f'virtualenv=={VIRTUALENV_VERSION}'], constraints=False))

    if coverage:
        commands.extend(collect_package_install(packages=[f'coverage=={get_coverage_version(python.version).coverage_version}'], constraints=False))

    if cryptography:
        commands.extend(collect_package_install(packages=get_cryptography_requirements(python)))

    if ansible or command:
        commands.extend(collect_general_install(command, ansible))

    if sanity:
        commands.extend(collect_sanity_install(sanity))

    if command == 'units':
        commands.extend(collect_units_install())

    if command in ('integration', 'windows-integration', 'network-integration'):
        commands.extend(collect_integration_install(command, controller))

    if (sanity or minimize) and any(isinstance(command, PipInstall) for command in commands):
        # bootstrap the managed virtual environment, which will have been created without any installed packages
        # sanity tests which install no packages skip this step
        commands = collect_bootstrap(python) + commands

        # most infrastructure packages can be removed from sanity test virtual environments after they've been created
        # removing them reduces the size of environments cached in containers
        uninstall_packages = list(get_venv_packages(python))

        if not minimize:
            # installed packages may have run-time dependencies on setuptools
            uninstall_packages.remove('setuptools')

        # hack to allow the package-data sanity test to keep wheel in the venv
        install_commands = [command for command in commands if isinstance(command, PipInstall)]
        install_wheel = any(install.has_package('wheel') for install in install_commands)

        if install_wheel:
            uninstall_packages.remove('wheel')

        commands.extend(collect_uninstall(packages=uninstall_packages))

    return commands


def run_pip(
    args: EnvironmentConfig,
    python: PythonConfig,
    commands: list[PipCommand],
    connection: t.Optional[Connection],
) -> None:
    """Run the specified pip commands for the given Python, and optionally the specified host."""
    connection = connection or LocalConnection(args)
    script = prepare_pip_script(commands)

    if isinstance(args, IntegrationConfig):
        # Integration tests can involve two hosts (controller and target).
        # The connection type can be used to disambiguate between the two.
        context = " (controller)" if isinstance(connection, LocalConnection) else " (target)"
    else:
        context = ""

    if isinstance(python, VirtualPythonConfig):
        context += " [venv]"

    # The interpreter path is not included below.
    # It can be seen by running ansible-test with increased verbosity (showing all commands executed).
    display.info(f'Installing requirements for Python {python.version}{context}')

    if not args.explain:
        try:
            connection.run([python.path], data=script, capture=False)
        except SubprocessError:
            script = prepare_pip_script([PipVersion()])

            try:
                connection.run([python.path], data=script, capture=True)
            except SubprocessError as ex:
                if 'pip is unavailable:' in ex.stdout + ex.stderr:
                    raise PipUnavailableError(python)

            raise


# Collect


def collect_general_install(
    command: t.Optional[str] = None,
    ansible: bool = False,
) -> list[PipInstall]:
    """Return details necessary for the specified general-purpose pip install(s)."""
    requirements_paths: list[tuple[str, str]] = []
    constraints_paths: list[tuple[str, str]] = []

    if ansible:
        path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'ansible.txt')
        requirements_paths.append((ANSIBLE_TEST_DATA_ROOT, path))

    if command:
        path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', f'{command}.txt')
        requirements_paths.append((ANSIBLE_TEST_DATA_ROOT, path))

    return collect_install(requirements_paths, constraints_paths)


def collect_package_install(packages: list[str], constraints: bool = True) -> list[PipInstall]:
    """Return the details necessary to install the specified packages."""
    return collect_install([], [], packages, constraints=constraints)


def collect_sanity_install(sanity: str) -> list[PipInstall]:
    """Return the details necessary for the specified sanity pip install(s)."""
    requirements_paths: list[tuple[str, str]] = []
    constraints_paths: list[tuple[str, str]] = []

    path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', f'sanity.{sanity}.txt')
    requirements_paths.append((ANSIBLE_TEST_DATA_ROOT, path))

    if data_context().content.is_ansible:
        path = os.path.join(data_context().content.sanity_path, 'code-smell', f'{sanity}.requirements.txt')
        requirements_paths.append((data_context().content.root, path))

    return collect_install(requirements_paths, constraints_paths, constraints=False)


def collect_units_install() -> list[PipInstall]:
    """Return details necessary for the specified units pip install(s)."""
    requirements_paths: list[tuple[str, str]] = []
    constraints_paths: list[tuple[str, str]] = []

    path = os.path.join(data_context().content.unit_path, 'requirements.txt')
    requirements_paths.append((data_context().content.root, path))

    path = os.path.join(data_context().content.unit_path, 'constraints.txt')
    constraints_paths.append((data_context().content.root, path))

    return collect_install(requirements_paths, constraints_paths)


def collect_integration_install(command: str, controller: bool) -> list[PipInstall]:
    """Return details necessary for the specified integration pip install(s)."""
    requirements_paths: list[tuple[str, str]] = []
    constraints_paths: list[tuple[str, str]] = []

    # Support for prefixed files was added to ansible-test in ansible-core 2.12 when split controller/target testing was implemented.
    # Previous versions of ansible-test only recognize non-prefixed files.
    # If a prefixed file exists (even if empty), it takes precedence over the non-prefixed file.
    prefixes = ('controller.' if controller else 'target.', '')

    for prefix in prefixes:
        path = os.path.join(data_context().content.integration_path, f'{prefix}requirements.txt')

        if os.path.exists(path):
            requirements_paths.append((data_context().content.root, path))
            break

    for prefix in prefixes:
        path = os.path.join(data_context().content.integration_path, f'{command}.{prefix}requirements.txt')

        if os.path.exists(path):
            requirements_paths.append((data_context().content.root, path))
            break

    for prefix in prefixes:
        path = os.path.join(data_context().content.integration_path, f'{prefix}constraints.txt')

        if os.path.exists(path):
            constraints_paths.append((data_context().content.root, path))
            break

    return collect_install(requirements_paths, constraints_paths)


def collect_install(
    requirements_paths: list[tuple[str, str]],
    constraints_paths: list[tuple[str, str]],
    packages: t.Optional[list[str]] = None,
    constraints: bool = True,
) -> list[PipInstall]:
    """Build a pip install list from the given requirements, constraints and packages."""
    # listing content constraints first gives them priority over constraints provided by ansible-test
    constraints_paths = list(constraints_paths)

    if constraints:
        constraints_paths.append((ANSIBLE_TEST_DATA_ROOT, os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'constraints.txt')))

    requirements = [(os.path.relpath(path, root), read_text_file(path)) for root, path in requirements_paths if usable_pip_file(path)]
    constraints = [(os.path.relpath(path, root), read_text_file(path)) for root, path in constraints_paths if usable_pip_file(path)]
    packages = packages or []

    if requirements or packages:
        installs = [PipInstall(
            requirements=requirements,
            constraints=constraints,
            packages=packages,
        )]
    else:
        installs = []

    return installs


def collect_uninstall(packages: list[str], ignore_errors: bool = False) -> list[PipUninstall]:
    """Return the details necessary for the specified pip uninstall."""
    uninstall = PipUninstall(
        packages=packages,
        ignore_errors=ignore_errors,
    )

    return [uninstall]


# Support


def get_venv_packages(python: PythonConfig) -> dict[str, str]:
    """Return a dictionary of Python packages needed for a consistent virtual environment specific to the given Python version."""

    # NOTE: This same information is needed for building the base-test-container image.
    #       See: https://github.com/ansible/base-test-container/blob/main/files/installer.py

    default_packages = dict(
        pip='21.3.1',
        setuptools='60.8.2',
        wheel='0.37.1',
    )

    override_packages = {
        '2.7': dict(
            pip='20.3.4',  # 21.0 requires Python 3.6+
            setuptools='44.1.1',  # 45.0.0 requires Python 3.5+
            wheel=None,
        ),
        '3.5': dict(
            pip='20.3.4',  # 21.0 requires Python 3.6+
            setuptools='50.3.2',  # 51.0.0 requires Python 3.6+
            wheel=None,
        ),
        '3.6': dict(
            pip='21.3.1',  # 22.0 requires Python 3.7+
            setuptools='59.6.0',  # 59.7.0 requires Python 3.7+
            wheel=None,
        ),
    }

    packages = {name: version or default_packages[name] for name, version in override_packages.get(python.version, default_packages).items()}

    return packages


def requirements_allowed(args: EnvironmentConfig, controller: bool) -> bool:
    """
    Return True if requirements can be installed, otherwise return False.

    Requirements are only allowed if one of the following conditions is met:

    The user specified --requirements manually.
    The install will occur on the controller and the controller or controller Python is managed by ansible-test.
    The install will occur on the target and the target or target Python is managed by ansible-test.
    """
    if args.requirements:
        return True

    if controller:
        return args.controller.is_managed or args.controller.python.is_managed

    target = args.only_targets(PosixConfig)[0]

    return target.is_managed or target.python.is_managed


def prepare_pip_script(commands: list[PipCommand]) -> str:
    """Generate a Python script to perform the requested pip commands."""
    data = [command.serialize() for command in commands]

    display.info(f'>>> Requirements Commands\n{json.dumps(data, indent=4)}', verbosity=3)

    args = dict(
        script=read_text_file(QUIET_PIP_SCRIPT_PATH),
        verbosity=display.verbosity,
        commands=data,
    )

    payload = to_text(base64.b64encode(to_bytes(json.dumps(args))))
    path = REQUIREMENTS_SCRIPT_PATH
    template = read_text_file(path)
    script = template.format(payload=payload)

    display.info(f'>>> Python Script from Template ({path})\n{script.strip()}', verbosity=4)

    return script


def usable_pip_file(path: t.Optional[str]) -> bool:
    """Return True if the specified pip file is usable, otherwise False."""
    return bool(path) and os.path.exists(path) and bool(os.path.getsize(path))


# Cryptography


def is_cryptography_available(python: str) -> bool:
    """Return True if cryptography is available for the given python."""
    try:
        raw_command([python, '-c', 'import cryptography'], capture=True)
    except SubprocessError:
        return False

    return True


def get_cryptography_requirements(python: PythonConfig) -> list[str]:
    """
    Return the correct cryptography and pyopenssl requirements for the given python version.
    The version of cryptography installed depends on the python version and openssl version.
    """
    openssl_version = get_openssl_version(python)

    if openssl_version and openssl_version < (1, 1, 0):
        # cryptography 3.2 requires openssl 1.1.x or later
        # see https://cryptography.io/en/latest/changelog.html#v3-2
        cryptography = 'cryptography < 3.2'
        # pyopenssl 20.0.0 requires cryptography 3.2 or later
        pyopenssl = 'pyopenssl < 20.0.0'
    else:
        # cryptography 3.4+ builds require a working rust toolchain
        # systems bootstrapped using ansible-core-ci can access additional wheels through the spare-tire package index
        cryptography = 'cryptography'
        # any future installation of pyopenssl is free to use any compatible version of cryptography
        pyopenssl = ''

    requirements = [
        cryptography,
        pyopenssl,
    ]

    requirements = [requirement for requirement in requirements if requirement]

    return requirements


def get_openssl_version(python: PythonConfig) -> t.Optional[tuple[int, ...]]:
    """Return the openssl version."""
    if not python.version.startswith('2.'):
        # OpenSSL version checking only works on Python 3.x.
        # This should be the most accurate, since it is the Python we will be using.
        version = json.loads(raw_command([python.path, os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'sslcheck.py')], capture=True)[0])['version']

        if version:
            display.info(f'Detected OpenSSL version {version_to_str(version)} under Python {python.version}.', verbosity=1)

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

            display.info(f'Detected OpenSSL version {version_to_str(version)} using the openssl CLI.', verbosity=1)

            return version

    display.info('Unable to detect OpenSSL version.', verbosity=1)

    return None
