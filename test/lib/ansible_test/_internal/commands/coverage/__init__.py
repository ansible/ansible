"""Common logic for the coverage subcommand."""
from __future__ import annotations

import collections.abc as c
import errno
import json
import os
import re
import typing as t

from ...encoding import (
    to_bytes,
)

from ...io import (
    read_text_file,
    read_json_file,
)

from ...util import (
    ApplicationError,
    common_environment,
    display,
    ANSIBLE_TEST_DATA_ROOT,
)

from ...util_common import (
    intercept_python,
    ResultType,
)

from ...config import (
    EnvironmentConfig,
)

from ...python_requirements import (
    install_requirements,
)

from ... target import (
    walk_module_targets,
)

from ...data import (
    data_context,
)

from ...pypi_proxy import (
    configure_pypi_proxy,
)

from ...provisioning import (
    HostState,
)

from ...coverage_util import (
    get_coverage_file_schema_version,
    CoverageError,
    CONTROLLER_COVERAGE_VERSION,
)

if t.TYPE_CHECKING:
    import coverage as coverage_module

COVERAGE_GROUPS = ('command', 'target', 'environment', 'version')
COVERAGE_CONFIG_PATH = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'coveragerc')
COVERAGE_OUTPUT_FILE_NAME = 'coverage'


