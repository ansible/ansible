"""Python requirements management"""
from __future__ import annotations

import base64
import dataclasses
import json
import os
import re
import typing as t

from .constants import (
    COVERAGE_REQUIRED_VERSION,
)

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
)

from .connections import (
    LocalConnection,
    Connection,
)

QUIET_PIP_SCRIPT_PATH = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'quiet_pip.py')
REQUIREMENTS_SCRIPT_PATH = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'requirements.py')


# Pip Abstraction


class PipUnavailableError(ApplicationError):
    """Exception raised when pip is not available."""
    def __init__(self, python):  # type: (PythonConfig) -> None
        super().__init__(f'Python {python.version} at "{python.path}" does not have pip available.')


@dataclasses.dataclass(frozen=True)
class PipCommand:
    """Base class for pip commands."""""

    def serialize(self):  # type: () -> t.Tuple[str, t.Dict[str, t.Any]]
        """Return a serialized representation of this command."""
        name = type(self).__name__[3:].lower()
        return name, self.__dict__


@dataclasses.dataclass(frozen=True)
class PipInstall(PipCommand):
    """Details required to perform a pip install."""
    requirements: t.List[t.Tuple[str, str]]
    constraints: t.List[t.Tuple[str, str]]
    packages: t.List[str]

    def has_package(self, name):  # type: (str) -> bool
        """Return True if the specified package will be installed, otherwise False."""
        name = name.lower()

        return (any(name in package.lower() for package in self.packages) or
                any(name in contents.lower() for path, contents in self.requirements))


@dataclasses.dataclass(frozen=True)
class PipUninstall(PipCommand):
    """Details required to perform a pip uninstall."""
    packages: t.List[str]
    ignore_errors: bool


@dataclasses.dataclass(frozen=True)
class PipVersion(PipCommand):
    """Details required to get the pip version."""


# Entry Points


def install_requirements(
        args,  # type: EnvironmentConfig
        python,  # type: PythonConfig
        ansible=False,  # type: bool
        command=False,  # type: bool
        coverage=False,  # type: bool
        virtualenv=False,  # type: bool
        controller=True,  # type: bool
        connection=None,  # type: t.Optional[Connection]
):  # type: (...) -> None
    """Install requirements for the given Python using the specified arguments."""
    create_result_directories(args)

    if not requirements_allowed(args, controller):
        return

    if command and isinstance(args, (UnitsConfig, IntegrationConfig)) and args.coverage:
        coverage = True

    cryptography = False

    if ansible:
        try:
            ansible_cache = install_requirements.ansible_cache
        except AttributeError:
            ansible_cache = install_requirements.ansible_cache = {}

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

    if any(isinstance(command, PipInstall) and command.has_package('pyyaml') for command in commands):
        check_pyyaml(python)


def collect_requirements(
        python,  # type: PythonConfig
        controller,  # type: bool
        ansible,  # type: bool
        cryptography,  # type: bool
        coverage,  # type: bool
        virtualenv,  # type: bool
        minimize,  # type: bool
        command,  # type: t.Optional[str]
        sanity,  # type: t.Optional[str]
):  # type: (...) -> t.List[PipCommand]
    """Collect requirements for the given Python using the specified arguments."""
    commands = []  # type: t.List[PipCommand]

    if virtualenv:
        commands.extend(collect_package_install(packages=['virtualenv']))

    if coverage:
        commands.extend(collect_package_install(packages=[f'coverage=={COVERAGE_REQUIRED_VERSION}'], constraints=False))

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

    if minimize:
        # In some environments pkg_resources is installed as a separate pip package which needs to be removed.
        # For example, using Python 3.8 on Ubuntu 18.04 a virtualenv is created with only pip and setuptools.
        # However, a venv is created with an additional pkg-resources package which is independent of setuptools.
        # Making sure pkg-resources is removed preserves the import test consistency between venv and virtualenv.
        # Additionally, in the above example, the pyparsing package vendored with pkg-resources is out-of-date and generates deprecation warnings.
        # Thus it is important to remove pkg-resources to prevent system installed packages from generating deprecation warnings.
        commands.extend(collect_uninstall(packages=['pkg-resources'], ignore_errors=True))
        commands.extend(collect_uninstall(packages=['setuptools', 'pip']))

    return commands


