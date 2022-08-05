"""Sanity test using pylint."""
from __future__ import annotations

import collections.abc as c
import itertools
import json
import os
import datetime
import configparser
import typing as t

from . import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    SANITY_ROOT,
)

from ...constants import (
    CONTROLLER_PYTHON_VERSIONS,
)

from ...test import (
    TestResult,
)

from ...target import (
    TestTarget,
)

from ...util import (
    SubprocessError,
    display,
    is_subdir,
    str_to_version,
)

from ...util_common import (
    run_command,
)

from ...ansible_util import (
    ansible_environment,
    get_collection_detail,
    CollectionDetail,
    CollectionDetailError,
)

from ...config import (
    SanityConfig,
)

from ...data import (
    data_context,
)

from ...host_configs import (
    PythonConfig,
)


class PylintTest(SanitySingleVersion):
    """Sanity test using pylint."""
    def __init__(self):
        super().__init__()
        self.optional_error_codes.update([
            'ansible-deprecated-date',
            'too-complex',
        ])

    @property
    def supported_python_versions(self) -> t.Optional[tuple[str, ...]]:
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        return tuple(version for version in CONTROLLER_PYTHON_VERSIONS if str_to_version(version) < (3, 11))

    @property
    def error_code(self) -> t.Optional[str]:
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'ansible-test'

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' or is_subdir(target.path, 'bin')]

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        plugin_dir = os.path.join(SANITY_ROOT, 'pylint', 'plugins')
        plugin_names = sorted(p[0] for p in [
            os.path.splitext(p) for p in os.listdir(plugin_dir)] if p[1] == '.py' and p[0] != '__init__')

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        module_paths = [os.path.relpath(p, data_context().content.module_path).split(os.path.sep) for p in
                        paths if is_subdir(p, data_context().content.module_path)]
        module_dirs = sorted({p[0] for p in module_paths if len(p) > 1})

        large_module_group_threshold = 500
        large_module_groups = [key for key, value in
                               itertools.groupby(module_paths, lambda p: p[0] if len(p) > 1 else '') if len(list(value)) > large_module_group_threshold]

        large_module_group_paths = [os.path.relpath(p, data_context().content.module_path).split(os.path.sep) for p in paths
                                    if any(is_subdir(p, os.path.join(data_context().content.module_path, g)) for g in large_module_groups)]
        large_module_group_dirs = sorted({os.path.sep.join(p[:2]) for p in large_module_group_paths if len(p) > 2})

        contexts = []
        remaining_paths = set(paths)

        def add_context(available_paths: set[str], context_name: str, context_filter: c.Callable[[str], bool]) -> None:
            """Add the specified context to the context list, consuming available paths that match the given context filter."""
            filtered_paths = set(p for p in available_paths if context_filter(p))
            contexts.append((context_name, sorted(filtered_paths)))
            available_paths -= filtered_paths

        def filter_path(path_filter: str = None) -> c.Callable[[str], bool]:
            """Return a function that filters out paths which are not a subdirectory of the given path."""
            def context_filter(path_to_filter: str) -> bool:
                """Return true if the given path matches, otherwise return False."""
                return is_subdir(path_to_filter, path_filter)

            return context_filter

        for large_module_dir in large_module_group_dirs:
            add_context(remaining_paths, 'modules/%s' % large_module_dir, filter_path(os.path.join(data_context().content.module_path, large_module_dir)))

        for module_dir in module_dirs:
            add_context(remaining_paths, 'modules/%s' % module_dir, filter_path(os.path.join(data_context().content.module_path, module_dir)))

        add_context(remaining_paths, 'modules', filter_path(data_context().content.module_path))
        add_context(remaining_paths, 'module_utils', filter_path(data_context().content.module_utils_path))

        add_context(remaining_paths, 'units', filter_path(data_context().content.unit_path))

        if data_context().content.collection:
            add_context(remaining_paths, 'collection', lambda p: True)
        else:
            add_context(remaining_paths, 'validate-modules', filter_path('test/lib/ansible_test/_util/controller/sanity/validate-modules/'))
            add_context(remaining_paths, 'validate-modules-unit', filter_path('test/lib/ansible_test/tests/validate-modules-unit/'))
            add_context(remaining_paths, 'code-smell', filter_path('test/lib/ansible_test/_util/controller/sanity/code-smell/'))
            add_context(remaining_paths, 'ansible-test-target', filter_path('test/lib/ansible_test/_util/target/'))
            add_context(remaining_paths, 'ansible-test', filter_path('test/lib/'))
            add_context(remaining_paths, 'test', filter_path('test/'))
            add_context(remaining_paths, 'hacking', filter_path('hacking/'))
            add_context(remaining_paths, 'ansible', lambda p: True)

        messages = []
        context_times = []

        collection_detail = None

        if data_context().content.collection:
            try:
                collection_detail = get_collection_detail(python)

                if not collection_detail.version:
                    display.warning('Skipping pylint collection version checks since no collection version was found.')
            except CollectionDetailError as ex:
                display.warning('Skipping pylint collection version checks since collection detail loading failed: %s' % ex.reason)

        test_start = datetime.datetime.utcnow()

        for context, context_paths in sorted(contexts):
            if not context_paths:
                continue

            context_start = datetime.datetime.utcnow()
            messages += self.pylint(args, context, context_paths, plugin_dir, plugin_names, python, collection_detail)
            context_end = datetime.datetime.utcnow()

            context_times.append('%s: %d (%s)' % (context, len(context_paths), context_end - context_start))

        test_end = datetime.datetime.utcnow()

        for context_time in context_times:
            display.info(context_time, verbosity=4)

        display.info('total: %d (%s)' % (len(paths), test_end - test_start), verbosity=4)

        errors = [SanityMessage(
            message=m['message'].replace('\n', ' '),
            path=m['path'],
            line=int(m['line']),
            column=int(m['column']),
            level=m['type'],
            code=m['symbol'],
        ) for m in messages]

        if args.explain:
            return SanitySuccess(self.name)

        errors = settings.process_errors(errors, paths)

        if errors:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)

    @staticmethod
    def pylint(
            args: SanityConfig,
            context: str,
            paths: list[str],
            plugin_dir: str,
            plugin_names: list[str],
            python: PythonConfig,
            collection_detail: CollectionDetail,
    ) -> list[dict[str, str]]:
        """Run pylint using the config specified by the context on the specified paths."""
        rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', context.split('/')[0] + '.cfg')

        if not os.path.exists(rcfile):
            if data_context().content.collection:
                rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', 'collection.cfg')
            else:
                rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', 'default.cfg')

        parser = configparser.ConfigParser()
        parser.read(rcfile)

        if parser.has_section('ansible-test'):
            config = dict(parser.items('ansible-test'))
        else:
            config = {}

        disable_plugins = set(i.strip() for i in config.get('disable-plugins', '').split(',') if i)
        load_plugins = set(plugin_names + ['pylint.extensions.mccabe']) - disable_plugins

        cmd = [
            python.path,
            '-m', 'pylint',
            '--jobs', '0',
            '--reports', 'n',
            '--max-line-length', '160',
            '--max-complexity', '20',
            '--rcfile', rcfile,
            '--output-format', 'json',
            '--load-plugins', ','.join(load_plugins),
        ] + paths

        if data_context().content.collection:
            cmd.extend(['--collection-name', data_context().content.collection.full_name])

            if collection_detail and collection_detail.version:
                cmd.extend(['--collection-version', collection_detail.version])

        append_python_path = [plugin_dir]

        if data_context().content.collection:
            append_python_path.append(data_context().content.collection.root)

        env = ansible_environment(args)
        env['PYTHONPATH'] += os.path.pathsep + os.path.pathsep.join(append_python_path)

        # expose plugin paths for use in custom plugins
        env.update(dict(('ANSIBLE_TEST_%s_PATH' % k.upper(), os.path.abspath(v) + os.path.sep) for k, v in data_context().content.plugin_paths.items()))

        if paths:
            display.info('Checking %d file(s) in context "%s" with config: %s' % (len(paths), context, rcfile), verbosity=1)

            try:
                stdout, stderr = run_command(args, cmd, env=env, capture=True)
                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr or status >= 32:
                raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)
        else:
            stdout = None

        if not args.explain and stdout:
            messages = json.loads(stdout)
        else:
            messages = []

        return messages
