#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Test runner for all Ansible tests."""

from __future__ import absolute_import, print_function

import errno
import os
import sys

from lib.util import (
    ApplicationError,
    display,
    raw_command,
    get_docker_completion,
    generate_pip_command,
)

from lib.delegation import (
    delegate,
)

from lib.executor import (
    command_posix_integration,
    command_network_integration,
    command_windows_integration,
    command_units,
    command_shell,
    SUPPORTED_PYTHON_VERSIONS,
    ApplicationWarning,
    Delegate,
    generate_pip_install,
    check_startup,
)

from lib.config import (
    IntegrationConfig,
    PosixIntegrationConfig,
    WindowsIntegrationConfig,
    NetworkIntegrationConfig,
    SanityConfig,
    UnitsConfig,
    ShellConfig,
)

from lib.sanity import (
    command_sanity,
    sanity_init,
    sanity_get_tests,
)

from lib.target import (
    find_target_completion,
    walk_posix_integration_targets,
    walk_network_integration_targets,
    walk_windows_integration_targets,
    walk_units_targets,
    walk_sanity_targets,
)

from lib.core_ci import (
    AWS_ENDPOINTS,
)

from lib.cloud import (
    initialize_cloud_plugins,
)

import lib.cover


def main():
    """Main program function."""
    try:
        git_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        os.chdir(git_root)
        initialize_cloud_plugins()
        sanity_init()
        args = parse_args()
        config = args.config(args)
        display.verbosity = config.verbosity
        display.truncate = config.truncate
        display.redact = config.redact
        display.color = config.color
        display.info_stderr = (isinstance(config, SanityConfig) and config.lint) or (isinstance(config, IntegrationConfig) and config.list_targets)
        check_startup()

        try:
            args.func(config)
        except Delegate as ex:
            delegate(config, ex.exclude, ex.require, ex.integration_targets)

        display.review_warnings()
    except ApplicationWarning as ex:
        display.warning(str(ex))
        exit(0)
    except ApplicationError as ex:
        display.error(str(ex))
        exit(1)
    except KeyboardInterrupt:
        exit(2)
    except IOError as ex:
        if ex.errno == errno.EPIPE:
            exit(3)
        raise


