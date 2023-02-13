"""Virtual environment management."""
from __future__ import annotations

import collections.abc as c
import json
import os
import pathlib
import sys
import typing as t

from .config import (
    EnvironmentConfig,
)

from .util import (
    find_python,
    SubprocessError,
    get_available_python_versions,
    ANSIBLE_TEST_TARGET_TOOLS_ROOT,
    display,
    remove_tree,
    ApplicationError,
    str_to_version,
    raw_command,
)

from .util_common import (
    run_command,
    ResultType,
)

from .host_configs import (
    VirtualPythonConfig,
    PythonConfig,
)

from .python_requirements import (
    collect_bootstrap,
    run_pip,
)


def get_virtual_python(
    args: EnvironmentConfig,
    python: VirtualPythonConfig,
) -> VirtualPythonConfig:
    """Create a virtual environment for the given Python and return the path to its root."""
    if python.system_site_packages:
        suffix = '-ssp'
    else:
        suffix = ''

    virtual_environment_path = os.path.join(ResultType.TMP.path, 'delegation', f'python{python.version}{suffix}')
    virtual_environment_marker = os.path.join(virtual_environment_path, 'marker.txt')

    virtual_environment_python = VirtualPythonConfig(
        version=python.version,
        path=os.path.join(virtual_environment_path, 'bin', 'python'),
        system_site_packages=python.system_site_packages,
    )

    if os.path.exists(virtual_environment_marker):
        display.info('Using existing Python %s virtual environment: %s' % (python.version, virtual_environment_path), verbosity=1)
    else:
        # a virtualenv without a marker is assumed to have been partially created
        remove_tree(virtual_environment_path)

        if not create_virtual_environment(args, python, virtual_environment_path, python.system_site_packages):
            raise ApplicationError(f'Python {python.version} does not provide virtual environment support.')

        commands = collect_bootstrap(virtual_environment_python)

        run_pip(args, virtual_environment_python, commands, None)  # get_virtual_python()

    # touch the marker to keep track of when the virtualenv was last used
    pathlib.Path(virtual_environment_marker).touch()

    return virtual_environment_python


def create_virtual_environment(
    args: EnvironmentConfig,
    python: PythonConfig,
    path: str,
    system_site_packages: bool = False,
    pip: bool = False,
) -> bool:
    """Create a virtual environment using venv or virtualenv for the requested Python version."""
    if not os.path.exists(python.path):
        # the requested python version could not be found
        return False

    if str_to_version(python.version) >= (3, 0):
        # use the built-in 'venv' module on Python 3.x
        # creating a virtual environment using 'venv' when running in a virtual environment created by 'virtualenv' results
        # in a copy of the original virtual environment instead of creation of a new one
        # avoid this issue by only using "real" python interpreters to invoke 'venv'
        for real_python in iterate_real_pythons(python.version):
            if run_venv(args, real_python, system_site_packages, pip, path):
                display.info('Created Python %s virtual environment using "venv": %s' % (python.version, path), verbosity=1)
                return True

        # something went wrong, most likely the package maintainer for the Python installation removed ensurepip
        # which will prevent creation of a virtual environment without installation of other OS packages

    # use the installed 'virtualenv' module on the Python requested version
    if run_virtualenv(args, python.path, python.path, system_site_packages, pip, path):
        display.info('Created Python %s virtual environment using "virtualenv": %s' % (python.version, path), verbosity=1)
        return True

    available_pythons = get_available_python_versions()

    for available_python_version, available_python_interpreter in sorted(available_pythons.items()):
        if available_python_interpreter == python.path:
            # already attempted to use this interpreter
            continue

        virtualenv_version = get_virtualenv_version(args, available_python_interpreter)

        if not virtualenv_version:
            # virtualenv not available for this Python or we were unable to detect the version
            continue

        # try using 'virtualenv' from another Python to setup the desired version
        if run_virtualenv(args, available_python_interpreter, python.path, system_site_packages, pip, path):
            display.info('Created Python %s virtual environment using "virtualenv" on Python %s: %s' % (python.version, available_python_version, path),
                         verbosity=1)
            return True

    # no suitable 'virtualenv' available
    return False


