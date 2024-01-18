"""Sanity test for ansible-doc."""
from __future__ import annotations

import collections
import json
import os
import re

from . import (
    DOCUMENTABLE_PLUGINS,
    MULTI_FILE_PLUGINS,
    SanitySingleVersion,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    SanityMessage,
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

from ...ansible_util import (
    ansible_environment,
    intercept_python,
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


class AnsibleDocTest(SanitySingleVersion):
    """Sanity test for ansible-doc."""

    def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        plugin_paths = [plugin_path for plugin_type, plugin_path in data_context().content.plugin_paths.items() if plugin_type in DOCUMENTABLE_PLUGINS]

        return [target for target in targets
                if os.path.splitext(target.path)[1] == '.py'
                and os.path.basename(target.path) != '__init__.py'
                and any(is_subdir(target.path, path) for path in plugin_paths)
                ]

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        doc_targets: dict[str, list[str]] = collections.defaultdict(list)

        remap_types = dict(
            modules='module',
        )

        for plugin_type, plugin_path in data_context().content.plugin_paths.items():
            plugin_type = remap_types.get(plugin_type, plugin_type)

            for plugin_file_path in [target.name for target in targets.include if is_subdir(target.path, plugin_path)]:
                plugin_parts = os.path.relpath(plugin_file_path, plugin_path).split(os.path.sep)
                plugin_name = os.path.splitext(plugin_parts[-1])[0]

                if plugin_name.startswith('_'):
                    plugin_name = plugin_name[1:]

                plugin_fqcn = data_context().content.prefix + '.'.join(plugin_parts[:-1] + [plugin_name])

                doc_targets[plugin_type].append(plugin_fqcn)

        env = ansible_environment(args, color=False)

        for doc_type in MULTI_FILE_PLUGINS:
            if doc_targets.get(doc_type):
                # List plugins
                cmd = ['ansible-doc', '-l', '--json', '-t', doc_type]
                prefix = data_context().content.prefix if data_context().content.collection else 'ansible.builtin.'
                cmd.append(prefix[:-1])
                try:
                    stdout, stderr = intercept_python(args, python, cmd, env, capture=True)
                    status = 0
                except SubprocessError as ex:
                    stdout = ex.stdout
                    stderr = ex.stderr
                    status = ex.status

                if status:
                    summary = '%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr)
                    return SanityFailure(self.name, summary=summary)

                if stdout:
                    display.info(stdout.strip(), verbosity=3)

                if stderr:
                    summary = 'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
                    return SanityFailure(self.name, summary=summary)

                if args.explain:
                    continue

                plugin_list_json = json.loads(stdout)
                doc_targets[doc_type] = []
                for plugin_name, plugin_value in sorted(plugin_list_json.items()):
                    if plugin_value != 'UNDOCUMENTED':
                        doc_targets[doc_type].append(plugin_name)

                if not doc_targets[doc_type]:
                    del doc_targets[doc_type]

        error_messages: list[SanityMessage] = []

        for doc_type in sorted(doc_targets):
            for format_option in [None, '--json']:
                cmd = ['ansible-doc', '-t', doc_type]
                if format_option is not None:
                    cmd.append(format_option)
                cmd.extend(sorted(doc_targets[doc_type]))

                try:
                    stdout, stderr = intercept_python(args, python, cmd, env, capture=True)
                    status = 0
                except SubprocessError as ex:
                    stdout = ex.stdout
                    stderr = ex.stderr
                    status = ex.status

                if status:
                    summary = '%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr)
                    return SanityFailure(self.name, summary=summary)

                if stdout:
                    display.info(stdout.strip(), verbosity=3)

                if stderr:
                    # ignore removed module/plugin warnings
                    stderr = re.sub(r'\[WARNING]: [^ ]+ [^ ]+ has been removed\n', '', stderr).strip()

                if stderr:
                    summary = 'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
                    return SanityFailure(self.name, summary=summary)

        if args.explain:
            return SanitySuccess(self.name)

        error_messages = settings.process_errors(error_messages, paths)

        if error_messages:
            return SanityFailure(self.name, messages=error_messages)

        return SanitySuccess(self.name)
