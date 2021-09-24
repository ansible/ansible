"""Miscellaneous utility functions and classes."""
from __future__ import annotations

import errno
import fcntl
import inspect
import os
import pkgutil
import random
import re
import shutil
import socket
import stat
import string
import subprocess
import sys
import time
import functools
import shlex
import typing as t

from struct import unpack, pack
from termios import TIOCGWINSZ

from .encoding import (
    to_bytes,
    to_optional_bytes,
    to_optional_text,
)

from .io import (
    open_binary_file,
    read_text_file,
)

from .thread import (
    mutex,
)

from .constants import (
    SUPPORTED_PYTHON_VERSIONS,
)

C = t.TypeVar('C')
TType = t.TypeVar('TType')
TKey = t.TypeVar('TKey')
TValue = t.TypeVar('TValue')

PYTHON_PATHS = {}  # type: t.Dict[str, str]

try:
    # noinspection PyUnresolvedReferences
    MAXFD = subprocess.MAXFD
except AttributeError:
    MAXFD = -1

COVERAGE_CONFIG_NAME = 'coveragerc'

ANSIBLE_TEST_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# assume running from install
ANSIBLE_ROOT = os.path.dirname(ANSIBLE_TEST_ROOT)
ANSIBLE_BIN_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
ANSIBLE_LIB_ROOT = os.path.join(ANSIBLE_ROOT, 'ansible')
ANSIBLE_SOURCE_ROOT = None

if not os.path.exists(ANSIBLE_LIB_ROOT):
    # running from source
    ANSIBLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(ANSIBLE_TEST_ROOT)))
    ANSIBLE_BIN_PATH = os.path.join(ANSIBLE_ROOT, 'bin')
    ANSIBLE_LIB_ROOT = os.path.join(ANSIBLE_ROOT, 'lib', 'ansible')
    ANSIBLE_SOURCE_ROOT = ANSIBLE_ROOT

ANSIBLE_TEST_DATA_ROOT = os.path.join(ANSIBLE_TEST_ROOT, '_data')
ANSIBLE_TEST_UTIL_ROOT = os.path.join(ANSIBLE_TEST_ROOT, '_util')
ANSIBLE_TEST_CONFIG_ROOT = os.path.join(ANSIBLE_TEST_ROOT, 'config')

ANSIBLE_TEST_CONTROLLER_ROOT = os.path.join(ANSIBLE_TEST_UTIL_ROOT, 'controller')
ANSIBLE_TEST_TARGET_ROOT = os.path.join(ANSIBLE_TEST_UTIL_ROOT, 'target')

ANSIBLE_TEST_TOOLS_ROOT = os.path.join(ANSIBLE_TEST_CONTROLLER_ROOT, 'tools')

# Modes are set to allow all users the same level of access.
# This permits files to be used in tests that change users.
# The only exception is write access to directories for the user creating them.
# This avoids having to modify the directory permissions a second time.

MODE_READ = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH

MODE_FILE = MODE_READ
MODE_FILE_EXECUTE = MODE_FILE | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
MODE_FILE_WRITE = MODE_FILE | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH

MODE_DIRECTORY = MODE_READ | stat.S_IWUSR | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
MODE_DIRECTORY_WRITE = MODE_DIRECTORY | stat.S_IWGRP | stat.S_IWOTH


def cache(func):  # type: (t.Callable[[], TValue]) -> t.Callable[[], TValue]
    """Enforce exclusive access on a decorated function and cache the result."""
    storage = {}  # type: t.Dict[None, TValue]
    sentinel = object()

    @functools.wraps(func)
    def cache_func():
        """Cache the return value from func."""
        if (value := storage.get(None, sentinel)) is sentinel:
            value = storage[None] = func()

        return value

    wrapper = mutex(cache_func)

    return wrapper


def filter_args(args, filters):  # type: (t.List[str], t.Dict[str, int]) -> t.List[str]
    """Return a filtered version of the given command line arguments."""
    remaining = 0
    result = []

    for arg in args:
        if not arg.startswith('-') and remaining:
            remaining -= 1
            continue

        remaining = 0

        parts = arg.split('=', 1)
        key = parts[0]

        if key in filters:
            remaining = filters[key] - len(parts) + 1
            continue

        result.append(arg)

    return result


