"""Miscellaneous utility functions and classes."""

from __future__ import absolute_import, print_function

import errno
import os
import pipes
import pkgutil
import shutil
import subprocess
import re
import sys
import time


def is_shippable():
    """
    :rtype: bool
    """
    return os.environ.get('SHIPPABLE') == 'true'


def remove_file(path):
    """
    :type path: str
    """
    if os.path.isfile(path):
        os.remove(path)


def find_executable(executable, cwd=None, path=None, required=True):
    """
    :type executable: str
    :type cwd: str
    :type path: str
    :type required: bool | str
    :rtype: str | None
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
            path = os.environ.get('PATH', os.defpath)

        if path:
            path_dirs = path.split(os.pathsep)
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


def raw_command(cmd, capture=False, env=None, data=None, cwd=None, explain=False, stdin=None, stdout=None,
                cmd_verbosity=1, str_errors='strict'):
    """
    :type cmd: collections.Iterable[str]
    :type capture: bool
    :type env: dict[str, str] | None
    :type data: str | None
    :type cwd: str | None
    :type explain: bool
    :type stdin: file | None
    :type stdout: file | None
    :type cmd_verbosity: int
    :type str_errors: str
    :rtype: str | None, str | None
    """
    if not cwd:
        cwd = os.getcwd()

    if not env:
        env = common_environment()

    cmd = list(cmd)

    escaped_cmd = ' '.join(pipes.quote(c) for c in cmd)

    display.info('Run command: %s' % escaped_cmd, verbosity=cmd_verbosity)
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

    try:
        process = subprocess.Popen(cmd, env=env, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            raise ApplicationError('Required program "%s" not found.' % cmd[0])
        raise

    if communicate:
        encoding = 'utf-8'
        data_bytes = data.encode(encoding) if data else None
        stdout_bytes, stderr_bytes = process.communicate(data_bytes)
        stdout_text = stdout_bytes.decode(encoding, str_errors) if stdout_bytes else u''
        stderr_text = stderr_bytes.decode(encoding, str_errors) if stderr_bytes else u''
    else:
        process.wait()
        stdout_text, stderr_text = None, None

    status = process.returncode
    runtime = time.time() - start

    display.info('Command exited with status %s after %s seconds.' % (status, runtime), verbosity=4)

    if status == 0:
        return stdout_text, stderr_text

    raise SubprocessError(cmd, status, stdout_text, stderr_text, runtime)


def common_environment():
    """Common environment used for executing all programs."""
    env = dict(
        LC_ALL='en_US.UTF-8',
        PATH=os.environ.get('PATH', os.defpath),
    )

    required = (
        'HOME',
    )

    optional = (
        'HTTPTESTER',
        'LD_LIBRARY_PATH',
        'SSH_AUTH_SOCK',
    )

    env.update(pass_vars(required=required, optional=optional))

    return env


def pass_vars(required, optional):
    """
    :type required: collections.Iterable[str]
    :type optional: collections.Iterable[str]
    :rtype: dict[str, str]
    """
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


def deepest_path(path_a, path_b):
    """Return the deepest of two paths, or None if the paths are unrelated.
    :type path_a: str
    :type path_b: str
    :rtype: str | None
    """
    if path_a == '.':
        path_a = ''

    if path_b == '.':
        path_b = ''

    if path_a.startswith(path_b):
        return path_a or '.'

    if path_b.startswith(path_a):
        return path_b or '.'

    return None


def remove_tree(path):
    """
    :type path: str
    """
    try:
        shutil.rmtree(path)
    except OSError as ex:
        if ex.errno != errno.ENOENT:
            raise


def make_dirs(path):
    """
    :type path: str
    """
    try:
        os.makedirs(path)
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise


def is_binary_file(path):
    """
    :type path: str
    :rtype: bool
    """
    with open(path, 'rb') as path_fd:
        return b'\0' in path_fd.read(1024)


class Display(object):
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
        self.color = True
        self.warnings = []
        self.warnings_unique = set()
        self.info_stderr = False

    def __warning(self, message):
        """
        :type message: str
        """
        self.print_message('WARNING: %s' % message, color=self.purple, fd=sys.stderr)

    def review_warnings(self):
        """Review all warnings which previously occurred."""
        if not self.warnings:
            return

        self.__warning('Reviewing previous %d warning(s):' % len(self.warnings))

        for warning in self.warnings:
            self.__warning(warning)

    def warning(self, message, unique=False):
        """
        :type message: str
        :type unique: bool
        """
        if unique:
            if message in self.warnings_unique:
                return

            self.warnings_unique.add(message)

        self.__warning(message)
        self.warnings.append(message)

    def notice(self, message):
        """
        :type message: str
        """
        self.print_message('NOTICE: %s' % message, color=self.purple, fd=sys.stderr)

    def error(self, message):
        """
        :type message: str
        """
        self.print_message('ERROR: %s' % message, color=self.red, fd=sys.stderr)

    def info(self, message, verbosity=0):
        """
        :type message: str
        :type verbosity: int
        """
        if self.verbosity >= verbosity:
            color = self.verbosity_colors.get(verbosity, self.yellow)
            self.print_message(message, color=color, fd=sys.stderr if self.info_stderr else sys.stdout)

    def print_message(self, message, color=None, fd=sys.stdout):  # pylint: disable=locally-disabled, invalid-name
        """
        :type message: str
        :type color: str | None
        :type fd: file
        """
        if color and self.color:
            # convert color resets in message to desired color
            message = message.replace(self.clear, color)
            message = '%s%s%s' % (color, message, self.clear)

        print(message, file=fd)
        fd.flush()


class ApplicationError(Exception):
    """General application error."""
    pass


class ApplicationWarning(Exception):
    """General application warning which interrupts normal program flow."""
    pass


class SubprocessError(ApplicationError):
    """Error resulting from failed subprocess execution."""
    def __init__(self, cmd, status=0, stdout=None, stderr=None, runtime=None):
        """
        :type cmd: list[str]
        :type status: int
        :type stdout: str | None
        :type stderr: str | None
        :type runtime: float | None
        """
        message = 'Command "%s" returned exit status %s.\n' % (' '.join(pipes.quote(c) for c in cmd), status)

        if stderr:
            message += '>>> Standard Error\n'
            message += '%s%s\n' % (stderr.strip(), Display.clear)

        if stdout:
            message += '>>> Standard Output\n'
            message += '%s%s\n' % (stdout.strip(), Display.clear)

        message = message.strip()

        super(SubprocessError, self).__init__(message)

        self.cmd = cmd
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.runtime = runtime


class MissingEnvironmentVariable(ApplicationError):
    """Error caused by missing environment variable."""
    def __init__(self, name):
        """
        :type name: str
        """
        super(MissingEnvironmentVariable, self).__init__('Missing environment variable: %s' % name)

        self.name = name


class CommonConfig(object):
    """Configuration common to all commands."""
    def __init__(self, args):
        """
        :type args: any
        """
        self.color = args.color  # type: bool
        self.explain = args.explain  # type: bool
        self.verbosity = args.verbosity  # type: int
        self.debug = args.debug  # type: bool


def docker_qualify_image(name):
    """
    :type name: str
    :rtype: str
    """
    if not name or any((c in name) for c in ('/', ':')):
        return name

    return 'ansible/ansible:%s' % name


def parse_to_dict(pattern, value):
    """
    :type pattern: str
    :type value: str
    :return: dict[str, str]
    """
    match = re.search(pattern, value)

    if match is None:
        raise Exception('Pattern "%s" did not match value: %s' % (pattern, value))

    return match.groupdict()


def get_subclasses(class_type):
    """
    :type class_type: type
    :rtype: set[str]
    """
    subclasses = set()
    queue = [class_type]

    while queue:
        parent = queue.pop()

        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                queue.append(child)

    return subclasses


def import_plugins(directory):
    """
    :type directory: str
    """
    path = os.path.join(os.path.dirname(__file__), directory)
    prefix = 'lib.%s.' % directory

    for (_, name, _) in pkgutil.iter_modules([path], prefix=prefix):
        __import__(name)


def load_plugins(base_type, database):
    """
    :type base_type: type
    :type database: dict[str, type]
    """
    plugins = dict((sc.__module__.split('.')[2], sc) for sc in get_subclasses(base_type))  # type: dict [str, type]

    for plugin in plugins:
        database[plugin] = plugins[plugin]


display = Display()  # pylint: disable=locally-disabled, invalid-name
