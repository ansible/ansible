#!/usr/bin/env python
"""Interpreter and code coverage injector for use with ansible-test.

The injector serves two main purposes:

1) Control the python interpreter used to run test tools and ansible code.
2) Provide optional code coverage analysis of ansible code.

The injector is executed one of two ways:

1) On the controller via a symbolic link such as ansible or pytest.
   This is accomplished by prepending the injector directory to the PATH by ansible-test.

2) As the python interpreter when running ansible modules.
   This is only supported when connecting to the local host.
   Otherwise set the ANSIBLE_TEST_REMOTE_INTERPRETER environment variable.
   It can be empty to auto-detect the python interpreter on the remote host.
   If not empty it will be used to set ansible_python_interpreter.

NOTE: Running ansible-test with the --tox option or inside a virtual environment
      may prevent the injector from working for tests which use connection
      types other than local, or which use become, due to lack of permissions
      to access the interpreter for the virtual environment.
"""

from __future__ import absolute_import, print_function

import errno
import json
import os
import sys
import pipes
import logging
import getpass
import resource

logger = logging.getLogger('injector')  # pylint: disable=locally-disabled, invalid-name
# pylint: disable=locally-disabled, invalid-name
config = None  # type: InjectorConfig


class InjectorConfig(object):
    """Mandatory configuration."""
    def __init__(self, config_path):
        """Initialize config."""
        with open(config_path) as config_fd:
            _config = json.load(config_fd)

        self.python_interpreter = _config['python_interpreter']
        self.coverage_file = _config['coverage_file']

        # Read from the environment instead of config since it needs to be changed by integration test scripts.
        # It also does not need to flow from the controller to the remote. It is only used on the controller.
        self.remote_interpreter = os.environ.get('ANSIBLE_TEST_REMOTE_INTERPRETER', None)

        self.arguments = [to_text(c) for c in sys.argv]


def to_text(value):
    """
    :type value: str | None
    :rtype: str | None
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        return value.decode('utf-8')

    return u'%s' % value


def main():
    """Main entry point."""
    global config  # pylint: disable=locally-disabled, global-statement

    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s %(message)s')
    log_name = 'ansible-test-coverage.%s.log' % getpass.getuser()
    self_dir = os.path.dirname(os.path.abspath(__file__))

    handler = logging.FileHandler(os.path.join('/tmp', log_name))
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.FileHandler(os.path.abspath(os.path.join(self_dir, '..', 'logs', log_name)))
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)

    try:
        logger.debug('Self: %s', __file__)

        # to achieve a consistent nofile ulimit, set to 16k here, this can affect performance in subprocess.Popen when
        # being called with close_fds=True on Python (8x the time on some environments)
        nofile_limit = 16 * 1024
        current_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        new_limit = (nofile_limit, nofile_limit)
        if current_limit > new_limit:
            logger.debug('RLIMIT_NOFILE: %s -> %s', current_limit, new_limit)
            resource.setrlimit(resource.RLIMIT_NOFILE, (nofile_limit, nofile_limit))
        else:
            logger.debug('RLIMIT_NOFILE: %s', current_limit)

        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'injector.json')

        try:
            config = InjectorConfig(config_path)
        except IOError:
            logger.exception('Error reading config: %s', config_path)
            exit('No injector config found. Set ANSIBLE_TEST_REMOTE_INTERPRETER if the test is not connecting to the local host.')

        logger.debug('Arguments: %s', ' '.join(pipes.quote(c) for c in config.arguments))
        logger.debug('Python interpreter: %s', config.python_interpreter)
        logger.debug('Remote interpreter: %s', config.remote_interpreter)
        logger.debug('Coverage file: %s', config.coverage_file)

        require_cwd = False

        if os.path.basename(__file__) == 'injector.py':
            if config.coverage_file:
                args, env, require_cwd = cover()
            else:
                args, env = runner()
        elif os.path.basename(__file__) == 'python.py':
            args, env = python()  # run arbitrary python commands using the correct python and with optional code coverage
        else:
            args, env = injector()

        logger.debug('Run command: %s', ' '.join(pipes.quote(c) for c in args))

        altered_cwd = False

        try:
            cwd = os.getcwd()
        except OSError as ex:
            # some platforms, such as OS X, may not allow querying the working directory when using become to drop privileges
            if ex.errno != errno.EACCES:
                raise
            if require_cwd:
                # make sure the program we execute can determine the working directory if it's required
                cwd = '/'
                os.chdir(cwd)
                altered_cwd = True
            else:
                cwd = None

        logger.debug('Working directory: %s%s', cwd or '?', ' (altered)' if altered_cwd else '')

        for key in sorted(env.keys()):
            logger.debug('%s=%s', key, env[key])

        os.execvpe(args[0], args, env)
    except Exception as ex:
        logger.fatal(ex)
        raise


def python():
    """
    :rtype: list[str], dict[str, str]
    """
    if config.coverage_file:
        args, env = coverage_command()
    else:
        args, env = [config.python_interpreter], os.environ.copy()

    args += config.arguments[1:]

    return args, env


def injector():
    """
    :rtype: list[str], dict[str, str]
    """
    command = os.path.basename(__file__)
    executable = find_executable(command)

    if config.coverage_file:
        args, env = coverage_command()
    else:
        args, env = [config.python_interpreter], os.environ.copy()

    args += [executable]

    if command in ('ansible', 'ansible-playbook', 'ansible-pull'):
        if config.remote_interpreter is None:
            interpreter = os.path.join(os.path.dirname(__file__), 'injector.py')
        elif config.remote_interpreter == '':
            interpreter = None
        else:
            interpreter = config.remote_interpreter

        if interpreter:
            args += ['--extra-vars', 'ansible_python_interpreter=' + interpreter]

    args += config.arguments[1:]

    return args, env


def runner():
    """
    :rtype: list[str], dict[str, str]
    """
    args, env = [config.python_interpreter], os.environ.copy()

    args += config.arguments[1:]

    return args, env


def cover():
    """
    :rtype: list[str], dict[str, str], bool
    """
    if len(config.arguments) > 1:
        executable = config.arguments[1]
    else:
        executable = ''

    require_cwd = False

    if os.path.basename(executable).startswith('ansible_module_'):
        args, env = coverage_command()
        # coverage requires knowing the working directory
        require_cwd = True
    else:
        args, env = [config.python_interpreter], os.environ.copy()

    args += config.arguments[1:]

    return args, env, require_cwd


def coverage_command():
    """
    :rtype: list[str], dict[str, str]
    """
    self_dir = os.path.dirname(os.path.abspath(__file__))

    args = [
        config.python_interpreter,
        '-m',
        'coverage.__main__',
        'run',
        '--rcfile',
        os.path.join(self_dir, '.coveragerc'),
    ]

    env = os.environ.copy()
    env['COVERAGE_FILE'] = config.coverage_file

    return args, env


def find_executable(executable):
    """
    :type executable: str
    :rtype: str
    """
    self = os.path.abspath(__file__)
    path = os.environ.get('PATH', os.path.defpath)
    seen_dirs = set()

    for path_dir in path.split(os.path.pathsep):
        if path_dir in seen_dirs:
            continue

        seen_dirs.add(path_dir)
        candidate = os.path.abspath(os.path.join(path_dir, executable))

        if candidate == self:
            continue

        if os.path.exists(candidate) and os.access(candidate, os.F_OK | os.X_OK):
            return candidate

    raise Exception('Executable "%s" not found in path: %s' % (executable, path))


if __name__ == '__main__':
    main()
