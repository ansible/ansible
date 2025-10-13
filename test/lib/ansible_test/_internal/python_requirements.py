"""Python requirements management"""

from __future__ import annotations

import base64
import dataclasses
import json
import os
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
    ApplicationError,
    SubprocessError,
    display,
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

if t.TYPE_CHECKING:
    from .host_profiles import (
        HostProfile,
    )

QUIET_PIP_SCRIPT_PATH = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'quiet_pip.py')
REQUIREMENTS_SCRIPT_PATH = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'requirements.py')

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
    setuptools: bool
    wheel: bool


# Entry Points


def install_requirements(
    args: EnvironmentConfig,
    host_profile: HostProfile | None,
    python: PythonConfig,
    ansible: bool = False,
    command: bool = False,
    coverage: bool = False,
    controller: bool = True,
    connection: t.Optional[Connection] = None,
) -> None:
    """Install requirements for the given Python using the specified arguments."""
    create_result_directories(args)

    if not requirements_allowed(args, controller):
        post_install(host_profile)
        return

    if command and isinstance(args, (UnitsConfig, IntegrationConfig)) and args.coverage:
        coverage = True

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

    commands = collect_requirements(
        python=python,
        controller=controller,
        ansible=ansible,
        command=args.command if command else None,
        coverage=coverage,
        minimize=False,
        sanity=None,
    )

    from .host_profiles import DebuggableProfile

    if isinstance(host_profile, DebuggableProfile) and host_profile.debugger and host_profile.debugger.get_python_package():
        commands.append(PipInstall(
            requirements=[],
            constraints=[],
            packages=[host_profile.debugger.get_python_package()],
        ))

    if not commands:
        post_install(host_profile)
        return

    run_pip(args, python, commands, connection)

    # false positive: pylint: disable=no-member
    if any(isinstance(command, PipInstall) and command.has_package('pyyaml') for command in commands):
        check_pyyaml(python)

    post_install(host_profile)


def post_install(host_profile: HostProfile) -> None:
    """Operations to perform after requirements are installed."""
    from .host_profiles import DebuggableProfile

    if isinstance(host_profile, DebuggableProfile):
        host_profile.activate_debugger()


def collect_bootstrap(python: PythonConfig) -> list[PipCommand]:
    """Return the details necessary to bootstrap pip into an empty virtual environment."""
    infrastructure_packages = get_venv_packages(python)
    pip_version = infrastructure_packages['pip']
    packages = [f'{name}=={version}' for name, version in infrastructure_packages.items()]

    bootstrap = PipBootstrap(
        pip_version=pip_version,
        packages=packages,
        setuptools=False,
        wheel=False,
    )

    return [bootstrap]


def collect_requirements(
    python: PythonConfig,
    controller: bool,
    ansible: bool,
    coverage: bool,
    minimize: bool,
    command: t.Optional[str],
    sanity: t.Optional[str],
) -> list[PipCommand]:
    """Collect requirements for the given Python using the specified arguments."""
    commands: list[PipCommand] = []

    if coverage:
        commands.extend(collect_package_install(packages=[f'coverage=={get_coverage_version(python.version).coverage_version}'], constraints=False))

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
                    raise PipUnavailableError(python) from None

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
        pip='25.2',
    )

    override_packages: dict[str, dict[str, str]] = {
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
