"""Sanity test for proper import exception handling."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from .. import types as t

from ..sanity import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
    SANITY_ROOT,
)

from ..target import (
    TestTarget,
)

from ..util import (
    ANSIBLE_TEST_DATA_ROOT,
    SubprocessError,
    remove_tree,
    display,
    parse_to_list_of_dict,
    is_subdir,
    generate_pip_command,
    find_python,
    get_hash,
    REMOTE_ONLY_PYTHON_VERSIONS,
)

from ..util_common import (
    intercept_command,
    run_command,
    ResultType,
)

from ..ansible_util import (
    ansible_environment,
)

from ..executor import (
    generate_pip_install,
    install_cryptography,
)

from ..config import (
    SanityConfig,
)

from ..coverage_util import (
    coverage_context,
)

from ..venv import (
    create_virtual_environment,
)

from ..data import (
    data_context,
)


def _get_module_test(module_restrictions):  # type: (bool) -> t.Callable[[str], bool]
    """Create a predicate which tests whether a path can be used by modules or not."""
    module_path = data_context().content.module_path
    module_utils_path = data_context().content.module_utils_path
    if module_restrictions:
        return lambda path: is_subdir(path, module_path) or is_subdir(path, module_utils_path)
    return lambda path: not (is_subdir(path, module_path) or is_subdir(path, module_utils_path))


class ImportTest(SanityMultipleVersion):
    """Sanity test for proper import exception handling."""
    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' and
                any(is_subdir(target.path, path) for path in data_context().content.plugin_paths.values())]

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        capture_pip = args.verbosity < 2

        python = find_python(python_version)

        if python_version.startswith('2.') and args.requirements:
            # hack to make sure that virtualenv is available under Python 2.x
            # on Python 3.x we can use the built-in venv
            pip = generate_pip_command(python)
            run_command(args, generate_pip_install(pip, '', packages=['virtualenv']), capture=capture_pip)

        settings = self.load_processor(args, python_version)

        paths = [target.path for target in targets.include]

        env = ansible_environment(args, color=False)

        temp_root = os.path.join(ResultType.TMP.path, 'sanity', 'import')

        messages = []

        for import_type, test, add_ansible_requirements in (
                ('module', _get_module_test(True), False),
                ('plugin', _get_module_test(False), True),
        ):
            if import_type == 'plugin' and python_version in REMOTE_ONLY_PYTHON_VERSIONS:
                continue

            data = '\n'.join([path for path in paths if test(path)])
            if not data:
                continue

            requirements_file = None

            # create a clean virtual environment to minimize the available imports beyond the python standard library
            virtual_environment_dirname = 'minimal-py%s' % python_version.replace('.', '')
            if add_ansible_requirements:
                requirements_file = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'requirements', 'sanity.import-plugins.txt')
                virtual_environment_dirname += '-requirements-%s' % get_hash(requirements_file)
            virtual_environment_path = os.path.join(temp_root, virtual_environment_dirname)
            virtual_environment_bin = os.path.join(virtual_environment_path, 'bin')

            remove_tree(virtual_environment_path)

            if not create_virtual_environment(args, python_version, virtual_environment_path):
                display.warning("Skipping sanity test '%s' on Python %s due to missing virtual environment support." % (self.name, python_version))
                return SanitySkipped(self.name, python_version)

            # add the importer to our virtual environment so it can be accessed through the coverage injector
            importer_path = os.path.join(virtual_environment_bin, 'importer.py')
            yaml_to_json_path = os.path.join(virtual_environment_bin, 'yaml_to_json.py')
            if not args.explain:
                os.symlink(os.path.abspath(os.path.join(SANITY_ROOT, 'import', 'importer.py')), importer_path)
                os.symlink(os.path.abspath(os.path.join(SANITY_ROOT, 'import', 'yaml_to_json.py')), yaml_to_json_path)

            # activate the virtual environment
            env['PATH'] = '%s:%s' % (virtual_environment_bin, env['PATH'])

            env.update(
                SANITY_TEMP_PATH=ResultType.TMP.path,
                SANITY_IMPORTER_TYPE=import_type,
            )

            if data_context().content.collection:
                env.update(
                    SANITY_COLLECTION_FULL_NAME=data_context().content.collection.full_name,
                    SANITY_EXTERNAL_PYTHON=python,
                )

            virtualenv_python = os.path.join(virtual_environment_bin, 'python')
            virtualenv_pip = generate_pip_command(virtualenv_python)

            # make sure requirements are installed if needed
            if requirements_file:
                install_cryptography(args, virtualenv_python, python_version, virtualenv_pip)
                run_command(args, generate_pip_install(virtualenv_pip, 'sanity', context='import-plugins'), env=env, capture=capture_pip)

            # make sure coverage is available in the virtual environment if needed
            if args.coverage:
                run_command(args, generate_pip_install(virtualenv_pip, '', packages=['setuptools']), env=env, capture=capture_pip)
                run_command(args, generate_pip_install(virtualenv_pip, '', packages=['coverage']), env=env, capture=capture_pip)

            try:
                # In some environments pkg_resources is installed as a separate pip package which needs to be removed.
                # For example, using Python 3.8 on Ubuntu 18.04 a virtualenv is created with only pip and setuptools.
                # However, a venv is created with an additional pkg-resources package which is independent of setuptools.
                # Making sure pkg-resources is removed preserves the import test consistency between venv and virtualenv.
                # Additionally, in the above example, the pyparsing package vendored with pkg-resources is out-of-date and generates deprecation warnings.
                # Thus it is important to remove pkg-resources to prevent system installed packages from generating deprecation warnings.
                run_command(args, virtualenv_pip + ['uninstall', '--disable-pip-version-check', '-y', 'pkg-resources'], env=env, capture=capture_pip)
            except SubprocessError:
                pass

            run_command(args, virtualenv_pip + ['uninstall', '--disable-pip-version-check', '-y', 'setuptools'], env=env, capture=capture_pip)
            run_command(args, virtualenv_pip + ['uninstall', '--disable-pip-version-check', '-y', 'pip'], env=env, capture=capture_pip)

            display.info(import_type + ': ' + data, verbosity=4)

            cmd = ['importer.py']

            try:
                with coverage_context(args):
                    stdout, stderr = intercept_command(args, cmd, self.name, env, capture=True, data=data, python_version=python_version,
                                                       virtualenv=virtualenv_python)

                if stdout or stderr:
                    raise SubprocessError(cmd, stdout=stdout, stderr=stderr)
            except SubprocessError as ex:
                if ex.status != 10 or ex.stderr or not ex.stdout:
                    raise

                pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

                parsed = parse_to_list_of_dict(pattern, ex.stdout)

                relative_temp_root = os.path.relpath(temp_root, data_context().content.root) + os.path.sep

                messages += [SanityMessage(
                    message=r['message'],
                    path=os.path.relpath(r['path'], relative_temp_root) if r['path'].startswith(relative_temp_root) else r['path'],
                    line=int(r['line']),
                    column=int(r['column']),
                ) for r in parsed]

        results = settings.process_errors(messages, paths)

        if results:
            return SanityFailure(self.name, messages=results, python_version=python_version)

        return SanitySuccess(self.name, python_version=python_version)