def read_lines_without_comments(path, remove_blank_lines=False, optional=False):  # type: (str, bool, bool) -> t.List[str]
    """
    Returns lines from the specified text file with comments removed.
    Comments are any content from a hash symbol to the end of a line.
    Any spaces immediately before a comment are also removed.
    """
    if optional and not os.path.exists(path):
        return []

    lines = read_text_file(path).splitlines()

    lines = [re.sub(r' *#.*$', '', line) for line in lines]

    if remove_blank_lines:
        lines = [line for line in lines if line]

    return lines


def exclude_none_values(data):  # type: (t.Dict[TKey, t.Optional[TValue]]) -> t.Dict[TKey, TValue]
    """Return the provided dictionary with any None values excluded."""
    return dict((key, value) for key, value in data.items() if value is not None)


def find_executable(executable, cwd=None, path=None, required=True):  # type: (str, t.Optional[str], t.Optional[str], t.Union[bool, str]) -> t.Optional[str]
    """
    Find the specified executable and return the full path, or None if it could not be found.
    If required is True an exception will be raised if the executable is not found.
    If required is set to 'warning' then a warning will be shown if the executable is not found.
    """
    match = None
    real_cwd = os.getcwd()

    if not cwd:
        cwd = real_cwd

    if os.path.dirname(executable):
        target = os.path.join(cwd, executable)
        if os.path.exists(target) and os.access(target, os.F_OK | os.X_OK):
            match = executable
    else:
        if path is None:
            path = os.environ.get('PATH', os.path.defpath)

        if path:
            path_dirs = path.split(os.path.pathsep)
            seen_dirs = set()

            for path_dir in path_dirs:
                if path_dir in seen_dirs:
                    continue

                seen_dirs.add(path_dir)

                if os.path.abspath(path_dir) == real_cwd:
                    path_dir = cwd

                candidate = os.path.join(path_dir, executable)

                if os.path.exists(candidate) and os.access(candidate, os.F_OK | os.X_OK):
                    match = candidate
                    break

    if not match and required:
        message = 'Required program "%s" not found.' % executable

        if required != 'warning':
            raise ApplicationError(message)

        display.warning(message)

    return match


def find_python(version, path=None, required=True):  # type: (str, t.Optional[str], bool) -> t.Optional[str]
    """
    Find and return the full path to the specified Python version.
    If required, an exception will be raised not found.
    If not required, None will be returned if not found.
    """
    version_info = str_to_version(version)

    if not path and version_info == sys.version_info[:len(version_info)]:
        python_bin = sys.executable
    else:
        python_bin = find_executable('python%s' % version, path=path, required=required)

    return python_bin


@cache
def get_ansible_version():  # type: () -> str
    """Return the Ansible version."""
    # ansible may not be in our sys.path
    # avoids a symlink to release.py since ansible placement relative to ansible-test may change during delegation
    load_module(os.path.join(ANSIBLE_LIB_ROOT, 'release.py'), 'ansible_release')

    # noinspection PyUnresolvedReferences
    from ansible_release import __version__ as ansible_version  # pylint: disable=import-error

    return ansible_version


@cache
def get_available_python_versions():  # type: () -> t.Dict[str, str]
    """Return a dictionary indicating which supported Python versions are available."""
    return dict((version, path) for version, path in ((version, find_python(version, required=False)) for version in SUPPORTED_PYTHON_VERSIONS) if path)


