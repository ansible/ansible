"""Virtual environment management."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import types as t

from .config import (
    EnvironmentConfig,
)

from .util import (
    find_python,
    SubprocessError,
    get_available_python_versions,
    SUPPORTED_PYTHON_VERSIONS,
    display,
)

from .util_common import (
    run_command,
)


def create_virtual_environment(args,  # type: EnvironmentConfig
                               version,  # type: str
                               path,  # type: str
                               system_site_packages=False,  # type: bool
                               pip=True,  # type: bool
                               ):  # type: (...) -> bool
    """Create a virtual environment using venv or virtualenv for the requested Python version."""
    if os.path.isdir(path):
        display.info('Using existing Python %s virtual environment: %s' % (version, path))
        return True

    python = find_python(version, required=False)
    python_version = tuple(int(v) for v in version.split('.'))

    if not python:
        # the requested python version could not be found
        return False

    if python_version >= (3, 0):
        # use the built-in 'venv' module on Python 3.x
        if run_venv(args, python, system_site_packages, pip, path):
            display.info('Created Python %s virtual environment using "venv": %s' % (version, path))
            return True

        # something went wrong, this shouldn't happen
        return False

    available_pythons = get_available_python_versions(SUPPORTED_PYTHON_VERSIONS)
    available_virtualenvs = get_available_virtualenv_versions(args, available_pythons)

    if version == '2.6':
        # virtualenv 16.0.0 dropped python 2.6 support: https://virtualenv.pypa.io/en/latest/changes/#v16-0-0-2018-05-16
        available_virtualenvs = dict((pv, vv) for pv, vv in available_virtualenvs.items() if vv < (16, 0, 0))

    if not available_virtualenvs:
        # no known python interpreter has a suitable 'virtualenv' installed
        return False

    virtualenv = available_virtualenvs.get(version)

    if virtualenv:
        # use the installed 'virtualenv' module on the Python requested version
        if run_virtualenv(args, python, python, system_site_packages, pip, path):
            display.info('Created Python %s virtual environment using "virtualenv": %s' % (version, path))
            return True

    # the 'virtualenv' module was found for a Python version other than the one requested

    for available_version in sorted(available_virtualenvs.keys()):
        available_python = available_pythons[available_version]

        # try using 'virtualenv' from another Python to setup the desired version
        if run_virtualenv(args, available_python, python, system_site_packages, pip, path):
            display.info('Created Python %s virtual environment using "virtualenv" on Python %s: %s' % (version, available_version, path))
            return True

    # no suitable 'virtualenv' available
    return False


def run_venv(args,  # type: EnvironmentConfig
             run_python,  # type: str
             system_site_packages,  # type: bool
             pip,  # type: bool
             path,  # type: str
             ):  # type: (...) -> bool
    """Create a virtual environment using the 'venv' module. Not available on Python 2.x."""
    cmd = [run_python, '-m', 'venv']

    if system_site_packages:
        cmd.append('--system-site-packages')

    if not pip:
        cmd.append('--without-pip')

    cmd.append(path)

    try:
        run_command(args, cmd, capture=True)
    except SubprocessError:
        return False

    return True


def run_virtualenv(args,  # type: EnvironmentConfig
                   run_python,  # type: str
                   env_python,  # type: str
                   system_site_packages,  # type: bool
                   pip,  # type: bool
                   path,  # type: str
                   ):  # type: (...) -> bool
    """Create a virtual environment using the 'virtualenv' module."""
    cmd = [run_python, '-m', 'virtualenv', '--python', env_python]

    if system_site_packages:
        cmd.append('--system-site-packages')

    if not pip:
        cmd.append('--no-pip')

    cmd.append(path)

    try:
        run_command(args, cmd, capture=True)
    except SubprocessError:
        return False

    return True


def get_available_virtualenv_versions(args, versions):  # type: (EnvironmentConfig, t.Dict[str, str]) -> t.Dict[str, t.Tuple[int, ...]]
    """Return a dictionary indicating the virtualenv version available for the requested Python versions."""
    try:
        return get_available_virtualenv_versions.result
    except AttributeError:
        pass

    get_available_virtualenv_versions.result = dict((pv, vv) for pv, vv in
                                                    ((version, get_virtualenv_version(args, python)) for version, python in versions.items()) if vv)

    return get_available_virtualenv_versions.result


def get_virtualenv_version(args, python):  # type: (EnvironmentConfig, str) -> t.Optional[t.Tuple[int, ...]]
    """Get the virtualenv version for the given python intepreter, if available."""
    cmd = [python, '-m', 'virtualenv', '--version']

    try:
        stdout = run_command(args, cmd, capture=True)[0]
    except SubprocessError:
        return None

    # noinspection PyBroadException
    try:
        return tuple(int(v) for v in stdout.strip().split('.'))
    except Exception:  # pylint: disable=broad-except
        return None
