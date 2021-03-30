"""Common logic for the coverage subcommand."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from .. import types as t

from ..encoding import (
    to_bytes,
)

from ..io import (
    open_binary_file,
    read_json_file,
)

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

from .. target import (
    walk_module_targets,
)

from ..data import (
    data_context,
)

if t.TYPE_CHECKING:
    import coverage as coverage_module

COVERAGE_GROUPS = ('command', 'target', 'environment', 'version')
COVERAGE_CONFIG_PATH = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'coveragerc')
COVERAGE_OUTPUT_FILE_NAME = 'coverage'


class CoverageConfig(EnvironmentConfig):
    """Configuration for the coverage command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageConfig, self).__init__(args, 'coverage')

        self.group_by = frozenset(args.group_by) if 'group_by' in args and args.group_by else set()  # type: t.FrozenSet[str]
        self.all = args.all if 'all' in args else False  # type: bool
        self.stub = args.stub if 'stub' in args else False  # type: bool
        self.export = args.export if 'export' in args else None  # type: str
        self.coverage = False  # temporary work-around to support intercept_command in cover.py


def initialize_coverage(args):  # type: (CoverageConfig) -> coverage_module
    """Delegate execution if requested, install requirements, then import and return the coverage module. Raises an exception if coverage is not available."""
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

    coverage_version_string = coverage.__version__
    coverage_version = tuple(int(v) for v in coverage_version_string.split('.'))

    min_version = (4, 2)
    max_version = (5, 0)

    supported_version = True
    recommended_version = '4.5.4'

    if coverage_version < min_version or coverage_version >= max_version:
        supported_version = False

    if not supported_version:
        raise ApplicationError('Version %s of "coverage" is not supported. Version %s is known to work and is recommended.' % (
            coverage_version_string, recommended_version))

    return coverage


def run_coverage(args, output_file, command, cmd):  # type: (CoverageConfig, str, str, t.List[str]) -> None
    """Run the coverage cli tool with the specified options."""
    env = common_environment()
    env.update(dict(COVERAGE_FILE=output_file))

    cmd = ['python', '-m', 'coverage.__main__', command, '--rcfile', COVERAGE_CONFIG_PATH] + cmd

    intercept_command(args, target_name='coverage', env=env, cmd=cmd, disable_coverage=True)


def get_python_coverage_files(path=None):  # type: (t.Optional[str]) -> t.List[str]
    """Return the list of Python coverage file paths."""
    return get_coverage_files('python', path)


def get_powershell_coverage_files(path=None):  # type: (t.Optional[str]) -> t.List[str]
    """Return the list of PowerShell coverage file paths."""
    return get_coverage_files('powershell', path)


def get_coverage_files(language, path=None):  # type: (str, t.Optional[str]) -> t.List[str]
    """Return the list of coverage file paths for the given language."""
    coverage_dir = path or ResultType.COVERAGE.path
    coverage_files = [os.path.join(coverage_dir, f) for f in os.listdir(coverage_dir)
                      if '=coverage.' in f and '=%s' % language in f]

    return coverage_files


def get_collection_path_regexes():  # type: () -> t.Tuple[t.Optional[t.Pattern], t.Optional[t.Pattern]]
    """Return a pair of regexes used for identifying and manipulating collection paths."""
    if data_context().content.collection:
        collection_search_re = re.compile(r'/%s/' % data_context().content.collection.directory)
        collection_sub_re = re.compile(r'^.*?/%s/' % data_context().content.collection.directory)
    else:
        collection_search_re = None
        collection_sub_re = None

    return collection_search_re, collection_sub_re


def get_python_modules():  # type: () -> t.Dict[str, str]
    """Return a dictionary of Ansible module names and their paths."""
    return dict((target.module, target.path) for target in list(walk_module_targets()) if target.path.endswith('.py'))


