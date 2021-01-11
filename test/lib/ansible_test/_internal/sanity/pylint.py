"""Sanity test using pylint."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import itertools
import json
import os
import datetime

from .. import types as t

from ..sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SANITY_ROOT,
)

from ..target import (
    TestTarget,
)

from ..util import (
    SubprocessError,
    display,
    ConfigParser,
    is_subdir,
    find_python,
)

from ..util_common import (
    run_command,
)

from ..ansible_util import (
    ansible_environment,
    get_collection_detail,
    CollectionDetail,
    CollectionDetailError,
)

from ..config import (
    SanityConfig,
)

from ..data import (
    data_context,
)


class PylintTest(SanitySingleVersion):
    """Sanity test using pylint."""

    def __init__(self):
        super(PylintTest, self).__init__()
        self.optional_error_codes.update([
            'ansible-deprecated-date',
            'too-complex',
        ])

    @property
    def error_code(self):  # type: () -> t.Optional[str]
        """Error code for ansible-test matching the format used by the underlying test program, or None if the program does not use error codes."""
        return 'ansible-test'

    @property
    def supported_python_versions(self):  # type: () -> t.Optional[t.Tuple[str, ...]]
        """A tuple of supported Python versions or None if the test does not depend on specific Python versions."""
        # Python 3.9 is not supported on pylint < 2.5.0.
        # Unfortunately pylint 2.5.0 and later include an unfixed regression.
        # See: https://github.com/PyCQA/pylint/issues/3701
        return tuple(python_version for python_version in super(PylintTest, self).supported_python_versions if python_version not in ('3.9',))

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if os.path.splitext(target.path)[1] == '.py' or is_subdir(target.path, 'bin')]

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        plugin_dir = os.path.join(SANITY_ROOT, 'pylint', 'plugins')
        plugin_names = sorted(p[0] for p in [
            os.path.splitext(p) for p in os.listdir(plugin_dir)] if p[1] == '.py' and p[0] != '__init__')

        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        module_paths = [os.path.relpath(p, data_context().content.module_path).split(os.path.sep) for p in
                        paths if is_subdir(p, data_context().content.module_path)]
        module_dirs = sorted(set([p[0] for p in module_paths if len(p) > 1]))

        large_module_group_threshold = 500
        large_module_groups = [key for key, value in
                               itertools.groupby(module_paths, lambda p: p[0] if len(p) > 1 else '') if len(list(value)) > large_module_group_threshold]

        large_module_group_paths = [os.path.relpath(p, data_context().content.module_path).split(os.path.sep) for p in paths
                                    if any(is_subdir(p, os.path.join(data_context().content.module_path, g)) for g in large_module_groups)]
        large_module_group_dirs = sorted(set([os.path.sep.join(p[:2]) for p in large_module_group_paths if len(p) > 2]))

        contexts = []
        remaining_paths = set(paths)

        def add_context(available_paths, context_name, context_filter):
            """
            :type available_paths: set[str]
            :type context_name: str
            :type context_filter: (str) -> bool
            """
            filtered_paths = set(p for p in available_paths if context_filter(p))
            contexts.append((context_name, sorted(filtered_paths)))
            available_paths -= filtered_paths

        def filter_path(path_filter=None):
            """
            :type path_filter: str
            :rtype: (str) -> bool
            """
            def context_filter(path_to_filter):
                """
                :type path_to_filter: str
                :rtype: bool
                """
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
            add_context(remaining_paths, 'validate-modules', filter_path('test/lib/ansible_test/_data/sanity/validate-modules/'))
            add_context(remaining_paths, 'validate-modules-unit', filter_path('test/lib/ansible_test/tests/validate-modules-unit/'))
            add_context(remaining_paths, 'sanity', filter_path('test/lib/ansible_test/_data/sanity/'))
            add_context(remaining_paths, 'ansible-test', filter_path('test/lib/'))
            add_context(remaining_paths, 'test', filter_path('test/'))
            add_context(remaining_paths, 'hacking', filter_path('hacking/'))
            add_context(remaining_paths, 'ansible', lambda p: True)

        messages = []
        context_times = []

        python = find_python(python_version)

        collection_detail = None

        if data_context().content.collection:
            try:
                collection_detail = get_collection_detail(args, python)

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
            args,  # type: SanityConfig
            context,  # type: str
            paths,  # type: t.List[str]
            plugin_dir,  # type: str
            plugin_names,  # type: t.List[str]
            python,  # type: str
            collection_detail,  # type: CollectionDetail
    ):  # type: (...) -> t.List[t.Dict[str, str]]
        """Run pylint using the config specified by the context on the specified paths."""
        rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', context.split('/')[0] + '.cfg')

        if not os.path.exists(rcfile):
            if data_context().content.collection:
                rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', 'collection.cfg')
            else:
                rcfile = os.path.join(SANITY_ROOT, 'pylint', 'config', 'default.cfg')

        parser = ConfigParser()
        parser.read(rcfile)

        if parser.has_section('ansible-test'):
            config = dict(parser.items('ansible-test'))
        else:
            config = dict()

        disable_plugins = set(i.strip() for i in config.get('disable-plugins', '').split(',') if i)
        load_plugins = set(plugin_names + ['pylint.extensions.mccabe']) - disable_plugins

        cmd = [
            python,
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
