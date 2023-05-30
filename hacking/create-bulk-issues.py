#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Create GitHub issues for deprecated features."""

from __future__ import annotations

import abc
import argparse
import dataclasses
import os
import pathlib
import re
import subprocess
import sys
import typing as t

import yaml

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
    labels: list[str] | None = None

    def create(self) -> str:
        cmd = ['gh', 'issue', 'create', '--title', self.title, '--body', self.body, '--project', self.project]

        if self.labels:
            for label in self.labels:
                cmd.extend(('--label', label))

        process = subprocess.run(cmd, capture_output=True, check=True)
        url = process.stdout.decode().strip()
        return url


@dataclasses.dataclass(frozen=True)
class Feature:
    title: str
    summary: str
    component: str
    labels: list[str] | None = None

    @staticmethod
    def from_dict(data: dict[str, t.Any]) -> Feature:
        title = data.get('title')
        summary = data.get('summary')
        component = data.get('component')
        labels = data.get('labels')

        if not isinstance(title, str):
            raise RuntimeError(f'`title` is not `str`: {title}')

        if not isinstance(summary, str):
            raise RuntimeError(f'`summary` is not `str`: {summary}')

        if not isinstance(component, str):
            raise RuntimeError(f'`component` is not `str`: {component}')

        if not isinstance(labels, list) or not all(isinstance(item, str) for item in labels):
            raise RuntimeError(f'`labels` is not `list[str]`: {labels}')

        return Feature(
            title=title,
            summary=summary,
            component=component,
            labels=labels,
        )

    def create_issue(self, project: str) -> Issue:
        body = f'''
### Summary

{self.summary}

### Issue Type

Feature Idea

### Component Name

`{self.component}`
'''

        return Issue(
            title=self.title,
            summary=self.summary,
            body=body.strip(),
            project=project,
            labels=self.labels,
        )


@dataclasses.dataclass(frozen=True)
class BugReport:
    title: str
    summary: str
    component: str
    labels: list[str] | None = None

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
            labels=self.labels,
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
    create: bool
    verbose: bool

    def run(self) -> None:
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class DeprecationArgs(Args):
    tests: list[str]

    def run(self) -> None:
        deprecated_command(self)


@dataclasses.dataclass(frozen=True)
class FeatureArgs(Args):
    source: pathlib.Path

    def run(self) -> None:
        feature_command(self)


def parse_args() -> Args:
    parser = argparse.ArgumentParser()

    create_common_arguments(parser)

    subparser = parser.add_subparsers(required=True)

    create_deprecation_parser(subparser)
    create_feature_parser(subparser)

    args = invoke_parser(parser)

    return args


def create_deprecation_parser(subparser) -> None:
    parser: argparse.ArgumentParser = subparser.add_parser('deprecation')
    parser.set_defaults(type=DeprecationArgs)
    parser.set_defaults(command=deprecated_command)

    parser.add_argument(
        '--test',
        dest='tests',
        choices=tuple(TEST_OPTIONS),
        action='append',
        help='sanity test name',
    )

    create_common_arguments(parser)


def create_feature_parser(subparser) -> None:
    parser: argparse.ArgumentParser = subparser.add_parser('feature')
    parser.set_defaults(type=FeatureArgs)
    parser.set_defaults(command=feature_command)

    parser.add_argument(
        '--source',
        type=pathlib.Path,
        default=pathlib.Path('issues.yml'),
        help='YAML file containing issue details (default: %(default)s)',
    )

    create_common_arguments(parser)


def create_common_arguments(parser: argparse.ArgumentParser) -> None:
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


def invoke_parser(parser: argparse.ArgumentParser) -> Args:
    if argcomplete:
        argcomplete.autocomplete(parser)

    parsed_args = parser.parse_args()

    kvp = {}
    args_type = parsed_args.type

    for field in dataclasses.fields(args_type):
        kvp[field.name] = getattr(parsed_args, field.name)

    args = args_type(**kvp)

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


def create_issues_from_deprecation_messages(test_type: t.Type[Deprecation], messages: list[str]) -> list[Issue]:
    deprecations = [test_type.parse(message) for message in messages]
    bug_reports = [deprecation.create_bug_report() for deprecation in deprecations]
    issues = [bug_report.create_issue(PROJECT) for bug_report in bug_reports]
    return issues


def info(message: str) -> None:
    print(message, file=sys.stderr)


def main() -> None:
    args = parse_args()
    args.run()


def deprecated_command(args: DeprecationArgs) -> None:
    issues: list[Issue] = []

    for test in args.tests or list(TEST_OPTIONS):
        test_type = TEST_OPTIONS[test]
        info(f'Running "{test}" sanity test...')
        messages = run_sanity_test(test)
        issues.extend(create_issues_from_deprecation_messages(test_type, messages))

    create_issues(args, issues)


def feature_command(args: FeatureArgs) -> None:
    with args.source.open() as source_file:
        source = yaml.safe_load(source_file)

    default: dict[str, t.Any] = source.get('default', {})
    features: list[dict[str, t.Any]] = source.get('features', [])

    if not isinstance(default, dict):
        raise RuntimeError('`default` must be `dict[str, ...]`')

    if not isinstance(features, list):
        raise RuntimeError('`features` must be `list[dict[str, ...]]`')

    issues: list[Issue] = []

    for feature in features:
        data = default.copy()
        data.update(feature)

        feature = Feature.from_dict(data)
        issues.append(feature.create_issue(PROJECT))

    create_issues(args, issues)


def create_issues(args: Args, issues: list[Issue]) -> None:
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