def raw_command(
        cmd,  # type: t.Iterable[str]
        capture=False,  # type: bool
        env=None,  # type: t.Optional[t.Dict[str, str]]
        data=None,  # type: t.Optional[str]
        cwd=None,  # type: t.Optional[str]
        explain=False,  # type: bool
        stdin=None,  # type: t.Optional[t.BinaryIO]
        stdout=None,  # type: t.Optional[t.BinaryIO]
        cmd_verbosity=1,  # type: int
        str_errors='strict',  # type: str
        error_callback=None,  # type: t.Optional[t.Callable[[SubprocessError], None]]
):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
    """Run the specified command and return stdout and stderr as a tuple."""
    if not cwd:
        cwd = os.getcwd()

    if not env:
        env = common_environment()

    cmd = list(cmd)

    escaped_cmd = ' '.join(shlex.quote(c) for c in cmd)

    display.info('Run command: %s' % escaped_cmd, verbosity=cmd_verbosity, truncate=True)
    display.info('Working directory: %s' % cwd, verbosity=2)

    program = find_executable(cmd[0], cwd=cwd, path=env['PATH'], required='warning')

    if program:
        display.info('Program found: %s' % program, verbosity=2)

    for key in sorted(env.keys()):
        display.info('%s=%s' % (key, env[key]), verbosity=2)

    if explain:
        return None, None

    communicate = False

    if stdin is not None:
        data = None
        communicate = True
    elif data is not None:
        stdin = subprocess.PIPE
        communicate = True

    if stdout:
        communicate = True

    if capture:
        stdout = stdout or subprocess.PIPE
        stderr = subprocess.PIPE
        communicate = True
    else:
        stderr = None

    start = time.time()
    process = None

    try:
        try:
            cmd_bytes = [to_bytes(c) for c in cmd]
            env_bytes = dict((to_bytes(k), to_bytes(v)) for k, v in env.items())
            process = subprocess.Popen(cmd_bytes, env=env_bytes, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)  # pylint: disable=consider-using-with
        except OSError as ex:
            if ex.errno == errno.ENOENT:
                raise ApplicationError('Required program "%s" not found.' % cmd[0])
            raise

        if communicate:
            data_bytes = to_optional_bytes(data)
            stdout_bytes, stderr_bytes = process.communicate(data_bytes)
            stdout_text = to_optional_text(stdout_bytes, str_errors) or u''
            stderr_text = to_optional_text(stderr_bytes, str_errors) or u''
        else:
            process.wait()
            stdout_text, stderr_text = None, None
    finally:
        if process and process.returncode is None:
            process.kill()
            display.info('')  # the process we're interrupting may have completed a partial line of output
            display.notice('Killed command to avoid an orphaned child process during handling of an unexpected exception.')

    status = process.returncode
    runtime = time.time() - start

    display.info('Command exited with status %s after %s seconds.' % (status, runtime), verbosity=4)

    if status == 0:
        return stdout_text, stderr_text

    raise SubprocessError(cmd, status, stdout_text, stderr_text, runtime, error_callback)


def common_environment():
    """Common environment used for executing all programs."""
    env = dict(
        LC_ALL='en_US.UTF-8',
        PATH=os.environ.get('PATH', os.path.defpath),
    )

    required = (
        'HOME',
    )

    optional = (
        'LD_LIBRARY_PATH',
        'SSH_AUTH_SOCK',
        # MacOS High Sierra Compatibility
        # http://sealiesoftware.com/blog/archive/2017/6/5/Objective-C_and_fork_in_macOS_1013.html
        # Example configuration for macOS:
        # export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
        'OBJC_DISABLE_INITIALIZE_FORK_SAFETY',
        'ANSIBLE_KEEP_REMOTE_FILES',
        # MacOS Homebrew Compatibility
        # https://cryptography.io/en/latest/installation/#building-cryptography-on-macos
        # This may also be required to install pyyaml with libyaml support when installed in non-standard locations.
        # Example configuration for brew on macOS:
        # export LDFLAGS="-L$(brew --prefix openssl)/lib/     -L$(brew --prefix libyaml)/lib/"
        # export  CFLAGS="-I$(brew --prefix openssl)/include/ -I$(brew --prefix libyaml)/include/"
        # However, this is not adequate for PyYAML 3.13, which is the latest version supported on Python 2.6.
        # For that version the standard location must be used, or `pip install` must be invoked with additional options:
        # --global-option=build_ext --global-option=-L{path_to_lib_dir}
        'LDFLAGS',
        'CFLAGS',
    )

    # FreeBSD Compatibility
    # This is required to include libyaml support in PyYAML.
    # The header /usr/local/include/yaml.h isn't in the default include path for the compiler.
    # It is included here so that tests can take advantage of it, rather than only ansible-test during managed pip installs.
    # If CFLAGS has been set in the environment that value will take precedence due to being an optional var when calling pass_vars.
    if os.path.exists('/etc/freebsd-update.conf'):
        env.update(CFLAGS='-I/usr/local/include/')

    env.update(pass_vars(required=required, optional=optional))

    return env


def pass_vars(required, optional):  # type: (t.Collection[str], t.Collection[str]) -> t.Dict[str, str]
    """Return a filtered dictionary of environment variables based on the current environment."""
    env = {}

    for name in required:
        if name not in os.environ:
            raise MissingEnvironmentVariable(name)
        env[name] = os.environ[name]

    for name in optional:
        if name not in os.environ:
            continue
        env[name] = os.environ[name]

    return env


