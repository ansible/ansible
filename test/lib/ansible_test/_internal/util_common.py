"""Common utility code that depends on CommonConfig."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import contextlib
import os
import shutil
import tempfile
import textwrap

from .util import (
    common_environment,
    COVERAGE_CONFIG_PATH,
    COVERAGE_OUTPUT_PATH,
    display,
    find_python,
    ANSIBLE_ROOT,
    is_shippable,
    MODE_DIRECTORY,
    MODE_FILE_EXECUTE,
    PYTHON_PATHS,
    raw_command,
    to_bytes,
    ANSIBLE_TEST_DATA_ROOT,
)


class CommonConfig:
    """Configuration common to all commands."""
    def __init__(self, args, command):
        """
        :type args: any
        :type command: str
        """
        self.command = command

        self.color = args.color  # type: bool
        self.explain = args.explain  # type: bool
        self.verbosity = args.verbosity  # type: int
        self.debug = args.debug  # type: bool
        self.truncate = args.truncate  # type: int
        self.redact = args.redact  # type: bool

        if is_shippable():
            self.redact = True

        self.cache = {}


@contextlib.contextmanager
def named_temporary_file(args, prefix, suffix, directory, content):
    """
    :param args: CommonConfig
    :param prefix: str
    :param suffix: str
    :param directory: str
    :param content: str | bytes | unicode
    :rtype: str
    """
    if args.explain:
        yield os.path.join(directory, '%stemp%s' % (prefix, suffix))
    else:
        with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, dir=directory) as tempfile_fd:
            tempfile_fd.write(to_bytes(content))
            tempfile_fd.flush()

            yield tempfile_fd.name


def get_python_path(args, interpreter):
    """
    :type args: TestConfig
    :type interpreter: str
    :rtype: str
    """
    # When the python interpreter is already named "python" its directory can simply be added to the path.
    # Using another level of indirection is only required when the interpreter has a different name.
    if os.path.basename(interpreter) == 'python':
        return os.path.dirname(interpreter)

    python_path = PYTHON_PATHS.get(interpreter)

    if python_path:
        return python_path

    prefix = 'python-'
    suffix = '-ansible'

    root_temp_dir = '/tmp'

    if args.explain:
        return os.path.join(root_temp_dir, ''.join((prefix, 'temp', suffix)))

    python_path = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=root_temp_dir)
    injected_interpreter = os.path.join(python_path, 'python')

    # A symlink is faster than the execv wrapper, but isn't compatible with virtual environments.
    # Attempt to detect when it is safe to use a symlink by checking the real path of the interpreter.
    use_symlink = os.path.dirname(os.path.realpath(interpreter)) == os.path.dirname(interpreter)

    if use_symlink:
        display.info('Injecting "%s" as a symlink to the "%s" interpreter.' % (injected_interpreter, interpreter), verbosity=1)

        os.symlink(interpreter, injected_interpreter)
    else:
        display.info('Injecting "%s" as a execv wrapper for the "%s" interpreter.' % (injected_interpreter, interpreter), verbosity=1)

        code = textwrap.dedent('''
        #!%s

        from __future__ import absolute_import

        from os import execv
        from sys import argv

        python = '%s'

        execv(python, [python] + argv[1:])
        ''' % (interpreter, interpreter)).lstrip()

        with open(injected_interpreter, 'w') as python_fd:
            python_fd.write(code)

        os.chmod(injected_interpreter, MODE_FILE_EXECUTE)

    os.chmod(python_path, MODE_DIRECTORY)

    if not PYTHON_PATHS:
        atexit.register(cleanup_python_paths)

    PYTHON_PATHS[interpreter] = python_path

    return python_path


def cleanup_python_paths():
    """Clean up all temporary python directories."""
    for path in sorted(PYTHON_PATHS.values()):
        display.info('Cleaning up temporary python directory: %s' % path, verbosity=2)
        shutil.rmtree(path)


def get_coverage_environment(args, target_name, version, temp_path, module_coverage):
    """
    :type args: TestConfig
    :type target_name: str
    :type version: str
    :type temp_path: str
    :type module_coverage: bool
    :rtype: dict[str, str]
    """
    if temp_path:
        # integration tests (both localhost and the optional testhost)
        # config and results are in a temporary directory
        coverage_config_base_path = temp_path
        coverage_output_base_path = temp_path
    else:
        # unit tests, sanity tests and other special cases (localhost only)
        # config and results are in the source tree
        coverage_config_base_path = args.coverage_config_base_path or ANSIBLE_ROOT
        coverage_output_base_path = os.path.abspath(os.path.join('test/results'))

    config_file = os.path.join(coverage_config_base_path, COVERAGE_CONFIG_PATH)
    coverage_file = os.path.join(coverage_output_base_path, COVERAGE_OUTPUT_PATH, '%s=%s=%s=%s=coverage' % (
        args.command, target_name, args.coverage_label or 'local-%s' % version, 'python-%s' % version))

    if args.coverage_check:
        # cause the 'coverage' module to be found, but not imported or enabled
        coverage_file = ''

    # Enable code coverage collection on local Python programs (this does not include Ansible modules).
    # Used by the injectors to support code coverage.
    # Used by the pytest unit test plugin to support code coverage.
    # The COVERAGE_FILE variable is also used directly by the 'coverage' module.
    env = dict(
        COVERAGE_CONF=config_file,
        COVERAGE_FILE=coverage_file,
    )

    if module_coverage:
        # Enable code coverage collection on Ansible modules (both local and remote).
        # Used by the AnsiballZ wrapper generator in lib/ansible/executor/module_common.py to support code coverage.
        env.update(dict(
            _ANSIBLE_COVERAGE_CONFIG=config_file,
            _ANSIBLE_COVERAGE_OUTPUT=coverage_file,
        ))

    return env


def intercept_command(args, cmd, target_name, env, capture=False, data=None, cwd=None, python_version=None, temp_path=None, module_coverage=True,
                      virtualenv=None):
    """
    :type args: TestConfig
    :type cmd: collections.Iterable[str]
    :type target_name: str
    :type env: dict[str, str]
    :type capture: bool
    :type data: str | None
    :type cwd: str | None
    :type python_version: str | None
    :type temp_path: str | None
    :type module_coverage: bool
    :type virtualenv: str | None
    :rtype: str | None, str | None
    """
    if not env:
        env = common_environment()

    cmd = list(cmd)
    version = python_version or args.python_version
    interpreter = virtualenv or find_python(version)
    inject_path = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'injector')

    if not virtualenv:
        # injection of python into the path is required when not activating a virtualenv
        # otherwise scripts may find the wrong interpreter or possibly no interpreter
        python_path = get_python_path(args, interpreter)
        inject_path = python_path + os.path.pathsep + inject_path

    env['PATH'] = inject_path + os.path.pathsep + env['PATH']
    env['ANSIBLE_TEST_PYTHON_VERSION'] = version
    env['ANSIBLE_TEST_PYTHON_INTERPRETER'] = interpreter

    if args.coverage:
        # add the necessary environment variables to enable code coverage collection
        env.update(get_coverage_environment(args, target_name, version, temp_path, module_coverage))

    return run_command(args, cmd, capture=capture, env=env, data=data, cwd=cwd)


def run_command(args, cmd, capture=False, env=None, data=None, cwd=None, always=False, stdin=None, stdout=None,
                cmd_verbosity=1, str_errors='strict'):
    """
    :type args: CommonConfig
    :type cmd: collections.Iterable[str]
    :type capture: bool
    :type env: dict[str, str] | None
    :type data: str | None
    :type cwd: str | None
    :type always: bool
    :type stdin: file | None
    :type stdout: file | None
    :type cmd_verbosity: int
    :type str_errors: str
    :rtype: str | None, str | None
    """
    explain = args.explain and not always
    return raw_command(cmd, capture=capture, env=env, data=data, cwd=cwd, explain=explain, stdin=stdin, stdout=stdout,
                       cmd_verbosity=cmd_verbosity, str_errors=str_errors)