def parse_args():
    """Parse command line arguments."""
    try:
        import argparse
    except ImportError:
        if '--requirements' not in sys.argv:
            raise
        raw_command(generate_pip_install(generate_pip_command(sys.executable), 'ansible-test'))
        import argparse

    try:
        import argcomplete
    except ImportError:
        argcomplete = None

    if argcomplete:
        epilog = 'Tab completion available using the "argcomplete" python package.'
    else:
        epilog = 'Install the "argcomplete" python package to enable tab completion.'

    parser = argparse.ArgumentParser(epilog=epilog)

    common = argparse.ArgumentParser(add_help=False)

    common.add_argument('-e', '--explain',
                        action='store_true',
                        help='explain commands that would be executed')

    common.add_argument('-v', '--verbose',
                        dest='verbosity',
                        action='count',
                        default=0,
                        help='display more output')

    common.add_argument('--color',
                        metavar='COLOR',
                        nargs='?',
                        help='generate color output: %(choices)s',
                        choices=('yes', 'no', 'auto'),
                        const='yes',
                        default='auto')

    common.add_argument('--debug',
                        action='store_true',
                        help='run ansible commands in debug mode')

    common.add_argument('--truncate',
                        dest='truncate',
                        metavar='COLUMNS',
                        type=int,
                        default=display.columns,
                        help='truncate some long output (0=disabled) (default: auto)')

    common.add_argument('--redact',
                        dest='redact',
                        action='store_true',
                        help='redact sensitive values in output')

    test = argparse.ArgumentParser(add_help=False, parents=[common])

    test.add_argument('include',
                      metavar='TARGET',
                      nargs='*',
                      help='test the specified target').completer = complete_target

    test.add_argument('--exclude',
                      metavar='TARGET',
                      action='append',
                      help='exclude the specified target').completer = complete_target

    test.add_argument('--require',
                      metavar='TARGET',
                      action='append',
                      help='require the specified target').completer = complete_target

    test.add_argument('--coverage',
                      action='store_true',
                      help='analyze code coverage when running tests')

    test.add_argument('--coverage-label',
                      default='',
                      help='label to include in coverage output file names')

    test.add_argument('--metadata',
                      help=argparse.SUPPRESS)

    add_changes(test, argparse)
    add_environments(test)

    integration = argparse.ArgumentParser(add_help=False, parents=[test])

    integration.add_argument('--python',
                             metavar='VERSION',
                             choices=SUPPORTED_PYTHON_VERSIONS + ('default',),
                             help='python version: %s' % ', '.join(SUPPORTED_PYTHON_VERSIONS))

    integration.add_argument('--start-at',
                             metavar='TARGET',
                             help='start at the specified target').completer = complete_target

    integration.add_argument('--start-at-task',
                             metavar='TASK',
                             help='start at the specified task')

    integration.add_argument('--tags',
                             metavar='TAGS',
                             help='only run plays and tasks tagged with these values')

    integration.add_argument('--skip-tags',
                             metavar='TAGS',
                             help='only run plays and tasks whose tags do not match these values')

    integration.add_argument('--diff',
                             action='store_true',
                             help='show diff output')

    integration.add_argument('--allow-destructive',
                             action='store_true',
                             help='allow destructive tests (--local and --tox only)')

    integration.add_argument('--allow-root',
                             action='store_true',
                             help='allow tests requiring root when not root')

    integration.add_argument('--allow-disabled',
                             action='store_true',
                             help='allow tests which have been marked as disabled')

    integration.add_argument('--allow-unstable',
                             action='store_true',
                             help='allow tests which have been marked as unstable')

    integration.add_argument('--allow-unstable-changed',
                             action='store_true',
                             help='allow tests which have been marked as unstable when focused changes are detected')

    integration.add_argument('--allow-unsupported',
                             action='store_true',
                             help='allow tests which have been marked as unsupported')

    integration.add_argument('--retry-on-error',
                             action='store_true',
                             help='retry failed test with increased verbosity')

    integration.add_argument('--continue-on-error',
                             action='store_true',
                             help='continue after failed test')

    integration.add_argument('--debug-strategy',
                             action='store_true',
                             help='run test playbooks using the debug strategy')

    integration.add_argument('--changed-all-target',
                             metavar='TARGET',
                             default='all',
                             help='target to run when all tests are needed')

    integration.add_argument('--list-targets',
                             action='store_true',
                             help='list matching targets instead of running tests')

    subparsers = parser.add_subparsers(metavar='COMMAND')
    subparsers.required = True  # work-around for python 3 bug which makes subparsers optional

    posix_integration = subparsers.add_parser('integration',
                                              parents=[integration],
                                              help='posix integration tests')

    posix_integration.set_defaults(func=command_posix_integration,
                                   targets=walk_posix_integration_targets,
                                   config=PosixIntegrationConfig)

    add_extra_docker_options(posix_integration)
    add_httptester_options(posix_integration, argparse)

    network_integration = subparsers.add_parser('network-integration',
                                                parents=[integration],
                                                help='network integration tests')

    network_integration.set_defaults(func=command_network_integration,
                                     targets=walk_network_integration_targets,
                                     config=NetworkIntegrationConfig)

    add_extra_docker_options(network_integration, integration=False)

    network_integration.add_argument('--platform',
                                     metavar='PLATFORM',
                                     action='append',
                                     help='network platform/version').completer = complete_network_platform

    network_integration.add_argument('--inventory',
                                     metavar='PATH',
                                     help='path to inventory used for tests')

    network_integration.add_argument('--testcase',
                                     metavar='TESTCASE',
                                     help='limit a test to a specified testcase').completer = complete_network_testcase

    windows_integration = subparsers.add_parser('windows-integration',
                                                parents=[integration],
                                                help='windows integration tests')

    windows_integration.set_defaults(func=command_windows_integration,
                                     targets=walk_windows_integration_targets,
                                     config=WindowsIntegrationConfig)

    add_extra_docker_options(windows_integration, integration=False)

    windows_integration.add_argument('--windows',
                                     metavar='VERSION',
                                     action='append',
                                     help='windows version').completer = complete_windows

    units = subparsers.add_parser('units',
                                  parents=[test],
                                  help='unit tests')

    units.set_defaults(func=command_units,
                       targets=walk_units_targets,
                       config=UnitsConfig)

    units.add_argument('--python',
                       metavar='VERSION',
                       choices=SUPPORTED_PYTHON_VERSIONS + ('default',),
                       help='python version: %s' % ', '.join(SUPPORTED_PYTHON_VERSIONS))

    units.add_argument('--collect-only',
                       action='store_true',
                       help='collect tests but do not execute them')

    add_extra_docker_options(units, integration=False)

    sanity = subparsers.add_parser('sanity',
                                   parents=[test],
                                   help='sanity tests')

    sanity.set_defaults(func=command_sanity,
                        targets=walk_sanity_targets,
                        config=SanityConfig)

    sanity.add_argument('--test',
                        metavar='TEST',
                        action='append',
                        choices=[test.name for test in sanity_get_tests()],
                        help='tests to run').completer = complete_sanity_test

    sanity.add_argument('--skip-test',
                        metavar='TEST',
                        action='append',
                        choices=[test.name for test in sanity_get_tests()],
                        help='tests to skip').completer = complete_sanity_test

    sanity.add_argument('--allow-disabled',
                        action='store_true',
                        help='allow tests to run which are disabled by default')

    sanity.add_argument('--list-tests',
                        action='store_true',
                        help='list available tests')

    sanity.add_argument('--python',
                        metavar='VERSION',
                        choices=SUPPORTED_PYTHON_VERSIONS + ('default',),
                        help='python version: %s' % ', '.join(SUPPORTED_PYTHON_VERSIONS))

    sanity.add_argument('--base-branch',
                        help=argparse.SUPPRESS)

    add_lint(sanity)
    add_extra_docker_options(sanity, integration=False)

    shell = subparsers.add_parser('shell',
                                  parents=[common],
                                  help='open an interactive shell')

    shell.set_defaults(func=command_shell,
                       config=ShellConfig)

    add_environments(shell, tox_version=True)
    add_extra_docker_options(shell)
    add_httptester_options(shell, argparse)

    coverage_common = argparse.ArgumentParser(add_help=False, parents=[common])

    add_environments(coverage_common, tox_version=True, tox_only=True)

    coverage = subparsers.add_parser('coverage',
                                     help='code coverage management and reporting')

    coverage_subparsers = coverage.add_subparsers(metavar='COMMAND')
    coverage_subparsers.required = True  # work-around for python 3 bug which makes subparsers optional

    coverage_combine = coverage_subparsers.add_parser('combine',
                                                      parents=[coverage_common],
                                                      help='combine coverage data and rewrite remote paths')

    coverage_combine.set_defaults(func=lib.cover.command_coverage_combine,
                                  config=lib.cover.CoverageConfig)

    add_extra_coverage_options(coverage_combine)

    coverage_erase = coverage_subparsers.add_parser('erase',
                                                    parents=[coverage_common],
                                                    help='erase coverage data files')

    coverage_erase.set_defaults(func=lib.cover.command_coverage_erase,
                                config=lib.cover.CoverageConfig)

    coverage_report = coverage_subparsers.add_parser('report',
                                                     parents=[coverage_common],
                                                     help='generate console coverage report')

    coverage_report.set_defaults(func=lib.cover.command_coverage_report,
                                 config=lib.cover.CoverageReportConfig)

    coverage_report.add_argument('--show-missing',
                                 action='store_true',
                                 help='show line numbers of statements not executed')
    coverage_report.add_argument('--include',
                                 metavar='PAT1,PAT2,...',
                                 help='include only files whose paths match one of these '
                                      'patterns. Accepts shell-style wildcards, which must be '
                                      'quoted.')
    coverage_report.add_argument('--omit',
                                 metavar='PAT1,PAT2,...',
                                 help='omit files whose paths match one of these patterns. '
                                      'Accepts shell-style wildcards, which must be quoted.')

    add_extra_coverage_options(coverage_report)

    coverage_html = coverage_subparsers.add_parser('html',
                                                   parents=[coverage_common],
                                                   help='generate html coverage report')

    coverage_html.set_defaults(func=lib.cover.command_coverage_html,
                               config=lib.cover.CoverageConfig)

    add_extra_coverage_options(coverage_html)

    coverage_xml = coverage_subparsers.add_parser('xml',
                                                  parents=[coverage_common],
                                                  help='generate xml coverage report')

    coverage_xml.set_defaults(func=lib.cover.command_coverage_xml,
                              config=lib.cover.CoverageConfig)

    add_extra_coverage_options(coverage_xml)

    if argcomplete:
        argcomplete.autocomplete(parser, always_complete_options=False, validator=lambda i, k: True)

    args = parser.parse_args()

    if args.explain and not args.verbosity:
        args.verbosity = 1

    if args.color == 'yes':
        args.color = True
    elif args.color == 'no':
        args.color = False
    else:
        args.color = sys.stdout.isatty()

    return args


