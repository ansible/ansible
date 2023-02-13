"""Sanity test to check integration test aliases."""
from __future__ import annotations

import dataclasses
import json
import textwrap
import os
import re
import typing as t

from . import (
    SanitySingleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    SANITY_ROOT,
)

from ...test import (
    TestResult,
)

from ...config import (
    SanityConfig,
)

from ...target import (
    filter_targets,
    walk_posix_integration_targets,
    walk_windows_integration_targets,
    walk_integration_targets,
    walk_module_targets,
    CompletionTarget,
    IntegrationTargetType,
)

from ..integration.cloud import (
    get_cloud_platforms,
)

from ...io import (
    read_text_file,
)

from ...util import (
    display,
    raw_command,
)

from ...util_common import (
    get_docs_url,
    write_json_test_results,
    ResultType,
)

from ...host_configs import (
    PythonConfig,
)


class IntegrationAliasesTest(SanitySingleVersion):
    """Sanity test to evaluate integration test aliases."""

    CI_YML = '.azure-pipelines/azure-pipelines.yml'
    TEST_ALIAS_PREFIX = 'shippable'  # this will be changed at some point in the future

    DISABLED = 'disabled/'
    UNSTABLE = 'unstable/'
    UNSUPPORTED = 'unsupported/'

    EXPLAIN_URL = get_docs_url('https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/integration-aliases.html')

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

    ansible_only = True

    def __init__(self) -> None:
        super().__init__()

        self._ci_config: dict[str, t.Any] = {}
        self._ci_test_groups: dict[str, list[int]] = {}

    @property
    def can_ignore(self) -> bool:
        """True if the test supports ignore entries."""
        return False

    @property
    def no_targets(self) -> bool:
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return True

    def load_ci_config(self, python: PythonConfig) -> dict[str, t.Any]:
        """Load and return the CI YAML configuration."""
        if not self._ci_config:
            self._ci_config = self.load_yaml(python, self.CI_YML)

        return self._ci_config

    @property
    def ci_test_groups(self) -> dict[str, list[int]]:
        """Return a dictionary of CI test names and their group(s)."""
        if not self._ci_test_groups:
            test_groups: dict[str, set[int]] = {}

            for stage in self._ci_config['stages']:
                for job in stage['jobs']:
                    if job.get('template') != 'templates/matrix.yml':
                        continue

                    parameters = job['parameters']

                    groups = parameters.get('groups', [])
                    test_format = parameters.get('testFormat', '{0}')
                    test_group_format = parameters.get('groupFormat', '{0}/{{1}}')

                    for target in parameters['targets']:
                        test = target.get('test') or target.get('name')

                        if groups:
                            tests_formatted = [test_group_format.format(test_format).format(test, group) for group in groups]
                        else:
                            tests_formatted = [test_format.format(test)]

                        for test_formatted in tests_formatted:
                            parts = test_formatted.split('/')
                            key = parts[0]

                            if key in ('sanity', 'units'):
                                continue

                            try:
                                group = int(parts[-1])
                            except ValueError:
                                continue

                            if group < 1 or group > 99:
                                continue

                            group_set = test_groups.setdefault(key, set())
                            group_set.add(group)

            self._ci_test_groups = dict((key, sorted(value)) for key, value in test_groups.items())

        return self._ci_test_groups

    def format_test_group_alias(self, name: str, fallback: str = '') -> str:
        """Return a test group alias using the given name and fallback."""
        group_numbers = self.ci_test_groups.get(name, None)

        if group_numbers:
            if min(group_numbers) != 1:
                display.warning('Min test group "%s" in %s is %d instead of 1.' % (name, self.CI_YML, min(group_numbers)), unique=True)

            if max(group_numbers) != len(group_numbers):
                display.warning('Max test group "%s" in %s is %d instead of %d.' % (name, self.CI_YML, max(group_numbers), len(group_numbers)), unique=True)

            if max(group_numbers) > 9:
                alias = '%s/%s/group(%s)/' % (self.TEST_ALIAS_PREFIX, name, '|'.join(str(i) for i in range(min(group_numbers), max(group_numbers) + 1)))
            elif len(group_numbers) > 1:
                alias = '%s/%s/group[%d-%d]/' % (self.TEST_ALIAS_PREFIX, name, min(group_numbers), max(group_numbers))
            else:
                alias = '%s/%s/group%d/' % (self.TEST_ALIAS_PREFIX, name, min(group_numbers))
        elif fallback:
            alias = '%s/%s/group%d/' % (self.TEST_ALIAS_PREFIX, fallback, 1)
        else:
            raise Exception('cannot find test group "%s" in %s' % (name, self.CI_YML))

        return alias

    def load_yaml(self, python: PythonConfig, path: str) -> dict[str, t.Any]:
        """Load the specified YAML file and return the contents."""
        yaml_to_json_path = os.path.join(SANITY_ROOT, self.name, 'yaml_to_json.py')
        return json.loads(raw_command([python.path, yaml_to_json_path], data=read_text_file(path), capture=True)[0])

    def test(self, args: SanityConfig, targets: SanityTargets, python: PythonConfig) -> TestResult:
        if args.explain:
            return SanitySuccess(self.name)

        if not os.path.isfile(self.CI_YML):
            return SanityFailure(self.name, messages=[SanityMessage(
                message='file missing',
                path=self.CI_YML,
            )])

        results = Results(
            comments=[],
            labels={},
        )

        self.load_ci_config(python)
        self.check_changes(args, results)

        write_json_test_results(ResultType.BOT, 'data-sanity-ci.json', results.__dict__)

        messages = []

        messages += self.check_posix_targets(args)
        messages += self.check_windows_targets()

        if messages:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)

    def check_posix_targets(self, args: SanityConfig) -> list[SanityMessage]:
        """Check POSIX integration test targets and return messages with any issues found."""
        posix_targets = tuple(walk_posix_integration_targets())

        clouds = get_cloud_platforms(args, posix_targets)
        cloud_targets = ['cloud/%s/' % cloud for cloud in clouds]

        all_cloud_targets = tuple(filter_targets(posix_targets, ['cloud/'], errors=False))
        invalid_cloud_targets = tuple(filter_targets(all_cloud_targets, cloud_targets, include=False, errors=False))

        messages = []

        for target in invalid_cloud_targets:
            for alias in target.aliases:
                if alias.startswith('cloud/') and alias != 'cloud/':
                    if any(alias.startswith(cloud_target) for cloud_target in cloud_targets):
                        continue

                    messages.append(SanityMessage('invalid alias `%s`' % alias, '%s/aliases' % target.path))

        messages += self.check_ci_group(
            targets=tuple(filter_targets(posix_targets, ['cloud/', '%s/generic/' % self.TEST_ALIAS_PREFIX], include=False, errors=False)),
            find=self.format_test_group_alias('linux').replace('linux', 'posix'),
            find_incidental=['%s/posix/incidental/' % self.TEST_ALIAS_PREFIX],
        )

        messages += self.check_ci_group(
            targets=tuple(filter_targets(posix_targets, ['%s/generic/' % self.TEST_ALIAS_PREFIX], errors=False)),
            find=self.format_test_group_alias('generic'),
        )

        for cloud in clouds:
            if cloud == 'httptester':
                find = self.format_test_group_alias('linux').replace('linux', 'posix')
                find_incidental = ['%s/posix/incidental/' % self.TEST_ALIAS_PREFIX]
            else:
                find = self.format_test_group_alias(cloud, 'generic')
                find_incidental = ['%s/%s/incidental/' % (self.TEST_ALIAS_PREFIX, cloud), '%s/cloud/incidental/' % self.TEST_ALIAS_PREFIX]

            messages += self.check_ci_group(
                targets=tuple(filter_targets(posix_targets, ['cloud/%s/' % cloud], errors=False)),
                find=find,
                find_incidental=find_incidental,
            )

        target_type_groups = {
            IntegrationTargetType.TARGET: (1, 2),
            IntegrationTargetType.CONTROLLER: (3, 4, 5),
            IntegrationTargetType.CONFLICT: (),
            IntegrationTargetType.UNKNOWN: (),
        }

        for target in posix_targets:
            if target.name == 'ansible-test-container':
                continue  # special test target which uses group 6 -- nothing else should be in that group

            if f'{self.TEST_ALIAS_PREFIX}/posix/' not in target.aliases:
                continue

            found_groups = [alias for alias in target.aliases if re.search(f'^{self.TEST_ALIAS_PREFIX}/posix/group[0-9]+/$', alias)]
            expected_groups = [f'{self.TEST_ALIAS_PREFIX}/posix/group{group}/' for group in target_type_groups[target.target_type]]
            valid_groups = [group for group in found_groups if group in expected_groups]
            invalid_groups = [group for group in found_groups if not any(group.startswith(expected_group) for expected_group in expected_groups)]

            if not valid_groups:
                messages.append(SanityMessage(f'Target of type {target.target_type.name} must be in at least one of these groups: {", ".join(expected_groups)}',
                                              f'{target.path}/aliases'))

            if invalid_groups:
                messages.append(SanityMessage(f'Target of type {target.target_type.name} cannot be in these groups: {", ".join(invalid_groups)}',
                                              f'{target.path}/aliases'))

        return messages

    def check_windows_targets(self) -> list[SanityMessage]:
        """Check Windows integration test targets and return messages with any issues found."""
        windows_targets = tuple(walk_windows_integration_targets())

        messages = []

        messages += self.check_ci_group(
            targets=windows_targets,
            find=self.format_test_group_alias('windows'),
            find_incidental=['%s/windows/incidental/' % self.TEST_ALIAS_PREFIX],
        )

        return messages

    def check_ci_group(
        self,
        targets: tuple[CompletionTarget, ...],
        find: str,
        find_incidental: t.Optional[list[str]] = None,
    ) -> list[SanityMessage]:
        """Check the CI groups set in the provided targets and return a list of messages with any issues found."""
        all_paths = set(target.path for target in targets)
        supported_paths = set(target.path for target in filter_targets(targets, [find], errors=False))
        unsupported_paths = set(target.path for target in filter_targets(targets, [self.UNSUPPORTED], errors=False))

        if find_incidental:
            incidental_paths = set(target.path for target in filter_targets(targets, find_incidental, errors=False))
        else:
            incidental_paths = set()

        unassigned_paths = all_paths - supported_paths - unsupported_paths - incidental_paths
        conflicting_paths = supported_paths & unsupported_paths

        unassigned_message = 'missing alias `%s` or `%s`' % (find.strip('/'), self.UNSUPPORTED.strip('/'))
        conflicting_message = 'conflicting alias `%s` and `%s`' % (find.strip('/'), self.UNSUPPORTED.strip('/'))

        messages = []

        for path in unassigned_paths:
            if path == 'test/integration/targets/ansible-test-container':
                continue  # special test target which uses group 6 -- nothing else should be in that group

            messages.append(SanityMessage(unassigned_message, '%s/aliases' % path))

        for path in conflicting_paths:
            messages.append(SanityMessage(conflicting_message, '%s/aliases' % path))

        return messages

    def check_changes(self, args: SanityConfig, results: Results) -> None:
        """Check changes and store results in the provided result dictionary."""
        integration_targets = list(walk_integration_targets())
        module_targets = list(walk_module_targets())

        integration_targets_by_name = dict((target.name, target) for target in integration_targets)
        module_names_by_path = dict((target.path, target.module) for target in module_targets)

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

        results.comments += comments
        results.labels.update(labels)

    def format_comment(self, template: str, targets: list[str]) -> t.Optional[str]:
        """Format and return a comment based on the given template and targets, or None if there are no targets."""
        if not targets:
            return None

        tests = '\n'.join('- %s' % target for target in targets)

        data = dict(
            explain_url=self.EXPLAIN_URL,
            tests=tests,
        )

        message = textwrap.dedent(template).strip().format(**data)

        return message


@dataclasses.dataclass
class Results:
    """Check results."""

    comments: list[str]
    labels: dict[str, bool]
