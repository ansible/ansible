"""Sanity test for ansible-doc."""
from __future__ import annotations

import collections
import os
import re
import typing as t

from . import (
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
    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        # This should use documentable plugins from constants instead
        unsupported_plugin_types = {
            # not supported by ansible-doc
            'action',
            'doc_fragments',
            'filter',
            'module_utils',
            'terminal',
            'test',
            # The following are plugin directories not directly supported by ansible-core (and thus also not by ansible-doc)
            # (https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#modules--plugins)
            'plugin_utils',
            'sub_plugins',
        }

        plugin_paths = [plugin_path for plugin_type, plugin_path in data_context().content.plugin_paths.items() if plugin_type not in unsupported_plugin_types]

        return [target for target in targets
                if os.path.splitext(target.path)[1] == '.py'
                and os.path.basename(target.path) != '__init__.py'
                and any(is_subdir(target.path, path) for path in plugin_paths)
                ]

    def test(self, args, targets, python):  # type: (SanityConfig, SanityTargets, PythonConfig) -> TestResult
        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        doc_targets = collections.defaultdict(list)  # type: t.Dict[str, t.List[str]]
        target_paths = collections.defaultdict(dict)  # type: t.Dict[str, t.Dict[str, str]]

        remap_types = dict(
            modules='module',
        )

        for plugin_type, plugin_path in data_context().content.plugin_paths.items():
            plugin_type = remap_types.get(plugin_type, plugin_type)

            for plugin_file_path in [target.name for target in targets.include if is_subdir(target.path, plugin_path)]:
                plugin_name = os.path.splitext(os.path.basename(plugin_file_path))[0]

                if plugin_name.startswith('_'):
                    plugin_name = plugin_name[1:]

                doc_targets[plugin_type].append(data_context().content.prefix + plugin_name)
                target_paths[plugin_type][data_context().content.prefix + plugin_name] = plugin_file_path

        env = ansible_environment(args, color=False)
        error_messages = []  # type: t.List[SanityMessage]

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
                    summary = u'%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr)
                    return SanityFailure(self.name, summary=summary)

                if stdout:
                    display.info(stdout.strip(), verbosity=3)

                if stderr:
                    # ignore removed module/plugin warnings
                    stderr = re.sub(r'\[WARNING]: [^ ]+ [^ ]+ has been removed\n', '', stderr).strip()

                if stderr:
                    summary = u'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
                    return SanityFailure(self.name, summary=summary)

        if args.explain:
            return SanitySuccess(self.name)

        error_messages = settings.process_errors(error_messages, paths)

        if error_messages:
            return SanityFailure(self.name, messages=error_messages)

        return SanitySuccess(self.name)
