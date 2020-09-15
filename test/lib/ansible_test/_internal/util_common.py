"""Common utility code that depends on CommonConfig."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import contextlib
import json
import os
import shutil
import sys
import tempfile
import textwrap

from . import types as t

from .util import (
    common_environment,
    COVERAGE_CONFIG_NAME,
    display,
    find_python,
    remove_tree,
    MODE_DIRECTORY,
    MODE_FILE_EXECUTE,
    PYTHON_PATHS,
    raw_command,
    to_bytes,
    ANSIBLE_TEST_DATA_ROOT,
    make_dirs,
    ApplicationError,
)

from .data import (
    data_context,
)

from .provider.layout import (
    LayoutMessages,
)


class ResultType:
    """Test result type."""
    BOT = None  # type: ResultType
    COVERAGE = None  # type: ResultType
    DATA = None  # type: ResultType
    JUNIT = None  # type: ResultType
    LOGS = None  # type: ResultType
    REPORTS = None  # type: ResultType
    TMP = None   # type: ResultType

    @staticmethod
    def _populate():
        ResultType.BOT = ResultType('bot')
        ResultType.COVERAGE = ResultType('coverage')
        ResultType.DATA = ResultType('data')
        ResultType.JUNIT = ResultType('junit')
        ResultType.LOGS = ResultType('logs')
        ResultType.REPORTS = ResultType('reports')
        ResultType.TMP = ResultType('.tmp')

    def __init__(self, name):  # type: (str) -> None
        self.name = name

    @property
    def relative_path(self):  # type: () -> str
        """The content relative path to the results."""
        return os.path.join(data_context().content.results_path, self.name)

    @property
    def path(self):  # type: () -> str
        """The absolute path to the results."""
        return os.path.join(data_context().content.root, self.relative_path)

    def __str__(self):  # type: () -> str
        return self.name


# noinspection PyProtectedMember
ResultType._populate()  # pylint: disable=protected-access


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

        self.cache = {}

    def get_ansible_config(self):  # type: () -> str
        """Return the path to the Ansible config for the given config."""
        return os.path.join(ANSIBLE_TEST_DATA_ROOT, 'ansible.cfg')


def handle_layout_messages(messages):  # type: (t.Optional[LayoutMessages]) -> None
    """Display the given layout messages."""
    if not messages:
        return

    for message in messages.info:
        display.info(message, verbosity=1)

    for message in messages.warning:
        display.warning(message)

    if messages.error:
        raise ApplicationError('\n'.join(messages.error))


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


def write_json_test_results(category, name, content):  # type: (ResultType, str, t.Union[t.List[t.Any], t.Dict[str, t.Any]]) -> None
    """Write the given json content to the specified test results path, creating directories as needed."""
    path = os.path.join(category.path, name)
    write_json_file(path, content, create_directories=True)


def write_text_test_results(category, name, content):  # type: (ResultType, str, str) -> None
    """Write the given text content to the specified test results path, creating directories as needed."""
    path = os.path.join(category.path, name)
    write_text_file(path, content, create_directories=True)


def write_json_file(path, content, create_directories=False):  # type: (str, t.Union[t.List[t.Any], t.Dict[str, t.Any]], bool) -> None
    """Write the given json content to the specified path, optionally creating missing directories."""
    text_content = json.dumps(content, sort_keys=True, indent=4) + '\n'
    write_text_file(path, text_content, create_directories=create_directories)


def write_text_file(path, content, create_directories=False):  # type: (str, str, bool) -> None
    """Write the given text content to the specified path, optionally creating missing directories."""
    if create_directories:
        make_dirs(os.path.dirname(path))

    with open(to_bytes(path), 'wb') as file:
        file.write(to_bytes(content))


def get_python_path(args, interpreter):
    """
    :type args: TestConfig
    :type interpreter: str
    :rtype: str
    """
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

        create_interpreter_wrapper(interpreter, injected_interpreter)

    os.chmod(python_path, MODE_DIRECTORY)

    if not PYTHON_PATHS:
        atexit.register(cleanup_python_paths)

    PYTHON_PATHS[interpreter] = python_path

    return python_path


def create_temp_dir(prefix=None, suffix=None, base_dir=None):  # type: (t.Optional[str], t.Optional[str], t.Optional[str]) -> str
    """Create a temporary directory that persists until the current process exits."""
    temp_path = tempfile.mkdtemp(prefix=prefix or 'tmp', suffix=suffix or '', dir=base_dir)
    atexit.register(remove_tree, temp_path)
    return temp_path


def create_interpreter_wrapper(interpreter, injected_interpreter):  # type: (str, str) -> None
    """Create a wrapper for the given Python interpreter at the specified path."""
    # sys.executable is used for the shebang to guarantee it is a binary instead of a script
    # injected_interpreter could be a script from the system or our own wrapper created for the --venv option
    shebang_interpreter = sys.executable

    code = textwrap.dedent('''
    #!%s

    from __future__ import absolute_import

    from os import execv
    from sys import argv

    python = '%s'

    execv(python, [python] + argv[1:])
    ''' % (shebang_interpreter, interpreter)).lstrip()

    write_text_file(injected_interpreter, code)

    os.chmod(injected_interpreter, MODE_FILE_EXECUTE)


def cleanup_python_paths():
    """Clean up all temporary python directories."""
    for path in sorted(PYTHON_PATHS.values()):
        display.info('Cleaning up temporary python directory: %s' % path, verbosity=2)
        shutil.rmtree(path)


def get_coverage_environment(args, target_name, version, temp_path, module_coverage, remote_temp_path=None):
    """
    :type args: TestConfig
    :type target_name: str
    :type version: str
    :type temp_path: str
    :type module_coverage: bool
    :type remote_temp_path: str | None
    :rtype: dict[str, str]
    """
    if temp_path:
        # integration tests (both localhost and the optional testhost)
        # config and results are in a temporary directory
        coverage_config_base_path = temp_path
        coverage_output_base_path = temp_path
    elif args.coverage_config_base_path:
        # unit tests, sanity tests and other special cases (localhost only)
        # config is in a temporary directory
        # results are in the source tree
        coverage_config_base_path = args.coverage_config_base_path
        coverage_output_base_path = os.path.join(data_context().content.root, data_context().content.results_path)
    else:
        raise Exception('No temp path and no coverage config base path. Check for missing coverage_context usage.')

    config_file = os.path.join(coverage_config_base_path, COVERAGE_CONFIG_NAME)
    coverage_file = os.path.join(coverage_output_base_path, ResultType.COVERAGE.name, '%s=%s=%s=%s=coverage' % (
        args.command, target_name, args.coverage_label or 'local-%s' % version, 'python-%s' % version))

    if not args.explain and not os.path.exists(config_file):
        raise Exception('Missing coverage config file: %s' % config_file)

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

        if remote_temp_path:
            # Include the command, target and label so the remote host can create a filename with that info. The remote
            # is responsible for adding '={language version}=coverage.{hostname}.{pid}.{id}'
            env['_ANSIBLE_COVERAGE_REMOTE_OUTPUT'] = os.path.join(remote_temp_path, '%s=%s=%s' % (
                args.command, target_name, args.coverage_label or 'remote'))
            env['_ANSIBLE_COVERAGE_REMOTE_WHITELIST'] = os.path.join(data_context().content.root, '*')

    return env


def intercept_command(args, cmd, target_name, env, capture=False, data=None, cwd=None, python_version=None, temp_path=None, module_coverage=True,
                      virtualenv=None, disable_coverage=False, remote_temp_path=None):
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
    :type disable_coverage: bool
    :type remote_temp_path: str | None
    :rtype: str | None, str | None
    """
    if not env:
        env = common_environment()
    else:
        env = env.copy()

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

    if args.coverage and not disable_coverage:
        # add the necessary environment variables to enable code coverage collection
        env.update(get_coverage_environment(args, target_name, version, temp_path, module_coverage,
                                            remote_temp_path=remote_temp_path))

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
