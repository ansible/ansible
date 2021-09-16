"""A tool for installing test requirements on the controller and target host."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# pylint: disable=wrong-import-position

import resource

# Setting a low soft RLIMIT_NOFILE value will improve the performance of subprocess.Popen on Python 2.x when close_fds=True.
# This will affect all Python subprocesses. It will also affect the current Python process if set before subprocess is imported for the first time.
SOFT_RLIMIT_NOFILE = 1024

CURRENT_RLIMIT_NOFILE = resource.getrlimit(resource.RLIMIT_NOFILE)
DESIRED_RLIMIT_NOFILE = (SOFT_RLIMIT_NOFILE, CURRENT_RLIMIT_NOFILE[1])

if DESIRED_RLIMIT_NOFILE < CURRENT_RLIMIT_NOFILE:
    resource.setrlimit(resource.RLIMIT_NOFILE, DESIRED_RLIMIT_NOFILE)
    CURRENT_RLIMIT_NOFILE = DESIRED_RLIMIT_NOFILE

import base64
import errno
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import typing as t
except ImportError:
    t = None

try:
    from shlex import quote as cmd_quote
except ImportError:
    # noinspection PyProtectedMember
    from pipes import quote as cmd_quote

ENCODING = 'utf-8'
PAYLOAD = b'{payload}'  # base-64 encoded JSON payload which will be populated before this script is executed

Text = type(u'')

VERBOSITY = 0
CONSOLE = sys.stderr


def main():  # type: () -> None
    """Main program entry point."""
    global VERBOSITY  # pylint: disable=global-statement

    payload = json.loads(to_text(base64.b64decode(PAYLOAD)))

    VERBOSITY = payload['verbosity']

    script = payload['script']
    commands = payload['commands']

    with tempfile.NamedTemporaryFile(prefix='ansible-test-', suffix='-pip.py') as pip:
        pip.write(to_bytes(script))
        pip.flush()

        for name, options in commands:
            try:
                globals()[name](pip.name, options)
            except ApplicationError as ex:
                print(ex)
                sys.exit(1)


def install(pip, options):  # type: (str, t.Dict[str, t.Any]) -> None
    """Perform a pip install."""
    requirements = options['requirements']
    constraints = options['constraints']
    packages = options['packages']

    tempdir = tempfile.mkdtemp(prefix='ansible-test-', suffix='-requirements')

    try:
        options = common_pip_options()
        options.extend(packages)

        for path, content in requirements:
            write_text_file(os.path.join(tempdir, path), content, True)
            options.extend(['-r', path])

        for path, content in constraints:
            write_text_file(os.path.join(tempdir, path), content, True)
            options.extend(['-c', path])

        command = [sys.executable, pip, 'install'] + options

        execute_command(command, tempdir)
    finally:
        remove_tree(tempdir)


def uninstall(pip, options):  # type: (str, t.Dict[str, t.Any]) -> None
    """Perform a pip uninstall."""
    packages = options['packages']
    ignore_errors = options['ignore_errors']

    options = common_pip_options()
    options.extend(packages)

    command = [sys.executable, pip, 'uninstall', '-y'] + options

    try:
        execute_command(command, capture=True)
    except SubprocessError:
        if not ignore_errors:
            raise


def common_pip_options():  # type: () -> t.List[str]
    """Return a list of common pip options."""
    return [
        '--disable-pip-version-check',
    ]


def devnull():  # type: () -> t.IO[bytes]
    """Return a file object that references devnull."""
    try:
        return devnull.file
    except AttributeError:
        devnull.file = open(os.devnull, 'w+b')  # pylint: disable=consider-using-with

    return devnull.file


class ApplicationError(Exception):
    """Base class for application exceptions."""


class SubprocessError(ApplicationError):
    """A command returned a non-zero status."""
    def __init__(self, cmd, status, stdout, stderr):  # type: (t.List[str], int, str, str) -> None
        message = 'A command failed with status %d: %s' % (status, ' '.join(cmd_quote(c) for c in cmd))

        if stderr:
            message += '\n>>> Standard Error\n%s' % stderr.strip()

        if stdout:
            message += '\n>>> Standard Output\n%s' % stdout.strip()

        super(SubprocessError, self).__init__(message)


def log(message, verbosity=0):  # type: (str, int) -> None
    """Log a message to the console if the verbosity is high enough."""
    if verbosity > VERBOSITY:
        return

    print(message, file=CONSOLE)
    CONSOLE.flush()


def execute_command(cmd, cwd=None, capture=False):  # type: (t.List[str], t.Optional[str], bool) -> None
    """Execute the specified command."""
    log('Execute command: %s' % ' '.join(cmd_quote(c) for c in cmd), verbosity=1)

    cmd_bytes = [to_bytes(c) for c in cmd]

    if capture:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    else:
        stdout = None
        stderr = None

    process = subprocess.Popen(cmd_bytes, cwd=to_optional_bytes(cwd), stdin=devnull(), stdout=stdout, stderr=stderr)  # pylint: disable=consider-using-with
    stdout_bytes, stderr_bytes = process.communicate()
    stdout_text = to_optional_text(stdout_bytes) or u''
    stderr_text = to_optional_text(stderr_bytes) or u''

    if process.returncode != 0:
        raise SubprocessError(cmd, process.returncode, stdout_text, stderr_text)


def write_text_file(path, content, create_directories=False):  # type: (str, str, bool) -> None
    """Write the given text content to the specified path, optionally creating missing directories."""
    if create_directories:
        make_dirs(os.path.dirname(path))

    with open_binary_file(path, 'wb') as file_obj:
        file_obj.write(to_bytes(content))


def remove_tree(path):  # type: (str) -> None
    """Remove the specified directory tree."""
    try:
        shutil.rmtree(to_bytes(path))
    except OSError as ex:
        if ex.errno != errno.ENOENT:
            raise


def make_dirs(path):  # type: (str) -> None
    """Create a directory at path, including any necessary parent directories."""
    try:
        os.makedirs(to_bytes(path))
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise


def open_binary_file(path, mode='rb'):  # type: (str, str) -> t.BinaryIO
    """Open the given path for binary access."""
    if 'b' not in mode:
        raise Exception('mode must include "b" for binary files: %s' % mode)

    # noinspection PyTypeChecker
    return io.open(to_bytes(path), mode)  # pylint: disable=consider-using-with


def to_optional_bytes(value, errors='strict'):  # type: (t.Optional[t.AnyStr], str) -> t.Optional[bytes]
    """Return the given value as bytes encoded using UTF-8 if not already bytes, or None if the value is None."""
    return None if value is None else to_bytes(value, errors)


def to_optional_text(value, errors='strict'):  # type: (t.Optional[t.AnyStr], str) -> t.Optional[t.Text]
    """Return the given value as text decoded using UTF-8 if not already text, or None if the value is None."""
    return None if value is None else to_text(value, errors)


def to_bytes(value, errors='strict'):  # type: (t.AnyStr, str) -> bytes
    """Return the given value as bytes encoded using UTF-8 if not already bytes."""
    if isinstance(value, bytes):
        return value

    if isinstance(value, Text):
        return value.encode(ENCODING, errors)

    raise Exception('value is not bytes or text: %s' % type(value))


def to_text(value, errors='strict'):  # type: (t.AnyStr, str) -> t.Text
    """Return the given value as text decoded using UTF-8 if not already text."""
    if isinstance(value, bytes):
        return value.decode(ENCODING, errors)

    if isinstance(value, Text):
        return value

    raise Exception('value is not bytes or text: %s' % type(value))


if __name__ == '__main__':
    main()
