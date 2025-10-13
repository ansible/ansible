"""Sanity test using pylint."""

from __future__ import annotations

import collections.abc as c
import itertools
import json
import os
import datetime
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
    REMOTE_ONLY_PYTHON_VERSIONS,
)

from ...io import (
    make_dirs,
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
)

from ...util_common import (
    run_command,
)

from ...ansible_util import (
    ansible_environment,
    get_collection_detail,
    CollectionDetail,
    CollectionDetailError,
    ResultType,
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

    def __init__(self) -> None:
        super().__init__()
        self.optional_error_codes.update([
            'ansible-deprecated-date',
            'too-complex',
        ])

    @property
    def error_code(self) -> t.Optional[str]:
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'ansible-test'

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' or is_subdir(target.path, 'bin')]

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        target_paths = set(target.path for target in self.filter_remote_targets(list(targets.targets)))

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

            if selected_paths := sorted(path for path in filtered_paths if path in target_paths):
                contexts.append((context_name, True, selected_paths))

            if selected_paths := sorted(path for path in filtered_paths if path not in target_paths):
                contexts.append((context_name, False, selected_paths))

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

        test_start = datetime.datetime.now(tz=datetime.timezone.utc)

        for context, is_target, context_paths in sorted(contexts):
            if not context_paths:
                continue

            context_start = datetime.datetime.now(tz=datetime.timezone.utc)
            messages += self.pylint(args, context, is_target, context_paths, plugin_dir, plugin_names, python, collection_detail)
            context_end = datetime.datetime.now(tz=datetime.timezone.utc)

            context_times.append('%s: %d (%s)' % (context, len(context_paths), context_end - context_start))

        test_end = datetime.datetime.now(tz=datetime.timezone.utc)

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
        is_target: bool,
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

        if is_target:
            context_label = 'target'
            min_python_version = REMOTE_ONLY_PYTHON_VERSIONS[0]
        else:
            context_label = 'controller'
            min_python_version = CONTROLLER_PYTHON_VERSIONS[0]

        load_plugins = set(plugin_names)
        plugin_options: dict[str, str] = {}

        # plugin: deprecated (ansible-test)
        if data_context().content.collection:
            plugin_options.update({'--collection-name': data_context().content.collection.full_name})
            plugin_options.update({'--collection-path': os.path.join(data_context().content.collection.root, data_context().content.collection.directory)})

            if collection_detail and collection_detail.version:
                plugin_options.update({'--collection-version': collection_detail.version})

        # plugin: pylint.extensions.mccabe
        if args.enable_optional_errors:
            load_plugins.add('pylint.extensions.mccabe')
            plugin_options.update({'--max-complexity': '20'})

        options = {
            '--py-version': min_python_version,
            '--load-plugins': ','.join(sorted(load_plugins)),
            '--rcfile': rcfile,
            '--jobs': '0',
            '--reports': 'n',
            '--output-format': 'json',
        }

        cmd = [python.path, '-m', 'pylint']
        cmd.extend(itertools.chain.from_iterable((options | plugin_options).items()))
        cmd.extend(paths)

        append_python_path = [plugin_dir]

        if data_context().content.collection:
            append_python_path.append(data_context().content.collection.root)

        env = ansible_environment(args)
        env['PYTHONPATH'] += os.path.pathsep + os.path.pathsep.join(append_python_path)

        # expose plugin paths for use in custom plugins
        env.update(dict(('ANSIBLE_TEST_%s_PATH' % k.upper(), os.path.abspath(v) + os.path.sep) for k, v in data_context().content.plugin_paths.items()))

        # Set PYLINTHOME to prevent pylint from checking for an obsolete directory, which can result in a test failure due to stderr output.
        # See: https://github.com/PyCQA/pylint/blob/e6c6bf5dfd61511d64779f54264b27a368c43100/pylint/constants.py#L148
        pylint_home = os.path.join(ResultType.TMP.path, 'pylint')
        make_dirs(pylint_home)
        env.update(PYLINTHOME=pylint_home)

        if paths:
            display.info(f'Checking {len(paths)} file(s) in context {context!r} ({context_label}) with config: {rcfile}', verbosity=1)

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

        expected_paths = set(paths)

        unexpected_messages = [message for message in messages if message["path"] not in expected_paths]
        messages = [message for message in messages if message["path"] in expected_paths]

        for unexpected_message in unexpected_messages:
            display.info(f"Unexpected message: {json.dumps(unexpected_message)}", verbosity=4)

        if unexpected_messages:
            display.notice(f"Discarded {len(unexpected_messages)} unexpected messages. Use -vvvv to display.")

        return messages