def add_lint(parser):
    """
    :type parser: argparse.ArgumentParser
    """
    parser.add_argument('--lint',
                        action='store_true',
                        help='write lint output to stdout, everything else stderr')

    parser.add_argument('--junit',
                        action='store_true',
                        help='write test failures to junit xml files')

    parser.add_argument('--failure-ok',
                        action='store_true',
                        help='exit successfully on failed tests after saving results')


def add_changes(parser, argparse):
    """
    :type parser: argparse.ArgumentParser
    :type argparse: argparse
    """
    parser.add_argument('--changed', action='store_true', help='limit targets based on changes')

    changes = parser.add_argument_group(title='change detection arguments')

    changes.add_argument('--tracked', action='store_true', help=argparse.SUPPRESS)
    changes.add_argument('--untracked', action='store_true', help='include untracked files')
    changes.add_argument('--ignore-committed', dest='committed', action='store_false', help='exclude committed files')
    changes.add_argument('--ignore-staged', dest='staged', action='store_false', help='exclude staged files')
    changes.add_argument('--ignore-unstaged', dest='unstaged', action='store_false', help='exclude unstaged files')

    changes.add_argument('--changed-from', metavar='PATH', help=argparse.SUPPRESS)
    changes.add_argument('--changed-path', metavar='PATH', action='append', help=argparse.SUPPRESS)