class CoverageConfig(EnvironmentConfig):
    """Configuration for the coverage command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args, 'coverage')


def initialize_coverage(args: CoverageConfig, host_state: HostState) -> coverage_module:
    """Delegate execution if requested, install requirements, then import and return the coverage module. Raises an exception if coverage is not available."""
    configure_pypi_proxy(args, host_state.controller_profile)  # coverage
    install_requirements(args, host_state.controller_profile.python, coverage=True)  # coverage

    try:
        import coverage
    except ImportError:
        coverage = None

    coverage_required_version = CONTROLLER_COVERAGE_VERSION.coverage_version

    if not coverage:
        raise ApplicationError(f'Version {coverage_required_version} of the Python "coverage" module must be installed to use this command.')

    if coverage.__version__ != coverage_required_version:
        raise ApplicationError(f'Version {coverage_required_version} of the Python "coverage" module is required. Version {coverage.__version__} was found.')

    return coverage


def run_coverage(args: CoverageConfig, host_state: HostState, output_file: str, command: str, cmd: list[str]) -> None:
    """Run the coverage cli tool with the specified options."""
    env = common_environment()
    env.update(dict(COVERAGE_FILE=output_file))

    cmd = ['python', '-m', 'coverage.__main__', command, '--rcfile', COVERAGE_CONFIG_PATH] + cmd

    stdout, stderr = intercept_python(args, host_state.controller_profile.python, cmd, env, capture=True)

    stdout = (stdout or '').strip()
    stderr = (stderr or '').strip()

    if stdout:
        display.info(stdout)

    if stderr:
        display.warning(stderr)


def get_all_coverage_files() -> list[str]:
    """Return a list of all coverage file paths."""
    return get_python_coverage_files() + get_powershell_coverage_files()


def get_python_coverage_files(path: t.Optional[str] = None) -> list[str]:
    """Return the list of Python coverage file paths."""
    return get_coverage_files('python', path)


def get_powershell_coverage_files(path: t.Optional[str] = None) -> list[str]:
    """Return the list of PowerShell coverage file paths."""
    return get_coverage_files('powershell', path)


def get_coverage_files(language: str, path: t.Optional[str] = None) -> list[str]:
    """Return the list of coverage file paths for the given language."""
    coverage_dir = path or ResultType.COVERAGE.path

    try:
        coverage_files = [os.path.join(coverage_dir, f) for f in os.listdir(coverage_dir)
                          if '=coverage.' in f and '=%s' % language in f]
    except IOError as ex:
        if ex.errno == errno.ENOENT:
            return []

        raise

    return coverage_files


def get_collection_path_regexes() -> tuple[t.Optional[t.Pattern], t.Optional[t.Pattern]]:
    """Return a pair of regexes used for identifying and manipulating collection paths."""
    if data_context().content.collection:
        collection_search_re = re.compile(r'/%s/' % data_context().content.collection.directory)
        collection_sub_re = re.compile(r'^.*?/%s/' % data_context().content.collection.directory)
    else:
        collection_search_re = None
        collection_sub_re = None

    return collection_search_re, collection_sub_re


def get_python_modules() -> dict[str, str]:
    """Return a dictionary of Ansible module names and their paths."""
    return dict((target.module, target.path) for target in list(walk_module_targets()) if target.path.endswith('.py'))


def enumerate_python_arcs(
        path: str,
        coverage: coverage_module,
        modules: dict[str, str],
        collection_search_re: t.Optional[t.Pattern],
        collection_sub_re: t.Optional[t.Pattern],
) -> c.Generator[tuple[str, set[tuple[int, int]]], None, None]:
    """Enumerate Python code coverage arcs in the given file."""
    if os.path.getsize(path) == 0:
        display.warning('Empty coverage file: %s' % path, verbosity=2)
        return

    try:
        arc_data = read_python_coverage(path, coverage)
    except CoverageError as ex:
        display.error(str(ex))
        return

    for filename, arcs in arc_data.items():
        if not arcs:
            # This is most likely due to using an unsupported version of coverage.
            display.warning('No arcs found for "%s" in coverage file: %s' % (filename, path))
            continue

        filename = sanitize_filename(filename, modules=modules, collection_search_re=collection_search_re, collection_sub_re=collection_sub_re)

        if not filename:
            continue

        yield filename, set(arcs)


PythonArcs = dict[str, list[tuple[int, int]]]
"""Python coverage arcs."""


def read_python_coverage(path: str, coverage: coverage_module) -> PythonArcs:
    """Return coverage arcs from the specified coverage file. Raises a CoverageError exception if coverage cannot be read."""
    try:
        return read_python_coverage_native(path, coverage)
    except CoverageError as ex:
        schema_version = get_coverage_file_schema_version(path)

        if schema_version == CONTROLLER_COVERAGE_VERSION.schema_version:
            raise CoverageError(path, f'Unexpected failure reading supported schema version {schema_version}.') from ex

    if schema_version == 0:
        return read_python_coverage_legacy(path)

    raise CoverageError(path, f'Unsupported schema version: {schema_version}')


def read_python_coverage_native(path: str, coverage: coverage_module) -> PythonArcs:
    """Return coverage arcs from the specified coverage file using the coverage API."""
    try:
        data = coverage.CoverageData(path)
        data.read()
        arcs = {filename: data.arcs(filename) for filename in data.measured_files()}
    except Exception as ex:
        raise CoverageError(path, f'Error reading coverage file using coverage API: {ex}') from ex

    return arcs


def read_python_coverage_legacy(path: str) -> PythonArcs:
    """Return coverage arcs from the specified coverage file, which must be in the legacy JSON format."""
    try:
        contents = read_text_file(path)
        contents = re.sub(r'''^!coverage.py: This is a private format, don't read it directly!''', '', contents)
        data = json.loads(contents)
        arcs: PythonArcs = {filename: [tuple(arc) for arc in arcs] for filename, arcs in data['arcs'].items()}
    except Exception as ex:
        raise CoverageError(path, f'Error reading JSON coverage file: {ex}') from ex

    return arcs


def enumerate_powershell_lines(
        path: str,
        collection_search_re: t.Optional[t.Pattern],
        collection_sub_re: t.Optional[t.Pattern],
) -> c.Generator[tuple[str, dict[int, int]], None, None]:
    """Enumerate PowerShell code coverage lines in the given file."""
    if os.path.getsize(path) == 0:
        display.warning('Empty coverage file: %s' % path, verbosity=2)
        return

    try:
        coverage_run = read_json_file(path)
    except Exception as ex:  # pylint: disable=locally-disabled, broad-except
        display.error('%s' % ex)
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
        filename: str,
        modules: t.Optional[dict[str, str]] = None,
        collection_search_re: t.Optional[t.Pattern] = None,
        collection_sub_re: t.Optional[t.Pattern] = None,
) -> t.Optional[str]:
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
    def __init__(self, args: CoverageConfig, collection_search_re: t.Optional[t.Pattern] = None) -> None:
        self.args = args
        self.collection_search_re = collection_search_re
        self.invalid_paths: list[str] = []
        self.invalid_path_chars = 0

    def check_path(self, path: str) -> bool:
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

    def report(self) -> None:
        """Display a warning regarding invalid paths if any were found."""
        if self.invalid_paths:
            display.warning('Ignored %d characters from %d invalid coverage path(s).' % (self.invalid_path_chars, len(self.invalid_paths)))
