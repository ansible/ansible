#!/usr/bin/env python
"""Code coverage wrapper."""

from __future__ import absolute_import, print_function

import errno
import os
import sys
import pipes
import logging
import getpass

logger = logging.getLogger('injector')  # pylint: disable=locally-disabled, invalid-name


def main():
    """Main entry point."""
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
        logger.debug('Arguments: %s', ' '.join(pipes.quote(c) for c in sys.argv))

        if os.path.basename(__file__).startswith('runner'):
            args, env = runner()
        elif os.path.basename(__file__).startswith('cover'):
            args, env = cover()
        else:
            args, env = injector()

        logger.debug('Run command: %s', ' '.join(pipes.quote(c) for c in args))

        try:
            cwd = os.getcwd()
        except OSError as ex:
            if ex.errno != errno.EACCES:
                raise
            cwd = None

        logger.debug('Working directory: %s', cwd or '?')

        for key in sorted(env.keys()):
            logger.debug('%s=%s', key, env[key])

        os.execvpe(args[0], args, env)
    except Exception as ex:
        logger.fatal(ex)
        raise


def injector():
    """
    :rtype: list[str], dict[str, str]
    """
    self_dir = os.path.dirname(os.path.abspath(__file__))
    command = os.path.basename(__file__)
    mode = os.environ.get('ANSIBLE_TEST_COVERAGE')
    version = os.environ.get('ANSIBLE_TEST_PYTHON_VERSION', '')
    executable = find_executable(command)

    if mode in ('coverage', 'version'):
        if mode == 'coverage':
            args, env = coverage_command(self_dir, version)
            args += [executable]
            tool = 'cover'
        else:
            interpreter = find_executable('python' + version)
            args, env = [interpreter, executable], os.environ.copy()
            tool = 'runner'

        if command in ('ansible', 'ansible-playbook', 'ansible-pull'):
            interpreter = find_executable(tool + version)
            args += ['--extra-vars', 'ansible_python_interpreter=' + interpreter]
    else:
        args, env = [executable], os.environ.copy()

    args += sys.argv[1:]

    return args, env


def runner():
    """
    :rtype: list[str], dict[str, str]
    """
    command = os.path.basename(__file__)
    version = command.replace('runner', '')

    interpreter = find_executable('python' + version)
    args, env = [interpreter], os.environ.copy()

    args += sys.argv[1:]

    return args, env


def cover():
    """
    :rtype: list[str], dict[str, str]
    """
    self_dir = os.path.dirname(os.path.abspath(__file__))
    command = os.path.basename(__file__)
    version = command.replace('cover', '')

    if len(sys.argv) > 1:
        executable = sys.argv[1]
    else:
        executable = ''

    if os.path.basename(executable).startswith('ansible_module_'):
        args, env = coverage_command(self_dir, version)
    else:
        interpreter = find_executable('python' + version)
        args, env = [interpreter], os.environ.copy()

    args += sys.argv[1:]

    return args, env


def coverage_command(self_dir, version):
    """
    :type self_dir: str
    :type version: str
    :rtype: list[str], dict[str, str]
    """
    executable = 'coverage'

    if version:
        executable += '-%s' % version

    args = [
        find_executable(executable),
        'run',
        '--rcfile',
        os.path.join(self_dir, '.coveragerc'),
    ]

    env = os.environ.copy()
    env['COVERAGE_FILE'] = os.path.abspath(os.path.join(self_dir, '..', 'output', 'coverage'))

    return args, env


def find_executable(executable):
    """
    :type executable: str
    :rtype: str
    """
    self = os.path.abspath(__file__)
    path = os.environ.get('PATH', os.defpath)
    seen_dirs = set()

    for path_dir in path.split(os.pathsep):
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