def iterate_real_pythons(version: str) -> c.Iterable[str]:
    """
    Iterate through available real python interpreters of the requested version.
    The current interpreter will be checked and then the path will be searched.
    """
    version_info = str_to_version(version)
    current_python = None

    if version_info == sys.version_info[:len(version_info)]:
        current_python = sys.executable
        real_prefix = get_python_real_prefix(current_python)

        if real_prefix:
            current_python = find_python(version, os.path.join(real_prefix, 'bin'))

        if current_python:
            yield current_python

    path = os.environ.get('PATH', os.path.defpath)

    if not path:
        return

    found_python = find_python(version, path)

    if not found_python:
        return

    if found_python == current_python:
        return

    real_prefix = get_python_real_prefix(found_python)

    if real_prefix:
        found_python = find_python(version, os.path.join(real_prefix, 'bin'))

    if found_python:
        yield found_python


def get_python_real_prefix(python_path: str) -> t.Optional[str]:
    """
    Return the real prefix of the specified interpreter or None if the interpreter is not a virtual environment created by 'virtualenv'.
    """
    cmd = [python_path, os.path.join(os.path.join(ANSIBLE_TEST_TARGET_TOOLS_ROOT, 'virtualenvcheck.py'))]
    check_result = json.loads(raw_command(cmd, capture=True)[0])
    real_prefix = check_result['real_prefix']
    return real_prefix


def run_venv(
    args: EnvironmentConfig,
    run_python: str,
    system_site_packages: bool,
    pip: bool,
    path: str,
) -> bool:
    """Create a virtual environment using the 'venv' module. Not available on Python 2.x."""
    cmd = [run_python, '-m', 'venv']

    if system_site_packages:
        cmd.append('--system-site-packages')

    if not pip:
        cmd.append('--without-pip')

    cmd.append(path)

    try:
        run_command(args, cmd, capture=True)
    except SubprocessError as ex:
        remove_tree(path)

        if args.verbosity > 1:
            display.error(ex.message)

        return False

    return True


def run_virtualenv(
    args: EnvironmentConfig,
    run_python: str,
    env_python: str,
    system_site_packages: bool,
    pip: bool,
    path: str,
) -> bool:
    """Create a virtual environment using the 'virtualenv' module."""
    # always specify which interpreter to use to guarantee the desired interpreter is provided
    # otherwise virtualenv may select a different interpreter than the one running virtualenv
    cmd = [run_python, '-m', 'virtualenv', '--python', env_python]

    if system_site_packages:
        cmd.append('--system-site-packages')

    if not pip:
        cmd.append('--no-pip')
        # these options provide consistency with venv, which does not install them without pip
        cmd.append('--no-setuptools')
        cmd.append('--no-wheel')

    cmd.append(path)

    try:
        run_command(args, cmd, capture=True)
    except SubprocessError as ex:
        remove_tree(path)

        if args.verbosity > 1:
            display.error(ex.message)

        return False

    return True


def get_virtualenv_version(args: EnvironmentConfig, python: str) -> t.Optional[tuple[int, ...]]:
    """Get the virtualenv version for the given python interpreter, if available, otherwise return None."""
    try:
        cache = get_virtualenv_version.cache  # type: ignore[attr-defined]
    except AttributeError:
        cache = get_virtualenv_version.cache = {}  # type: ignore[attr-defined]

    if python not in cache:
        try:
            stdout = run_command(args, [python, '-m', 'virtualenv', '--version'], capture=True)[0]
        except SubprocessError as ex:
            stdout = ''

            if args.verbosity > 1:
                display.error(ex.message)

        version = None

        if stdout:
            # noinspection PyBroadException
            try:
                version = str_to_version(stdout.strip())
            except Exception:  # pylint: disable=broad-except
                pass

        cache[python] = version

    version = cache[python]

    return version