def enumerate_python_arcs(
        path,  # type: str
        coverage,  # type: coverage_module
        modules,  # type: t.Dict[str, str]
        collection_search_re,  # type: t.Optional[t.Pattern]
        collection_sub_re,  # type: t.Optional[t.Pattern]
):  # type: (...) -> t.Generator[t.Tuple[str, t.Set[t.Tuple[int, int]]]]
    """Enumerate Python code coverage arcs in the given file."""
    if os.path.getsize(path) == 0:
        display.warning('Empty coverage file: %s' % path, verbosity=2)
        return

    original = coverage.CoverageData()

    try:
        original.read_file(path)
    except Exception as ex:  # pylint: disable=locally-disabled, broad-except
        with open_binary_file(path) as file:
            header = file.read(6)

        if header == b'SQLite':
            display.error('File created by "coverage" 5.0+: %s' % os.path.relpath(path))
        else:
            display.error(u'%s' % ex)

        return

    for filename in original.measured_files():
        arcs = original.arcs(filename)

        if not arcs:
            # This is most likely due to using an unsupported version of coverage.
            display.warning('No arcs found for "%s" in coverage file: %s' % (filename, path))
            continue

        filename = sanitize_filename(filename, modules=modules, collection_search_re=collection_search_re, collection_sub_re=collection_sub_re)

        if not filename:
            continue

        yield filename, set(arcs)


def enumerate_powershell_lines(
        path,  # type: str
        collection_search_re,  # type: t.Optional[t.Pattern]
        collection_sub_re,  # type: t.Optional[t.Pattern]
):  # type: (...) -> t.Generator[t.Tuple[str, t.Dict[int, int]]]
    """Enumerate PowerShell code coverage lines in the given file."""
    if os.path.getsize(path) == 0:
        display.warning('Empty coverage file: %s' % path, verbosity=2)
        return

    try:
        coverage_run = read_json_file(path)
    except Exception as ex:  # pylint: disable=locally-disabled, broad-except
        display.error(u'%s' % ex)
        return

    for filename, hits in coverage_run.items():
        filename = sanitize_filename(filename, collection_search_re=collection_search_re, collection_sub_re=collection_sub_re)

        if not filename:
            continue

        if isinstance(hits, dict) and not hits.get('Line'):
            # Input data was previously aggregated and thus uses the standard ansible-test output format for PowerShell coverage.
            # This format differs from the more verbose format of raw coverage data from the remote Windows hosts.
            hits = dict((int(key), value) for key, value in hits.items())

            yield filename, hits
            continue

        # PowerShell unpacks arrays if there's only a single entry so this is a defensive check on that
        if not isinstance(hits, list):
            hits = [hits]

        hits = dict((hit['Line'], hit['HitCount']) for hit in hits if hit)

        yield filename, hits


def sanitize_filename(
        filename,  # type: str
        modules=None,  # type: t.Optional[t.Dict[str, str]]
        collection_search_re=None,  # type: t.Optional[t.Pattern]
        collection_sub_re=None,  # type: t.Optional[t.Pattern]
):  # type: (...) -> t.Optional[str]
    """Convert the given code coverage path to a local absolute path and return its, or None if the path is not valid."""
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

    filename = os.path.abspath(filename)  # make sure path is absolute (will be relative if previously exported)

    return filename


class PathChecker:
    """Checks code coverage paths to verify they are valid and reports on the findings."""
    def __init__(self, args, collection_search_re=None):  # type: (CoverageConfig, t.Optional[t.Pattern]) -> None
        self.args = args
        self.collection_search_re = collection_search_re
        self.invalid_paths = []
        self.invalid_path_chars = 0

    def check_path(self, path):  # type: (str) -> bool
        """Return True if the given coverage path is valid, otherwise display a warning and return False."""
        if os.path.isfile(to_bytes(path)):
            return True

        if self.collection_search_re and self.collection_search_re.search(path) and os.path.basename(path) == '__init__.py':
            # the collection loader uses implicit namespace packages, so __init__.py does not need to exist on disk
            # coverage is still reported for these non-existent files, but warnings are not needed
            return False

        self.invalid_paths.append(path)
        self.invalid_path_chars += len(path)

        if self.args.verbosity > 1:
            display.warning('Invalid coverage path: %s' % path)

        return False

    def report(self):  # type: () -> None
        """Display a warning regarding invalid paths if any were found."""
        if self.invalid_paths:
            display.warning('Ignored %d characters from %d invalid coverage path(s).' % (self.invalid_path_chars, len(self.invalid_paths)))
