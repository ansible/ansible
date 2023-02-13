"""Sanity test for proper import exception handling."""
from __future__ import annotations

import collections.abc as c
import os

from . import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
    TARGET_SANITY_ROOT,
    SanityTargets,
    create_sanity_virtualenv,
    check_sanity_virtualenv_yaml,
)

from ...constants import (
    CONTROLLER_MIN_PYTHON_VERSION,
    REMOTE_ONLY_PYTHON_VERSIONS,
)

from ...test import (
    TestResult,
)

from ...target import (
    TestTarget,
)

from ...util import (
    cache,
    SubprocessError,
    display,
    parse_to_list_of_dict,
    is_subdir,
    ANSIBLE_TEST_TOOLS_ROOT,
)

from ...util_common import (
    ResultType,
    create_temp_dir,
)

from ...ansible_util import (
    ansible_environment,
)

from ...python_requirements import (
    PipUnavailableError,
    install_requirements,
)

from ...config import (
    SanityConfig,
)

from ...coverage_util import (
    cover_python,
)

from ...data import (
    data_context,
)

from ...host_configs import (
    PythonConfig,
)

from ...venv import (
    get_virtualenv_version,
)


def _get_module_test(module_restrictions: bool) -> c.Callable[[str], bool]:
    """Create a predicate which tests whether a path can be used by modules or not."""
    module_path = data_context().content.module_path
    module_utils_path = data_context().content.module_utils_path
    if module_restrictions:
        return lambda path: is_subdir(path, module_path) or is_subdir(path, module_utils_path)
    return lambda path: not (is_subdir(path, module_path) or is_subdir(path, module_utils_path))


class ImportTest(SanityMultipleVersion):
    """Sanity test for proper import exception handling."""

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        if data_context().content.is_ansible:
            # all of ansible-core must pass the import test, not just plugins/modules
            # modules/module_utils will be tested using the module context
            # everything else will be tested using the plugin context
            paths = ['lib/ansible']
        else:
            # only plugins/modules must pass the import test for collections
            paths = list(data_context().content.plugin_paths.values())

        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' and
                any(is_subdir(target.path, path) for path in paths)]

    @property
    def needs_pypi(self) -> bool:
        """True if the test requires PyPI, otherwise False."""
        return True

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        settings = self.load_processor(args, python.version)

        paths = [target.path for target in targets.include]

        if python.version.startswith('2.') and (get_virtualenv_version(args, python.path) or (0,)) < (13,):
            # hack to make sure that virtualenv is available under Python 2.x
            # on Python 3.x we can use the built-in venv
            # version 13+ is required to use the `--no-wheel` option
            try:
                install_requirements(args, python, virtualenv=True, controller=False)  # sanity (import)
            except PipUnavailableError as ex:
                display.warning(str(ex))

        temp_root = os.path.join(ResultType.TMP.path, 'sanity', 'import')

        messages = []

        for import_type, test in (
            ('module', _get_module_test(True)),
            ('plugin', _get_module_test(False)),
        ):
            if import_type == 'plugin' and python.version in REMOTE_ONLY_PYTHON_VERSIONS:
                continue

            data = '\n'.join([path for path in paths if test(path)])

            if not data and not args.prime_venvs:
                continue

            virtualenv_python = create_sanity_virtualenv(args, python, f'{self.name}.{import_type}', coverage=args.coverage, minimize=True)

            if not virtualenv_python:
                display.warning(f'Skipping sanity test "{self.name}" on Python {python.version} due to missing virtual environment support.')
                return SanitySkipped(self.name, python.version)

            virtualenv_yaml = check_sanity_virtualenv_yaml(virtualenv_python)

            if virtualenv_yaml is False:
                display.warning(f'Sanity test "{self.name}" ({import_type}) on Python {python.version} may be slow due to missing libyaml support in PyYAML.')

            env = ansible_environment(args, color=False)

            env.update(
                SANITY_TEMP_PATH=ResultType.TMP.path,
                SANITY_IMPORTER_TYPE=import_type,
            )

            if data_context().content.collection:
                external_python = create_sanity_virtualenv(args, args.controller_python, self.name)

                env.update(
                    SANITY_COLLECTION_FULL_NAME=data_context().content.collection.full_name,
                    SANITY_EXTERNAL_PYTHON=external_python.path,
                    SANITY_YAML_TO_JSON=os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'yaml_to_json.py'),
                    ANSIBLE_CONTROLLER_MIN_PYTHON_VERSION=CONTROLLER_MIN_PYTHON_VERSION,
                    PYTHONPATH=':'.join((get_ansible_test_python_path(), env["PYTHONPATH"])),
                )

            if args.prime_venvs:
                continue

            display.info(import_type + ': ' + data, verbosity=4)

            cmd = ['importer.py']

            # add the importer to the path so it can be accessed through the coverage injector
            env.update(
                PATH=os.pathsep.join([os.path.join(TARGET_SANITY_ROOT, 'import'), env['PATH']]),
            )

            try:
                stdout, stderr = cover_python(args, virtualenv_python, cmd, self.name, env, capture=True, data=data)

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

        if args.prime_venvs:
            return SanitySkipped(self.name, python_version=python.version)

        results = settings.process_errors(messages, paths)

        if results:
            return SanityFailure(self.name, messages=results, python_version=python.version)

        return SanitySuccess(self.name, python_version=python.version)


@cache
def get_ansible_test_python_path() -> str:
    """
    Return a directory usable for PYTHONPATH, containing only the ansible-test collection loader.
    The temporary directory created will be cached for the lifetime of the process and cleaned up at exit.
    """
    python_path = create_temp_dir(prefix='ansible-test-')
    return python_path
