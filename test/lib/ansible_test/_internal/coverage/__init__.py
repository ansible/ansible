"""Common logic for the coverage subcommand."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from .. import types as t

from ..util import (
    ApplicationError,
    common_environment,
    display,
    ANSIBLE_TEST_DATA_ROOT,
)

from ..util_common import (
    intercept_command,
    ResultType,
)

from ..config import (
    EnvironmentConfig,
)

from ..executor import (
    Delegate,
    install_command_requirements,
)

from ..data import (
    data_context,
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


def get_python_coverage_files():  # type: () -> t.List[str]
    """Return the list of Python coverage file paths."""
    coverage_dir = ResultType.COVERAGE.path
    coverage_files = [os.path.join(coverage_dir, f) for f in os.listdir(coverage_dir)
                      if '=coverage.' in f and '=python' in f]

    return coverage_files


def get_powershell_coverage_files():  # type: () -> t.List[str]
    """Return the list of PowerShell coverage file paths."""
    coverage_dir = ResultType.COVERAGE.path
    coverage_files = [os.path.join(coverage_dir, f) for f in os.listdir(coverage_dir)
                      if '=coverage.' in f and '=powershell' in f]

    return coverage_files


def sanitize_filename(filename, modules=None, collection_search_re=None, collection_sub_re=None):
    """
    :type filename: str
    :type modules: dict | None
    :type collection_search_re: Pattern | None
    :type collection_sub_re: Pattern | None
    :rtype: str | None
    """
    ansible_path = os.path.abspath('lib/ansible/') + '/'
    root_path = data_context().content.root + '/'
    integration_temp_path = os.path.sep + os.path.join(ResultType.TMP.relative_path, 'integration') + os.path.sep

    if modules is None:
        modules = {}

    if '/ansible_modlib.zip/ansible/' in filename:
        # Rewrite the module_utils path from the remote host to match the controller. Ansible 2.6 and earlier.
        new_name = re.sub('^.*/ansible_modlib.zip/ansible/', ansible_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif collection_search_re and collection_search_re.search(filename):
        new_name = os.path.abspath(collection_sub_re.sub('', filename))
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search(r'/ansible_[^/]+_payload\.zip/ansible/', filename):
        # Rewrite the module_utils path from the remote host to match the controller. Ansible 2.7 and later.
        new_name = re.sub(r'^.*/ansible_[^/]+_payload\.zip/ansible/', ansible_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif '/ansible_module_' in filename:
        # Rewrite the module path from the remote host to match the controller. Ansible 2.6 and earlier.
        module_name = re.sub('^.*/ansible_module_(?P<module>.*).py$', '\\g<module>', filename)
        if module_name not in modules:
            display.warning('Skipping coverage of unknown module: %s' % module_name)
            return None
        new_name = os.path.abspath(modules[module_name])
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search(r'/ansible_[^/]+_payload(_[^/]+|\.zip)/__main__\.py$', filename):
        # Rewrite the module path from the remote host to match the controller. Ansible 2.7 and later.
        # AnsiballZ versions using zipimporter will match the `.zip` portion of the regex.
        # AnsiballZ versions not using zipimporter will match the `_[^/]+` portion of the regex.
        module_name = re.sub(r'^.*/ansible_(?P<module>[^/]+)_payload(_[^/]+|\.zip)/__main__\.py$',
                             '\\g<module>', filename).rstrip('_')
        if module_name not in modules:
            display.warning('Skipping coverage of unknown module: %s' % module_name)
            return None
        new_name = os.path.abspath(modules[module_name])
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search('^(/.*?)?/root/ansible/', filename):
        # Rewrite the path of code running on a remote host or in a docker container as root.
        new_name = re.sub('^(/.*?)?/root/ansible/', root_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif integration_temp_path in filename:
        # Rewrite the path of code running from an integration test temporary directory.
        new_name = re.sub(r'^.*' + re.escape(integration_temp_path) + '[^/]+/', root_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name

    return filename


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
