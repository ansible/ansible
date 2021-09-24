"""Common utility code that depends on CommonConfig."""
from __future__ import annotations

import atexit
import contextlib
import json
import os
import re
import shlex
import sys
import tempfile
import textwrap
import typing as t

from .constants import (
    ANSIBLE_BIN_SYMLINK_MAP,
)

from .encoding import (
    to_bytes,
)

from .util import (
    cache,
    display,
    remove_tree,
    MODE_DIRECTORY,
    MODE_FILE_EXECUTE,
    MODE_FILE,
    PYTHON_PATHS,
    raw_command,
    ANSIBLE_TEST_DATA_ROOT,
    ANSIBLE_TEST_TARGET_ROOT,
    ANSIBLE_TEST_TOOLS_ROOT,
    ApplicationError,
    SubprocessError,
    generate_name,
)

from .io import (
    make_dirs,
    read_text_file,
    write_text_file,
    write_json_file,
)

from .data import (
    data_context,
)

from .provider.layout import (
    LayoutMessages,
)

from .host_configs import (
    PythonConfig,
    VirtualPythonConfig,
)

CHECK_YAML_VERSIONS = {}


class ShellScriptTemplate:
    """A simple substition template for shell scripts."""
    def __init__(self, template):  # type: (t.Text) -> None
        self.template = template

    def substitute(self, **kwargs):  # type: (t.Dict[str, t.Union[str, t.List[str]]]) -> str
        """Return a string templated with the given arguments."""
        kvp = dict((k, self.quote(v)) for k, v in kwargs.items())
        pattern = re.compile(r'#{(?P<name>[^}]+)}')
        value = pattern.sub(lambda match: kvp[match.group('name')], self.template)
        return value

    @staticmethod
    def quote(value):  # type: (t.Union[str, t.List[str]]) -> str
        """Return a shell quoted version of the given value."""
        if isinstance(value, list):
            return shlex.quote(' '.join(value))

        return shlex.quote(value)


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
    def __init__(self, args, command):  # type: (t.Any, str) -> None
        self.command = command
        self.success = None  # type: t.Optional[bool]

        self.color = args.color  # type: bool
        self.explain = args.explain  # type: bool
        self.verbosity = args.verbosity  # type: int
        self.debug = args.debug  # type: bool
        self.truncate = args.truncate  # type: int
        self.redact = args.redact  # type: bool

        self.info_stderr = False  # type: bool

        self.session_name = generate_name()

        self.cache = {}

    def get_ansible_config(self):  # type: () -> str
        """Return the path to the Ansible config for the given config."""
        return os.path.join(ANSIBLE_TEST_DATA_ROOT, 'ansible.cfg')


def create_result_directories(args):  # type: (CommonConfig) -> None
    """Create result directories."""
    if args.explain:
        return

    make_dirs(ResultType.COVERAGE.path)
    make_dirs(ResultType.DATA.path)


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


def process_scoped_temporary_file(args, prefix='ansible-test-', suffix=None):  # type: (CommonConfig, t.Optional[str], t.Optional[str]) -> str
    """Return the path to a temporary file that will be automatically removed when the process exits."""
    if args.explain:
        path = os.path.join(tempfile.gettempdir(), f'{prefix or tempfile.gettempprefix()}{generate_name()}{suffix or ""}')
    else:
        temp_fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        os.close(temp_fd)
        atexit.register(lambda: os.remove(path))

    return path


def process_scoped_temporary_directory(args, prefix='ansible-test-', suffix=None):  # type: (CommonConfig, t.Optional[str], t.Optional[str]) -> str
    """Return the path to a temporary directory that will be automatically removed when the process exits."""
    if args.explain:
        path = os.path.join(tempfile.gettempdir(), f'{prefix or tempfile.gettempprefix()}{generate_name()}{suffix or ""}')
    else:
        path = tempfile.mkdtemp(prefix=prefix, suffix=suffix)
        atexit.register(lambda: remove_tree(path))

    return path


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
        yield os.path.join(directory or '/tmp', '%stemp%s' % (prefix, suffix))
    else:
        with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, dir=directory) as tempfile_fd:
            tempfile_fd.write(to_bytes(content))
            tempfile_fd.flush()

            yield tempfile_fd.name


def write_json_test_results(category,  # type: ResultType
                            name,  # type: str
                            content,  # type: t.Union[t.List[t.Any], t.Dict[str, t.Any]]
                            formatted=True,  # type: bool
                            encoder=None,  # type: t.Optional[t.Callable[[t.Any], t.Any]]
                            ):  # type: (...) -> None
    """Write the given json content to the specified test results path, creating directories as needed."""
    path = os.path.join(category.path, name)
    write_json_file(path, content, create_directories=True, formatted=formatted, encoder=encoder)


def write_text_test_results(category, name, content):  # type: (ResultType, str, str) -> None
    """Write the given text content to the specified test results path, creating directories as needed."""
    path = os.path.join(category.path, name)
    write_text_file(path, content, create_directories=True)


