"""Miscellaneous utility functions and classes."""

from __future__ import absolute_import, print_function

import errno
import os
import pipes
import shutil
import subprocess
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


def run_command(args, cmd, capture=False, env=None, data=None, cwd=None, always=False, stdin=None, stdout=None):
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
    :rtype: str | None, str | None
    """
    explain = args.explain and not always
    return raw_command(cmd, capture=capture, env=env, data=data, cwd=cwd, explain=explain, stdin=stdin, stdout=stdout)


def raw_command(cmd, capture=False, env=None, data=None, cwd=None, explain=False, stdin=None, stdout=None):
    """
    :type cmd: collections.Iterable[str]
    :type capture: bool
    :type env: dict[str, str] | None
    :type data: str | None
    :type cwd: str | None
    :type explain: bool
    :type stdin: file | None
    :type stdout: file | None
    :rtype: str | None, str | None
    """
    if not cwd:
        cwd = os.getcwd()

    if not env:
        env = common_environment()

    cmd = list(cmd)

    escaped_cmd = ' '.join(pipes.quote(c) for c in cmd)

    display.info('Run command: %s' % escaped_cmd, verbosity=1)
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
        stdout, stderr = process.communicate(data)
    else:
        process.wait()
        stdout, stderr = None, None

    status = process.returncode
    runtime = time.time() - start

    display.info('Command exited with status %s after %s seconds.' % (status, runtime), verbosity=4)

    if status == 0:
        return stdout, stderr

    raise SubprocessError(cmd, status, stdout, stderr, runtime)


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
        'SSH_AUTH_SOCK'
    )

    env.update(pass_vars(required=required, optional=optional))

    return env


def pass_vars(required=None, optional=None):
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
    :return: str | None
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

    def warning(self, message):
        """
        :type message: str
        """
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
            self.print_message(message, color=color)

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
    def __init__(self, message=None):
        """
        :type message: str | None
        """
        super(ApplicationError, self).__init__(message)


class ApplicationWarning(Exception):
    """General application warning which interrupts normal program flow."""
    def __init__(self, message=None):
        """
        :type message: str | None
        """
        super(ApplicationWarning, self).__init__(message)


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


display = Display()  # pylint: disable=locally-disabled, invalid-name
