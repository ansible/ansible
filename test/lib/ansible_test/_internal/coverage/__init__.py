"""Common logic for the coverage subcommand."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from .. import types as t

from ..util import (
    ApplicationError,
    common_environment,
    ANSIBLE_TEST_DATA_ROOT,
)

from ..util_common import (
    intercept_command,
)

from ..config import (
    EnvironmentConfig,
)

from ..executor import (
    Delegate,
    install_command_requirements,
)

COVERAGE_GROUPS = ('command', 'target', 'environment', 'version')
COVERAGE_CONFIG_PATH = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'coveragerc')
COVERAGE_OUTPUT_FILE_NAME = 'coverage'


def initialize_coverage(args):
    """
    :type args: CoverageConfig
    :rtype: coverage
    """
    if args.delegate:
        raise Delegate()

    if args.requirements:
        install_command_requirements(args)

    try:
        import coverage
    except ImportError:
        coverage = None

    if not coverage:
        raise ApplicationError('You must install the "coverage" python module to use this command.')

    return coverage


def run_coverage(args, output_file, command, cmd):  # type: (CoverageConfig, str, str, t.List[str]) -> None
    """Run the coverage cli tool with the specified options."""
    env = common_environment()
    env.update(dict(COVERAGE_FILE=output_file))

    cmd = ['python', '-m', 'coverage', command, '--rcfile', COVERAGE_CONFIG_PATH] + cmd

    intercept_command(args, target_name='coverage', env=env, cmd=cmd, disable_coverage=True)


class CoverageConfig(EnvironmentConfig):
    """Configuration for the coverage command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageConfig, self).__init__(args, 'coverage')

        self.group_by = frozenset(args.group_by) if 'group_by' in args and args.group_by else set()  # type: t.FrozenSet[str]
        self.all = args.all if 'all' in args else False  # type: bool
        self.stub = args.stub if 'stub' in args else False  # type: bool
        self.coverage = False  # temporary work-around to support intercept_command in cover.py