def add_environments(parser, tox_version=False, tox_only=False):
    """
    :type parser: argparse.ArgumentParser
    :type tox_version: bool
    :type tox_only: bool
    """
    parser.add_argument('--requirements',
                        action='store_true',
                        help='install command requirements')

    environments = parser.add_mutually_exclusive_group()

    environments.add_argument('--local',
                              action='store_true',
                              help='run from the local environment')

    if tox_version:
        environments.add_argument('--tox',
                                  metavar='VERSION',
                                  nargs='?',
                                  default=None,
                                  const='.'.join(str(i) for i in sys.version_info[:2]),
                                  choices=SUPPORTED_PYTHON_VERSIONS,
                                  help='run from a tox virtualenv: %s' % ', '.join(SUPPORTED_PYTHON_VERSIONS))
    else:
        environments.add_argument('--tox',
                                  action='store_true',
                                  help='run from a tox virtualenv')

    tox = parser.add_argument_group(title='tox arguments')

    tox.add_argument('--tox-sitepackages',
                     action='store_true',
                     help='allow access to globally installed packages')

    if tox_only:
        environments.set_defaults(
            docker=None,
            remote=None,
            remote_stage=None,
            remote_provider=None,
            remote_aws_region=None,
            remote_terminate=None,
        )

        return

    environments.add_argument('--docker',
                              metavar='IMAGE',
                              nargs='?',
                              default=None,
                              const='default',
                              help='run from a docker container').completer = complete_docker

    environments.add_argument('--remote',
                              metavar='PLATFORM',
                              default=None,
                              help='run from a remote instance').completer = complete_remote

    remote = parser.add_argument_group(title='remote arguments')

    remote.add_argument('--remote-stage',
                        metavar='STAGE',
                        help='remote stage to use: %(choices)s',
                        choices=['prod', 'dev'],
                        default='prod')

    remote.add_argument('--remote-provider',
                        metavar='PROVIDER',
                        help='remote provider to use: %(choices)s',
                        choices=['default', 'aws', 'azure', 'parallels'],
                        default='default')

    remote.add_argument('--remote-aws-region',
                        metavar='REGION',
                        help='remote aws region to use: %(choices)s (default: auto)',
                        choices=sorted(AWS_ENDPOINTS),
                        default=None)

    remote.add_argument('--remote-terminate',
                        metavar='WHEN',
                        help='terminate remote instance: %(choices)s (default: %(default)s)',
                        choices=['never', 'always', 'success'],
                        default='never')