@cache
def get_injector_path():  # type: () -> str
    """Return the path to a directory which contains a `python.py` executable and associated injector scripts."""
    injector_path = tempfile.mkdtemp(prefix='ansible-test-', suffix='-injector', dir='/tmp')

    display.info(f'Initializing "{injector_path}" as the temporary injector directory.', verbosity=1)

    injector_names = sorted(list(ANSIBLE_BIN_SYMLINK_MAP) + [
        'importer.py',
        'pytest',
    ])

    scripts = (
        ('python.py', '/usr/bin/env python', MODE_FILE_EXECUTE),
        ('virtualenv.sh', '/usr/bin/env bash', MODE_FILE),
    )

    source_path = os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'injector')

    for name in injector_names:
        os.symlink('python.py', os.path.join(injector_path, name))

    for name, shebang, mode in scripts:
        src = os.path.join(source_path, name)
        dst = os.path.join(injector_path, name)

        script = read_text_file(src)
        script = set_shebang(script, shebang)

        write_text_file(dst, script)
        os.chmod(dst, mode)

    os.chmod(injector_path, MODE_DIRECTORY)

    def cleanup_injector():
        """Remove the temporary injector directory."""
        remove_tree(injector_path)

    atexit.register(cleanup_injector)

    return injector_path


def set_shebang(script, executable):  # type: (str, str) -> str
    """Return the given script with the specified executable used for the shebang."""
    prefix = '#!'
    shebang = prefix + executable

    overwrite = (
        prefix,
        '# auto-shebang',
        '# shellcheck shell=',
    )

    lines = script.splitlines()

    if any(lines[0].startswith(value) for value in overwrite):
        lines[0] = shebang
    else:
        lines.insert(0, shebang)

    script = '\n'.join(lines)

    return script


def get_python_path(interpreter):  # type: (str) -> str
    """Return the path to a directory which contains a `python` executable that runs the specified interpreter."""
    python_path = PYTHON_PATHS.get(interpreter)

    if python_path:
        return python_path

    prefix = 'python-'
    suffix = '-ansible'

    root_temp_dir = '/tmp'

    python_path = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=root_temp_dir)
    injected_interpreter = os.path.join(python_path, 'python')

    # A symlink is faster than the execv wrapper, but isn't guaranteed to provide the correct result.
    # There are several scenarios known not to work with symlinks:
    #
    # - A virtual environment where the target is a symlink to another directory.
    # - A pyenv environment where the target is a shell script that changes behavior based on the program name.
    #
    # To avoid issues for these and other scenarios, only an exec wrapper is used.

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
        remove_tree(path)


def intercept_python(
        args,  # type: CommonConfig
        python,  # type: PythonConfig
        cmd,  # type: t.List[str]
        env,  # type: t.Dict[str, str]
        capture=False,  # type: bool
        data=None,  # type: t.Optional[str]
        cwd=None,  # type: t.Optional[str]
        always=False,  # type: bool
):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
    """
    Run a command while intercepting invocations of Python to control the version used.
    If the specified Python is an ansible-test managed virtual environment, it will be added to PATH to activate it.
    Otherwise a temporary directory will be created to ensure the correct Python can be found in PATH.
    """
    env = env.copy()
    cmd = list(cmd)
    inject_path = get_injector_path()

    # make sure scripts (including injector.py) find the correct Python interpreter
    if isinstance(python, VirtualPythonConfig):
        python_path = os.path.dirname(python.path)
    else:
        python_path = get_python_path(python.path)

    env['PATH'] = os.path.pathsep.join([inject_path, python_path, env['PATH']])
    env['ANSIBLE_TEST_PYTHON_VERSION'] = python.version
    env['ANSIBLE_TEST_PYTHON_INTERPRETER'] = python.path

    return run_command(args, cmd, capture=capture, env=env, data=data, cwd=cwd, always=always)


def run_command(
        args,  # type: CommonConfig
        cmd,  # type: t.Iterable[str]
        capture=False,  # type: bool
        env=None,  # type: t.Optional[t.Dict[str, str]]
        data=None,  # type: t.Optional[str]
        cwd=None,  # type: t.Optional[str]
        always=False,  # type: bool
        stdin=None,  # type: t.Optional[t.BinaryIO]
        stdout=None,  # type: t.Optional[t.BinaryIO]
        cmd_verbosity=1,  # type: int
        str_errors='strict',  # type: str
        error_callback=None,  # type: t.Optional[t.Callable[[SubprocessError], None]]
):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
    """Run the specified command and return stdout and stderr as a tuple."""
    explain = args.explain and not always
    return raw_command(cmd, capture=capture, env=env, data=data, cwd=cwd, explain=explain, stdin=stdin, stdout=stdout,
                       cmd_verbosity=cmd_verbosity, str_errors=str_errors, error_callback=error_callback)


def yamlcheck(python):
    """Return True if PyYAML has libyaml support, False if it does not and None if it was not found."""
    result = json.loads(raw_command([python.path, os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'yamlcheck.py')], capture=True)[0])

    if not result['yaml']:
        return None

    return result['cloader']


def check_pyyaml(python, required=True, quiet=False):  # type: (PythonConfig, bool, bool) -> t.Optional[bool]
    """
    Return True if PyYAML has libyaml support, False if it does not and None if it was not found.
    The result is cached if True or required.
    """
    try:
        return CHECK_YAML_VERSIONS[python.path]
    except KeyError:
        pass

    state = yamlcheck(python)

    if state is not None or required:
        # results are cached only if pyyaml is required or present
        # it is assumed that tests will not uninstall/re-install pyyaml -- if they do, those changes will go undetected
        CHECK_YAML_VERSIONS[python.path] = state

    if not quiet:
        if state is None:
            if required:
                display.warning('PyYAML is not installed for interpreter: %s' % python.path)
        elif not state:
            display.warning('PyYAML will be slow due to installation without libyaml support for interpreter: %s' % python.path)

    return state
