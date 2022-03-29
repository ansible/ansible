#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Create GitHub issues for deprecated features."""

from __future__ import annotations

import abc
import argparse
import dataclasses
import os
import re
import subprocess
import sys
import typing as t

try:
    # noinspection PyPackageRequirements
    import argcomplete
except ImportError:
    argcomplete = None

from ansible.release import __version__

MAJOR_MINOR_VERSION = '.'.join(__version__.split('.')[:2])
PROJECT = f'ansible-core {MAJOR_MINOR_VERSION}'


@dataclasses.dataclass(frozen=True)
class Issue:
    title: str
    summary: str
    body: str
    project: str

    def create(self) -> str:
        cmd = ['gh', 'issue', 'create', '--title', self.title, '--body', self.body, '--project', self.project]
        process = subprocess.run(cmd, capture_output=True, check=True)
        url = process.stdout.decode().strip()
        return url


@dataclasses.dataclass(frozen=True)
class BugReport:
    title: str
    summary: str
    component: str

    def create_issue(self, project: str) -> Issue:
        body = f'''
### Summary

{self.summary}

### Issue Type

Bug Report

### Component Name

`{self.component}`

### Ansible Version

{MAJOR_MINOR_VERSION}

### Configuration

N/A

### OS / Environment

N/A

### Steps to Reproduce

N/A

### Expected Results

N/A

### Actual Results

N/A
'''

        return Issue(
            title=self.title,
            summary=self.summary,
            body=body.strip(),
            project=project,
        )


@dataclasses.dataclass(frozen=True)
class Deprecation(metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def parse(message: str) -> Deprecation:
        pass

    @abc.abstractmethod
    def create_bug_report(self) -> BugReport:
        pass


@dataclasses.dataclass(frozen=True)
class DeprecatedConfig(Deprecation):
    path: str
    config: str
    version: str

    @staticmethod
    def parse(message: str) -> DeprecatedConfig:
        match = re.search('^(?P<path>.*):[0-9]+:[0-9]+: (?P<config>.*) is scheduled for removal in (?P<version>[0-9.]+)$', message)

        if not match:
            raise Exception(f'Unable to parse: {message}')

        return DeprecatedConfig(
            path=match.group('path'),
            config=match.group('config'),
            version=match.group('version'),
        )

    def create_bug_report(self) -> BugReport:
        return BugReport(
            title=f'Remove deprecated {self.config}',
            summary=f'The config option `{self.config}` should be removed from `{self.path}`. It was scheduled for removal in {self.version}.',
            component=self.path,
        )


@dataclasses.dataclass(frozen=True)
class UpdateBundled(Deprecation):
    path: str
    package: str
    old_version: str
    new_version: str
    json_link: str
    link: str = dataclasses.field(default='', init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'link', re.sub('/json$', '', self.json_link))

    @staticmethod
    def parse(message: str) -> UpdateBundled:
        match = re.search('^(?P<path>.*):[0-9]+:[0-9]+: UPDATE (?P<package>.*) from (?P<old>[0-9.]+) to (?P<new>[0-9.]+) (?P<link>https://.*)$', message)

        if not match:
            raise Exception(f'Unable to parse: {message}')

        return UpdateBundled(
            path=match.group('path'),
            package=match.group('package'),
            old_version=match.group('old'),
            new_version=match.group('new'),
            json_link=match.group('link'),
        )

    def create_bug_report(self) -> BugReport:
        return BugReport(
            title=f'Update bundled {self.package} to {self.new_version}',
            summary=f'Update the bundled package [{self.package}]({self.link}) from `{self.old_version}` to `{self.new_version}`.',
            component=self.path,
        )


TEST_OPTIONS = {
    'update-bundled': UpdateBundled,
    'deprecated-config': DeprecatedConfig,
}


@dataclasses.dataclass(frozen=True)
class Args:
    tests: list[str]
    create: bool
    verbose: bool


def parse_args() -> Args:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--test',
        dest='tests',
        choices=tuple(TEST_OPTIONS),
        action='append',
        help='sanity test name',
    )

    parser.add_argument(
        '--create',
        action='store_true',
        help='create issues on GitHub',
    )

    parser.add_argument(
        '-v',
        dest='verbose',
        action='store_true',
        help='verbose output',
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    parsed_args = parser.parse_args()

    if not parsed_args.tests:
        parsed_args.tests = list(TEST_OPTIONS)

    kvp = {}

    for field in dataclasses.fields(Args):
        kvp[field.name] = getattr(parsed_args, field.name)

    args = Args(**kvp)

    return args


def run_sanity_test(test_name: str) -> list[str]:
    cmd = ['ansible-test', 'sanity', '--test', test_name, '--lint', '--failure-ok']
    skip_path = 'test/sanity/code-smell/skip.txt'
    skip_temp_path = skip_path + '.tmp'

    os.rename(skip_path, skip_temp_path)  # make sure ansible-test isn't configured to skip any tests

    try:
        process = subprocess.run(cmd, capture_output=True, check=True)
    finally:
        os.rename(skip_temp_path, skip_path)  # restore the skip entries

    messages = process.stdout.decode().splitlines()

    return messages


def create_issues(test_type: t.Type[Deprecation], messages: list[str]) -> list[Issue]:
    deprecations = [test_type.parse(message) for message in messages]
    bug_reports = [deprecation.create_bug_report() for deprecation in deprecations]
    issues = [bug_report.create_issue(PROJECT) for bug_report in bug_reports]
    return issues


def info(message: str) -> None:
    print(message, file=sys.stderr)


def main() -> None:
    args = parse_args()
    issues: list[Issue] = []

    for test in args.tests:
        test_type = TEST_OPTIONS[test]
        info(f'Running "{test}" sanity test...')
        messages = run_sanity_test(test)
        issues.extend(create_issues(test_type, messages))

    if not issues:
        info('No issues found.')
        return

    info(f'Found {len(issues)} issue(s) to report:')

    for issue in issues:
        info(f'[{issue.title}] {issue.summary}')

        if args.verbose:
            info('>>>')
            info(issue.body)
            info('>>>')

        if args.create:
            url = issue.create()
            info(url)

    if not args.create:
        info('Pass the "--create" option to create these issues on GitHub.')


if __name__ == '__main__':
    main()