def remove_tree(path):  # type: (str) -> None
    """Remove the specified directory, siliently continuing if the directory does not exist."""
    try:
        shutil.rmtree(to_bytes(path))
    except OSError as ex:
        if ex.errno != errno.ENOENT:
            raise


def is_binary_file(path):  # type: (str) -> bool
    """Return True if the specified file is a binary file, otherwise return False."""
    assume_text = {
        '.cfg',
        '.conf',
        '.crt',
        '.cs',
        '.css',
        '.html',
        '.ini',
        '.j2',
        '.js',
        '.json',
        '.md',
        '.pem',
        '.ps1',
        '.psm1',
        '.py',
        '.rst',
        '.sh',
        '.txt',
        '.xml',
        '.yaml',
        '.yml',
    }

    assume_binary = {
        '.bin',
        '.eot',
        '.gz',
        '.ico',
        '.iso',
        '.jpg',
        '.otf',
        '.p12',
        '.png',
        '.pyc',
        '.rpm',
        '.ttf',
        '.woff',
        '.woff2',
        '.zip',
    }

    ext = os.path.splitext(path)[1]

    if ext in assume_text:
        return False

    if ext in assume_binary:
        return True

    with open_binary_file(path) as path_fd:
        # noinspection PyTypeChecker
        return b'\0' in path_fd.read(4096)


