"""Sanity test for ansible-doc."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import collections
import os
import re

from .. import types as t

from ..sanity import (
    SanitySingleVersion,
    SanityFailure,
    SanitySuccess,
    SanityMessage,
)

from ..target import (
    TestTarget,
)

from ..util import (
    SubprocessError,
    display,
    is_subdir,
)

from ..util_common import (
    intercept_command,
)

from ..ansible_util import (
    ansible_environment,
)

from ..config import (
    SanityConfig,
)

from ..data import (
    data_context,
)

from ..coverage_util import (
    coverage_context,
)


class AnsibleDocTest(SanitySingleVersion):
    """Sanity test for ansible-doc."""
    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        # This should use documentable plugins from constants instead
        plugin_type_blacklist = set([
            # not supported by ansible-doc
            'action',
            'doc_fragments',
            'filter',
            'module_utils',
            'netconf',
            'terminal',
            'test',
        ])

        plugin_paths = [plugin_path for plugin_type, plugin_path in data_context().content.plugin_paths.items() if plugin_type not in plugin_type_blacklist]

        return [target for target in targets
                if os.path.splitext(target.path)[1] == '.py'
                and os.path.basename(target.path) != '__init__.py'
                and any(is_subdir(target.path, path) for path in plugin_paths)
                ]

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        settings = self.load_processor(args)

        paths = [target.path for target in targets.include]

        doc_targets = collections.defaultdict(list)
        target_paths = collections.defaultdict(dict)

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
        error_messages = []

        for doc_type in sorted(doc_targets):
            cmd = ['ansible-doc', '-t', doc_type] + sorted(doc_targets[doc_type])

            try:
                with coverage_context(args):
                    stdout, stderr = intercept_command(args, cmd, target_name='ansible-doc', env=env, capture=True, python_version=python_version)

                status = 0
            except SubprocessError as ex:
                stdout = ex.stdout
                stderr = ex.stderr
                status = ex.status

            if stderr:
                errors = stderr.strip().splitlines()
                messages = [self.parse_error(e, target_paths) for e in errors]

                if messages and all(messages):
                    error_messages += messages
                    continue

            if status:
                summary = u'%s' % SubprocessError(cmd=cmd, status=status, stderr=stderr)
                return SanityFailure(self.name, summary=summary)

            if stdout:
                display.info(stdout.strip(), verbosity=3)

            if stderr:
                summary = u'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
                return SanityFailure(self.name, summary=summary)

        error_messages = settings.process_errors(error_messages, paths)

        if error_messages:
            return SanityFailure(self.name, messages=error_messages)

        return SanitySuccess(self.name)

    @staticmethod
    def parse_error(error, target_paths):
        """
        :type error: str
        :type target_paths: dict[str, dict[str, str]]
        :rtype: SanityMessage | None
        """
        # example error messages from lib/ansible/cli/doc.py:
        #   ERROR! module ping missing documentation (or could not parse documentation): expected string or buffer
        #   [ERROR]: module ping has a documentation error formatting or is missing documentation.
        match = re.search(r'^[^ ]*ERROR[^ ]* (?P<type>[^ ]+) (?P<name>[^ ]+) (?P<text>.*)$', error)

        if match:
            groups = match.groupdict()

            error_type = groups['type']
            error_name = groups['name']
            error_text = groups['text']

            if error_name in target_paths.get(error_type, {}):
                return SanityMessage(
                    message=error_text,
                    path=target_paths[error_type][error_name],
                )

        return None
