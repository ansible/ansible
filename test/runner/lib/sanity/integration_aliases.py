"""Sanity test to check integration test aliases."""
from __future__ import absolute_import, print_function

import json
import textwrap
import re

from lib.sanity import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
)

from lib.config import (
    SanityConfig,
)

from lib.target import (
    filter_targets,
    walk_posix_integration_targets,
    walk_windows_integration_targets,
    walk_integration_targets,
    walk_module_targets,
)

from lib.cloud import (
    get_cloud_platforms,
)

from lib.util import (
    display,
)


class IntegrationAliasesTest(SanitySingleVersion):
    """Sanity test to evaluate integration test aliases."""
    DISABLED = 'disabled/'
    UNSTABLE = 'unstable/'
    UNSUPPORTED = 'unsupported/'

    EXPLAIN_URL = 'https://docs.ansible.com/ansible/devel/dev_guide/testing/sanity/integration-aliases.html'

    TEMPLATE_DISABLED = """
    The following integration tests are **disabled** [[explain]({explain_url}#disabled)]:

    {tests}

    Consider fixing the integration tests before or alongside changes.
    """

    TEMPLATE_UNSTABLE = """
    The following integration tests are **unstable** [[explain]({explain_url}#unstable)]:

    {tests}

    Tests may need to be restarted due to failures unrelated to changes.
    """

    TEMPLATE_UNSUPPORTED = """
    The following integration tests are **unsupported** [[explain]({explain_url}#unsupported)]:

    {tests}

    Consider running the tests manually or extending test infrastructure to add support.
    """

    TEMPLATE_UNTESTED = """
    The following modules have **no integration tests** [[explain]({explain_url}#untested)]:

    {tests}

    Consider adding integration tests before or alongside changes.
    """

    def __init__(self):
        super(IntegrationAliasesTest, self).__init__()

        self._shippable_yml_lines = []  # type: list[str]
        self._shippable_test_groups = {}  # type: dict[str, set[int]]

    @property
    def shippable_yml_lines(self):
        """
        :rtype: list[str]
        """
        if not self._shippable_yml_lines:
            with open('shippable.yml', 'r') as shippable_yml_fd:
                self._shippable_yml_lines = shippable_yml_fd.read().splitlines()

        return self._shippable_yml_lines

    @property
    def shippable_test_groups(self):
        """
        :rtype: dict[str, set[int]]
        """
        if not self._shippable_test_groups:
            matches = [re.search(r'^[ #]+- env: T=(?P<group>[^/]+)/(?P<params>.+)/(?P<number>[1-9])$', line) for line in self.shippable_yml_lines]
            entries = [(match.group('group'), int(match.group('number'))) for match in matches if match]

            for key, value in entries:
                if key not in self._shippable_test_groups:
                    self._shippable_test_groups[key] = set()

                self._shippable_test_groups[key].add(value)

        return self._shippable_test_groups

    def format_shippable_group_alias(self, name, fallback=''):
        """
        :type name: str
        :type fallback: str
        :rtype: str
        """
        group_numbers = self.shippable_test_groups.get(name, None)

        if group_numbers:
            if min(group_numbers) != 1:
                display.warning('Min test group "%s" in shippable.yml is %d instead of 1.' % (name, min(group_numbers)), unique=True)

            if max(group_numbers) != len(group_numbers):
                display.warning('Max test group "%s" in shippable.yml is %d instead of %d.' % (name, max(group_numbers), len(group_numbers)), unique=True)

            if len(group_numbers) > 1:
                alias = 'shippable/%s/group[%d-%d]/' % (name, min(group_numbers), max(group_numbers))
            else:
                alias = 'shippable/%s/group%d/' % (name, min(group_numbers))
        elif fallback:
            alias = 'shippable/%s/group%d/' % (fallback, 1)
        else:
            raise Exception('cannot find test group "%s" in shippable.yml' % name)

        return alias

    def test(self, args, targets):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :rtype: TestResult
        """
        if args.explain:
            return SanitySuccess(self.name)

        results = dict(
            comments=[],
            labels={},
        )

        self.check_changes(args, results)

        with open('test/results/bot/data-sanity-ci.json', 'w') as results_fd:
            json.dump(results, results_fd, sort_keys=True, indent=4)

        messages = []

        messages += self.check_posix_targets(args)
        messages += self.check_windows_targets()

        if messages:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)

    def check_posix_targets(self, args):
        """
        :type args: SanityConfig
        :rtype: list[SanityMessage]
        """
        posix_targets = tuple(walk_posix_integration_targets())

        clouds = get_cloud_platforms(args, posix_targets)
        cloud_targets = ['cloud/%s/' % cloud for cloud in clouds]

        all_cloud_targets = tuple(filter_targets(posix_targets, ['cloud/'], include=True, directories=False, errors=False))
        invalid_cloud_targets = tuple(filter_targets(all_cloud_targets, cloud_targets, include=False, directories=False, errors=False))

        messages = []

        for target in invalid_cloud_targets:
            for alias in target.aliases:
                if alias.startswith('cloud/') and alias != 'cloud/':
                    if any(alias.startswith(cloud_target) for cloud_target in cloud_targets):
                        continue

                    messages.append(SanityMessage('invalid alias `%s`' % alias, '%s/aliases' % target.path))

        messages += self.check_ci_group(
            targets=tuple(filter_targets(posix_targets, ['cloud/'], include=False, directories=False, errors=False)),
            find=self.format_shippable_group_alias('linux').replace('linux', 'posix'),
        )

        for cloud in clouds:
            messages += self.check_ci_group(
                targets=tuple(filter_targets(posix_targets, ['cloud/%s/' % cloud], include=True, directories=False, errors=False)),
                find=self.format_shippable_group_alias(cloud, 'cloud'),
            )

        return messages

    def check_windows_targets(self):
        """
        :rtype: list[SanityMessage]
        """
        windows_targets = tuple(walk_windows_integration_targets())

        messages = []

        messages += self.check_ci_group(
            targets=windows_targets,
            find=self.format_shippable_group_alias('windows'),
        )

        return messages

    def check_ci_group(self, targets, find):
        """
        :type targets: tuple[CompletionTarget]
        :type find: str
        :rtype: list[SanityMessage]
        """
        all_paths = set(t.path for t in targets)
        supported_paths = set(t.path for t in filter_targets(targets, [find], include=True, directories=False, errors=False))
        unsupported_paths = set(t.path for t in filter_targets(targets, [self.UNSUPPORTED], include=True, directories=False, errors=False))

        unassigned_paths = all_paths - supported_paths - unsupported_paths
        conflicting_paths = supported_paths & unsupported_paths

        unassigned_message = 'missing alias `%s` or `%s`' % (find.strip('/'), self.UNSUPPORTED.strip('/'))
        conflicting_message = 'conflicting alias `%s` and `%s`' % (find.strip('/'), self.UNSUPPORTED.strip('/'))

        messages = []

        for path in unassigned_paths:
            messages.append(SanityMessage(unassigned_message, '%s/aliases' % path))

        for path in conflicting_paths:
            messages.append(SanityMessage(conflicting_message, '%s/aliases' % path))

        return messages

    def check_changes(self, args, results):
        """
        :type args: SanityConfig
        :type results: dict[str, any]
        """
        integration_targets = list(walk_integration_targets())
        module_targets = list(walk_module_targets())

        integration_targets_by_name = dict((t.name, t) for t in integration_targets)
        module_names_by_path = dict((t.path, t.module) for t in module_targets)

        disabled_targets = []
        unstable_targets = []
        unsupported_targets = []

        for command in [command for command in args.metadata.change_description.focused_command_targets if 'integration' in command]:
            for target in args.metadata.change_description.focused_command_targets[command]:
                if self.DISABLED in integration_targets_by_name[target].aliases:
                    disabled_targets.append(target)
                elif self.UNSTABLE in integration_targets_by_name[target].aliases:
                    unstable_targets.append(target)
                elif self.UNSUPPORTED in integration_targets_by_name[target].aliases:
                    unsupported_targets.append(target)

        untested_modules = []

        for path in args.metadata.change_description.no_integration_paths:
            module = module_names_by_path.get(path)

            if module:
                untested_modules.append(module)

        comments = [
            self.format_comment(self.TEMPLATE_DISABLED, disabled_targets),
            self.format_comment(self.TEMPLATE_UNSTABLE, unstable_targets),
            self.format_comment(self.TEMPLATE_UNSUPPORTED, unsupported_targets),
            self.format_comment(self.TEMPLATE_UNTESTED, untested_modules),
        ]

        comments = [comment for comment in comments if comment]

        labels = dict(
            needs_tests=bool(untested_modules),
            disabled_tests=bool(disabled_targets),
            unstable_tests=bool(unstable_targets),
            unsupported_tests=bool(unsupported_targets),
        )

        results['comments'] += comments
        results['labels'].update(labels)

    def format_comment(self, template, targets):
        """
        :type template: str
        :type targets: list[str]
        :rtype: str | None
        """
        if not targets:
            return None

        tests = '\n'.join('- %s' % target for target in targets)

        data = dict(
            explain_url=self.EXPLAIN_URL,
            tests=tests,
        )

        message = textwrap.dedent(template).strip().format(**data)

        return message