def generate_name(length=8):  # type: (int) -> str
    """Generate and return a random name."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _idx in range(length))


def generate_password():  # type: () -> str
    """Generate and return random password."""
    chars = [
        string.ascii_letters,
        string.digits,
        string.ascii_letters,
        string.digits,
        '-',
    ] * 4

    password = ''.join([random.choice(char) for char in chars[:-1]])

    display.sensitive.add(password)

    return password


class Display:
    """Manages color console output."""
    clear = '\033[0m'
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    purple = '\033[35m'
    cyan = '\033[36m'

    verbosity_colors = {
        0: None,
        1: green,
        2: blue,
        3: cyan,
    }

    def __init__(self):
        self.verbosity = 0
        self.color = sys.stdout.isatty()
        self.warnings = []
        self.warnings_unique = set()
        self.info_stderr = False
        self.rows = 0
        self.columns = 0
        self.truncate = 0
        self.redact = True
        self.sensitive = set()

        if os.isatty(0):
            self.rows, self.columns = unpack('HHHH', fcntl.ioctl(0, TIOCGWINSZ, pack('HHHH', 0, 0, 0, 0)))[:2]

    def __warning(self, message):  # type: (str) -> None
        """Internal implementation for displaying a warning message."""
        self.print_message('WARNING: %s' % message, color=self.purple, fd=sys.stderr)

    def review_warnings(self):  # type: () -> None
        """Review all warnings which previously occurred."""
        if not self.warnings:
            return

        self.__warning('Reviewing previous %d warning(s):' % len(self.warnings))

        for warning in self.warnings:
            self.__warning(warning)

    def warning(self, message, unique=False, verbosity=0):  # type: (str, bool, int) -> None
        """Display a warning level message."""
        if verbosity > self.verbosity:
            return

        if unique:
            if message in self.warnings_unique:
                return

            self.warnings_unique.add(message)

        self.__warning(message)
        self.warnings.append(message)

    def notice(self, message):  # type: (str) -> None
        """Display a notice level message."""
        self.print_message('NOTICE: %s' % message, color=self.purple, fd=sys.stderr)

    def error(self, message):  # type: (str) -> None
        """Display an error level message."""
        self.print_message('ERROR: %s' % message, color=self.red, fd=sys.stderr)

    def info(self, message, verbosity=0, truncate=False):  # type: (str, int, bool) -> None
        """Display an info level message."""
        if self.verbosity >= verbosity:
            color = self.verbosity_colors.get(verbosity, self.yellow)
            self.print_message(message, color=color, fd=sys.stderr if self.info_stderr else sys.stdout, truncate=truncate)

    def print_message(  # pylint: disable=locally-disabled, invalid-name
            self,
            message,  # type: str
            color=None,  # type: t.Optional[str]
            fd=sys.stdout,  # type: t.TextIO
            truncate=False,  # type: bool
    ):  # type: (...) -> None
        """Display a message."""
        if self.redact and self.sensitive:
            for item in self.sensitive:
                if not item:
                    continue

                message = message.replace(item, '*' * len(item))

        if truncate:
            if len(message) > self.truncate > 5:
                message = message[:self.truncate - 5] + ' ...'

        if color and self.color:
            # convert color resets in message to desired color
            message = message.replace(self.clear, color)
            message = '%s%s%s' % (color, message, self.clear)

        if sys.version_info[0] == 2:
            message = to_bytes(message)

        print(message, file=fd)
        fd.flush()


class ApplicationError(Exception):
    """General application error."""


class ApplicationWarning(Exception):
    """General application warning which interrupts normal program flow."""


class SubprocessError(ApplicationError):
    """Error resulting from failed subprocess execution."""
    def __init__(
            self,
            cmd,  # type: t.List[str]
            status=0,  # type: int
            stdout=None,  # type: t.Optional[str]
            stderr=None,  # type: t.Optional[str]
            runtime=None,  # type: t.Optional[float]
            error_callback=None,  # type: t.Optional[t.Callable[[SubprocessError], None]]
    ):  # type: (...) -> None
        message = 'Command "%s" returned exit status %s.\n' % (' '.join(shlex.quote(c) for c in cmd), status)

        if stderr:
            message += '>>> Standard Error\n'
            message += '%s%s\n' % (stderr.strip(), Display.clear)

        if stdout:
            message += '>>> Standard Output\n'
            message += '%s%s\n' % (stdout.strip(), Display.clear)

        self.cmd = cmd
        self.message = message
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.runtime = runtime

        if error_callback:
            error_callback(self)

        self.message = self.message.strip()

        super().__init__(self.message)


class MissingEnvironmentVariable(ApplicationError):
    """Error caused by missing environment variable."""
    def __init__(self, name):  # type: (str) -> None
        super().__init__('Missing environment variable: %s' % name)

        self.name = name


def retry(func, ex_type=SubprocessError, sleep=10, attempts=10):
    """Retry the specified function on failure."""
    for dummy in range(1, attempts):
        try:
            return func()
        except ex_type:
            time.sleep(sleep)

    return func()


def parse_to_list_of_dict(pattern, value):  # type: (str, str) -> t.List[t.Dict[str, str]]
    """Parse lines from the given value using the specified pattern and return the extracted list of key/value pair dictionaries."""
    matched = []
    unmatched = []

    for line in value.splitlines():
        match = re.search(pattern, line)

        if match:
            matched.append(match.groupdict())
        else:
            unmatched.append(line)

    if unmatched:
        raise Exception('Pattern "%s" did not match values:\n%s' % (pattern, '\n'.join(unmatched)))

    return matched


def get_subclasses(class_type):  # type: (t.Type[C]) -> t.List[t.Type[C]]
    """Returns a list of types that are concrete subclasses of the given type."""
    subclasses = set()  # type: t.Set[t.Type[C]]
    queue = [class_type]  # type: t.List[t.Type[C]]

    while queue:
        parent = queue.pop()

        for child in parent.__subclasses__():
            if child not in subclasses:
                if not inspect.isabstract(child):
                    subclasses.add(child)
                queue.append(child)

    return sorted(subclasses, key=lambda sc: sc.__name__)


def is_subdir(candidate_path, path):  # type: (str, str) -> bool
    """Returns true if candidate_path is path or a subdirectory of path."""
    if not path.endswith(os.path.sep):
        path += os.path.sep

    if not candidate_path.endswith(os.path.sep):
        candidate_path += os.path.sep

    return candidate_path.startswith(path)


def paths_to_dirs(paths):  # type: (t.List[str]) -> t.List[str]
    """Returns a list of directories extracted from the given list of paths."""
    dir_names = set()

    for path in paths:
        while True:
            path = os.path.dirname(path)

            if not path or path == os.path.sep:
                break

            dir_names.add(path + os.path.sep)

    return sorted(dir_names)


def str_to_version(version):  # type: (str) -> t.Tuple[int, ...]
    """Return a version tuple from a version string."""
    return tuple(int(n) for n in version.split('.'))


def version_to_str(version):  # type: (t.Tuple[int, ...]) -> str
    """Return a version string from a version tuple."""
    return '.'.join(str(n) for n in version)


def sorted_versions(versions):  # type: (t.List[str]) -> t.List[str]
    """Return a sorted copy of the given list of versions."""
    return [version_to_str(version) for version in sorted(str_to_version(version) for version in versions)]


def import_plugins(directory, root=None):  # type: (str, t.Optional[str]) -> None
    """
    Import plugins from the given directory relative to the given root.
    If the root is not provided, the 'lib' directory for the test runner will be used.
    """
    if root is None:
        root = os.path.dirname(__file__)

    path = os.path.join(root, directory)
    package = __name__.rsplit('.', 1)[0]
    prefix = '%s.%s.' % (package, directory.replace(os.path.sep, '.'))

    for (_module_loader, name, _ispkg) in pkgutil.iter_modules([path], prefix=prefix):
        module_path = os.path.join(root, name[len(package) + 1:].replace('.', os.path.sep) + '.py')
        load_module(module_path, name)


def load_plugins(base_type, database):  # type: (t.Type[C], t.Dict[str, t.Type[C]]) -> None
    """
    Load plugins of the specified type and track them in the specified database.
    Only plugins which have already been imported will be loaded.
    """
    plugins = dict((sc.__module__.rsplit('.', 1)[1], sc) for sc in get_subclasses(base_type))  # type: t.Dict[str, t.Type[C]]

    for plugin in plugins:
        database[plugin] = plugins[plugin]


def load_module(path, name):  # type: (str, str) -> None
    """Load a Python module using the given name and path."""
    if name in sys.modules:
        return

    if sys.version_info >= (3, 4):
        import importlib.util

        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        # noinspection PyUnresolvedReferences
        spec.loader.exec_module(module)

        sys.modules[name] = module
    else:
        # noinspection PyDeprecation
        import imp  # pylint: disable=deprecated-module

        # load_source (and thus load_module) require a file opened with `open` in text mode
        with open(to_bytes(path)) as module_file:
            # noinspection PyDeprecation
            imp.load_module(name, module_file, path, ('.py', 'r', imp.PY_SOURCE))


def sanitize_host_name(name):
    """Return a sanitized version of the given name, suitable for use as a hostname."""
    return re.sub('[^A-Za-z0-9]+', '-', name)[:63].strip('-')


@cache
def get_host_ip():
    """Return the host's IP address."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(('10.255.255.255', 22))
        host_ip = get_host_ip.ip = sock.getsockname()[0]

    display.info('Detected host IP: %s' % host_ip, verbosity=1)

    return host_ip