def run_pip(
        args,  # type: EnvironmentConfig
        python,  # type: PythonConfig
        commands,  # type: t.List[PipCommand]
        connection,  # type: t.Optional[Connection]
):  # type: (...) -> None
    """Run the specified pip commands for the given Python, and optionally the specified host."""
    connection = connection or LocalConnection(args)
    script = prepare_pip_script(commands)

    if not args.explain:
        try:
            connection.run([python.path], data=script)
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
    command=None,  # type: t.Optional[str]
    ansible=False,  # type: bool
):  # type: (...) -> t.List[PipInstall]
    """Return details necessary for the specified general-purpose pip install(s)."""
    requirements_paths = []  # type: t.List[t.Tuple[str, str]]
    constraints_paths = []  # type: t.List[t.Tuple[str, str]]

    if ansible:
        path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'ansible.txt')
        requirements_paths.append((ANSIBLE_TEST_DATA_ROOT, path))

    if command:
        path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', f'{command}.txt')
        requirements_paths.append((ANSIBLE_TEST_DATA_ROOT, path))

    return collect_install(requirements_paths, constraints_paths)


def collect_package_install(packages, constraints=True):  # type: (t.List[str], bool) -> t.List[PipInstall]
    """Return the details necessary to install the specified packages."""
    return collect_install([], [], packages, constraints=constraints)


def collect_sanity_install(sanity):  # type: (str) -> t.List[PipInstall]
    """Return the details necessary for the specified sanity pip install(s)."""
    requirements_paths = []  # type: t.List[t.Tuple[str, str]]
    constraints_paths = []  # type: t.List[t.Tuple[str, str]]

    path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', f'sanity.{sanity}.txt')
    requirements_paths.append((ANSIBLE_TEST_DATA_ROOT, path))

    if data_context().content.is_ansible:
        path = os.path.join(data_context().content.sanity_path, 'code-smell', f'{sanity}.requirements.txt')
        requirements_paths.append((data_context().content.root, path))

    return collect_install(requirements_paths, constraints_paths, constraints=False)


def collect_units_install():  # type: () -> t.List[PipInstall]
    """Return details necessary for the specified units pip install(s)."""
    requirements_paths = []  # type: t.List[t.Tuple[str, str]]
    constraints_paths = []  # type: t.List[t.Tuple[str, str]]

    path = os.path.join(data_context().content.unit_path, 'requirements.txt')
    requirements_paths.append((data_context().content.root, path))

    path = os.path.join(data_context().content.unit_path, 'constraints.txt')
    constraints_paths.append((data_context().content.root, path))

    return collect_install(requirements_paths, constraints_paths)


def collect_integration_install(command, controller):  # type: (str, bool) -> t.List[PipInstall]
    """Return details necessary for the specified integration pip install(s)."""
    requirements_paths = []  # type: t.List[t.Tuple[str, str]]
    constraints_paths = []  # type: t.List[t.Tuple[str, str]]

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
        requirements_paths,  # type: t.List[t.Tuple[str, str]]
        constraints_paths,  # type: t.List[t.Tuple[str, str]]
        packages=None,  # type: t.Optional[t.List[str]]
        constraints=True,  # type: bool
) -> t.List[PipInstall]:
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


def collect_uninstall(packages, ignore_errors=False):  # type: (t.List[str], bool) -> t.List[PipUninstall]
    """Return the details necessary for the specified pip uninstall."""
    uninstall = PipUninstall(
        packages=packages,
        ignore_errors=ignore_errors,
    )

    return [uninstall]


# Support


def requirements_allowed(args, controller):  # type: (EnvironmentConfig, bool) -> bool
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


def prepare_pip_script(commands):  # type: (t.List[PipCommand]) -> str
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


def usable_pip_file(path):  # type: (t.Optional[str]) -> bool
    """Return True if the specified pip file is usable, otherwise False."""
    return path and os.path.exists(path) and os.path.getsize(path)


# Cryptography


def is_cryptography_available(python):  # type: (str) -> bool
    """Return True if cryptography is available for the given python."""
    try:
        raw_command([python, '-c', 'import cryptography'], capture=True)
    except SubprocessError:
        return False

    return True


def get_cryptography_requirements(python):  # type: (PythonConfig) -> t.List[str]
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


def get_openssl_version(python):  # type: (PythonConfig) -> t.Optional[t.Tuple[int, ...]]
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
