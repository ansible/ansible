"""Virtual environment management."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import sys

from . import types as t

from .config import (
    EnvironmentConfig,
)

from .util import (
    find_python,
    SubprocessError,
    get_available_python_versions,
    SUPPORTED_PYTHON_VERSIONS,
    ANSIBLE_TEST_DATA_ROOT,
    display,
    remove_tree,
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
        display.info('Using existing Python %s virtual environment: %s' % (version, path), verbosity=1)
        return True

    python = find_python(version, required=False)
    python_version = tuple(int(v) for v in version.split('.'))

    if not python:
        # the requested python version could not be found
        return False

    if python_version >= (3, 0):
        # use the built-in 'venv' module on Python 3.x
        # creating a virtual environment using 'venv' when running in a virtual environment created by 'virtualenv' results
        # in a copy of the original virtual environment instead of creation of a new one
        # avoid this issue by only using "real" python interpreters to invoke 'venv'
        for real_python in iterate_real_pythons(args, version):
            if run_venv(args, real_python, system_site_packages, pip, path):
                display.info('Created Python %s virtual environment using "venv": %s' % (version, path), verbosity=1)
                return True

        # something went wrong, most likely the package maintainer for the Python installation removed ensurepip
        # which will prevent creation of a virtual environment without installation of other OS packages

    # use the installed 'virtualenv' module on the Python requested version
    if run_virtualenv(args, python, python, system_site_packages, pip, path):
        display.info('Created Python %s virtual environment using "virtualenv": %s' % (version, path), verbosity=1)
        return True

    available_pythons = get_available_python_versions(SUPPORTED_PYTHON_VERSIONS)

    for available_python_version, available_python_interpreter in sorted(available_pythons.items()):
        virtualenv_version = get_virtualenv_version(args, available_python_interpreter)

        if not virtualenv_version:
            # virtualenv not available for this Python or we were unable to detect the version
            continue

        if python_version == (2, 6) and virtualenv_version >= (16, 0, 0):
            # virtualenv 16.0.0 dropped python 2.6 support: https://virtualenv.pypa.io/en/latest/changes/#v16-0-0-2018-05-16
            continue

        # try using 'virtualenv' from another Python to setup the desired version
        if run_virtualenv(args, available_python_interpreter, python, system_site_packages, pip, path):
            display.info('Created Python %s virtual environment using "virtualenv" on Python %s: %s' % (version, available_python_version, path), verbosity=1)
            return True

    # no suitable 'virtualenv' available
    return False


def iterate_real_pythons(args, version):  # type: (EnvironmentConfig, str) -> t.Iterable[str]
    """
    Iterate through available real python interpreters of the requested version.
    The current interpreter will be checked and then the path will be searched.
    """
    version_info = tuple(int(n) for n in version.split('.'))
    current_python = None

    if version_info == sys.version_info[:len(version_info)]:
        current_python = sys.executable
        real_prefix = get_python_real_prefix(args, current_python)

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

    real_prefix = get_python_real_prefix(args, found_python)

    if real_prefix:
        found_python = find_python(version, os.path.join(real_prefix, 'bin'))

    if found_python:
        yield found_python


def get_python_real_prefix(args, path):  # type: (EnvironmentConfig, str) -> t.Optional[str]
    """
    Return the real prefix of the specified interpreter or None if the interpreter is not a virtual environment created by 'virtualenv'.
    """
    cmd = [path, os.path.join(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'virtualenvcheck.py'))]
    check_result = json.loads(run_command(args, cmd, capture=True, always=True)[0])
    real_prefix = check_result['real_prefix']
    return real_prefix


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
    except SubprocessError as ex:
        remove_tree(path)

        if args.verbosity > 1:
            display.error(ex)

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
    # always specify --python to guarantee the desired interpreter is provided
    # otherwise virtualenv may select a different interpreter than the one running virtualenv
    cmd = [run_python, '-m', 'virtualenv', '--python', env_python]

    if system_site_packages:
        cmd.append('--system-site-packages')

    if not pip:
        cmd.append('--no-pip')

    cmd.append(path)

    try:
        run_command(args, cmd, capture=True)
    except SubprocessError as ex:
        remove_tree(path)

        if args.verbosity > 1:
            display.error(ex)

        return False

    return True


def get_virtualenv_version(args, python):  # type: (EnvironmentConfig, str) -> t.Optional[t.Tuple[int, ...]]
    """Get the virtualenv version for the given python intepreter, if available."""
    try:
        return get_virtualenv_version.result
    except AttributeError:
        pass

    get_virtualenv_version.result = None

    cmd = [python, '-m', 'virtualenv', '--version']

    try:
        stdout = run_command(args, cmd, capture=True)[0]
    except SubprocessError as ex:
        if args.verbosity > 1:
            display.error(ex)

        stdout = ''

    if stdout:
        # noinspection PyBroadException
        try:
            get_virtualenv_version.result = tuple(int(v) for v in stdout.strip().split('.'))
        except Exception:  # pylint: disable=broad-except
            pass

    return get_virtualenv_version.result