def get_generic_type(base_type, generic_base_type):  # type: (t.Type, t.Type[TType]) -> t.Optional[t.Type[TType]]
    """Return the generic type arg derived from the generic_base_type type that is associated with the base_type type, if any, otherwise return None."""
    # noinspection PyUnresolvedReferences
    type_arg = t.get_args(base_type.__orig_bases__[0])[0]
    return None if isinstance(type_arg, generic_base_type) else type_arg


def get_type_associations(base_type, generic_base_type):  # type: (t.Type[TType], t.Type[TValue]) -> t.List[t.Tuple[t.Type[TValue], t.Type[TType]]]
    """Create and return a list of tuples associating generic_base_type derived types with a corresponding base_type derived type."""
    return [item for item in [(get_generic_type(sc_type, generic_base_type), sc_type) for sc_type in get_subclasses(base_type)] if item[1]]


def get_type_map(base_type, generic_base_type):  # type: (t.Type[TType], t.Type[TValue]) -> t.Dict[t.Type[TValue], t.Type[TType]]
    """Create and return a mapping of generic_base_type derived types to base_type derived types."""
    return {item[0]: item[1] for item in get_type_associations(base_type, generic_base_type)}


def verify_sys_executable(path):  # type: (str) -> t.Optional[str]
    """Verify that the given path references the current Python interpreter. If not, return the expected path, otherwise return None."""
    if path == sys.executable:
        return None

    if os.path.realpath(path) == os.path.realpath(sys.executable):
        return None

    expected_executable = raw_command([path, '-c', 'import sys; print(sys.executable)'], capture=True)[0]

    if expected_executable == sys.executable:
        return None

    return expected_executable


display = Display()  # pylint: disable=locally-disabled, invalid-name