def add_extra_coverage_options(parser):
    """
    :type parser: argparse.ArgumentParser
    """
    parser.add_argument('--group-by',
                        metavar='GROUP',
                        action='append',
                        choices=lib.cover.COVERAGE_GROUPS,
                        help='group output by: %s' % ', '.join(lib.cover.COVERAGE_GROUPS))

    parser.add_argument('--all',
                        action='store_true',
                        help='include all python source files')

    parser.add_argument('--stub',
                        action='store_true',
                        help='generate empty report of all python source files')


def add_httptester_options(parser, argparse):
    """
    :type parser: argparse.ArgumentParser
    :type argparse: argparse
    """
    group = parser.add_mutually_exclusive_group()

    group.add_argument('--httptester',
                       metavar='IMAGE',
                       default='quay.io/ansible/http-test-container:1.0.0',
                       help='docker image to use for the httptester container')

    group.add_argument('--disable-httptester',
                       dest='httptester',
                       action='store_const',
                       const='',
                       help='do not use the httptester container')

    parser.add_argument('--inject-httptester',
                        action='store_true',
                        help=argparse.SUPPRESS)  # internal use only


def add_extra_docker_options(parser, integration=True):
    """
    :type parser: argparse.ArgumentParser
    :type integration: bool
    """
    docker = parser.add_argument_group(title='docker arguments')

    docker.add_argument('--docker-no-pull',
                        action='store_false',
                        dest='docker_pull',
                        help='do not explicitly pull the latest docker images')

    docker.add_argument('--docker-keep-git',
                        action='store_true',
                        help='transfer git related files into the docker container')

    if not integration:
        return

    docker.add_argument('--docker-privileged',
                        action='store_true',
                        help='run docker container in privileged mode')

    docker.add_argument('--docker-memory',
                        help='memory limit for docker in bytes', type=int)


def complete_target(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    return find_target_completion(parsed_args.targets, prefix)


def complete_remote(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    del parsed_args

    with open('test/runner/completion/remote.txt', 'r') as completion_fd:
        images = completion_fd.read().splitlines()

    return [i for i in images if i.startswith(prefix)]


def complete_docker(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    del parsed_args

    images = sorted(get_docker_completion().keys())

    return [i for i in images if i.startswith(prefix)]


def complete_windows(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    with open('test/runner/completion/windows.txt', 'r') as completion_fd:
        images = completion_fd.read().splitlines()

    return [i for i in images if i.startswith(prefix) and (not parsed_args.windows or i not in parsed_args.windows)]


def complete_network_platform(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    with open('test/runner/completion/network.txt', 'r') as completion_fd:
        images = completion_fd.read().splitlines()

    return [i for i in images if i.startswith(prefix) and (not parsed_args.platform or i not in parsed_args.platform)]


def complete_network_testcase(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    testcases = []

    # since testcases are module specific, don't autocomplete if more than one
    # module is specidied
    if len(parsed_args.include) != 1:
        return []

    test_dir = 'test/integration/targets/%s/tests' % parsed_args.include[0]
    connections = os.listdir(test_dir)

    for conn in connections:
        if os.path.isdir(os.path.join(test_dir, conn)):
            for testcase in os.listdir(os.path.join(test_dir, conn)):
                if testcase.startswith(prefix):
                    testcases.append(testcase.split('.')[0])

    return testcases


def complete_sanity_test(prefix, parsed_args, **_):
    """
    :type prefix: unicode
    :type parsed_args: any
    :rtype: list[str]
    """
    del parsed_args

    tests = sorted(t.name for t in sanity_get_tests())

    return [i for i in tests if i.startswith(prefix)]


if __name__ == '__main__':
    main()
