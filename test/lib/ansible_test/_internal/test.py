"""Classes for storing and processing test results."""
from __future__ import annotations

import collections.abc as c
import datetime
import re
import typing as t

from .util import (
    display,
    get_ansible_version,
)

from .util_common import (
    write_text_test_results,
    write_json_test_results,
    ResultType,
)

from .metadata import (
    Metadata,
)

from .config import (
    TestConfig,
)

from . import junit_xml


def calculate_best_confidence(choices: tuple[tuple[str, int], ...], metadata: Metadata) -> int:
    """Return the best confidence value available from the given choices and metadata."""
    best_confidence = 0

    for path, line in choices:
        confidence = calculate_confidence(path, line, metadata)
        best_confidence = max(confidence, best_confidence)

    return best_confidence


def calculate_confidence(path: str, line: int, metadata: Metadata) -> int:
    """Return the confidence level for a test result associated with the given file path and line number."""
    ranges = metadata.changes.get(path)

    # no changes were made to the file
    if not ranges:
        return 0

    # changes were made to the same file and line
    if any(r[0] <= line <= r[1] in r for r in ranges):
        return 100

    # changes were made to the same file and the line number is unknown
    if line == 0:
        return 75

    # changes were made to the same file and the line number is different
    return 50


class TestResult:
    """Base class for test results."""
    def __init__(self, command: str, test: str, python_version: t.Optional[str] = None) -> None:
        self.command = command
        self.test = test
        self.python_version = python_version
        self.name = self.test or self.command

        if self.python_version:
            self.name += '-python-%s' % self.python_version

    def write(self, args: TestConfig) -> None:
        """Write the test results to various locations."""
        self.write_console()
        self.write_bot(args)

        if args.lint:
            self.write_lint()

        if args.junit:
            self.write_junit(args)

    def write_console(self) -> None:
        """Write results to console."""

    def write_lint(self) -> None:
        """Write lint results to stdout."""

    def write_bot(self, args: TestConfig) -> None:
        """Write results to a file for ansibullbot to consume."""

    def write_junit(self, args: TestConfig) -> None:
        """Write results to a junit XML file."""

    def create_result_name(self, extension: str) -> str:
        """Return the name of the result file using the given extension."""
        name = 'ansible-test-%s' % self.command

        if self.test:
            name += '-%s' % self.test

        if self.python_version:
            name += '-python-%s' % self.python_version

        name += extension

        return name

    def save_junit(self, args: TestConfig, test_case: junit_xml.TestCase) -> None:
        """Save the given test case results to disk as JUnit XML."""
        suites = junit_xml.TestSuites(
            suites=[
                junit_xml.TestSuite(
                    name='ansible-test',
                    cases=[test_case],
                    timestamp=datetime.datetime.utcnow(),
                ),
            ],
        )

        report = suites.to_pretty_xml()

        if args.explain:
            return

        write_text_test_results(ResultType.JUNIT, self.create_result_name('.xml'), report)


class TestTimeout(TestResult):
    """Test timeout."""
    def __init__(self, timeout_duration: int) -> None:
        super().__init__(command='timeout', test='')

        self.timeout_duration = timeout_duration

    def write(self, args: TestConfig) -> None:
        """Write the test results to various locations."""
        message = 'Tests were aborted after exceeding the %d minute time limit.' % self.timeout_duration

        # Include a leading newline to improve readability on Shippable "Tests" tab.
        # Without this, the first line becomes indented.
        output = '''
One or more of the following situations may be responsible:

- Code changes have resulted in tests that hang or run for an excessive amount of time.
- Tests have been added which exceed the time limit when combined with existing tests.
- Test infrastructure and/or external dependencies are operating slower than normal.'''

        if args.coverage:
            output += '\n- Additional overhead from collecting code coverage has resulted in tests exceeding the time limit.'

        output += '\n\nConsult the console log for additional details on where the timeout occurred.'

        timestamp = datetime.datetime.utcnow()

        suites = junit_xml.TestSuites(
            suites=[
                junit_xml.TestSuite(
                    name='ansible-test',
                    timestamp=timestamp,
                    cases=[
                        junit_xml.TestCase(
                            name='timeout',
                            classname='timeout',
                            errors=[
                                junit_xml.TestError(
                                    message=message,
                                ),
                            ],
                        ),
                    ],
                )
            ],
        )

        report = suites.to_pretty_xml()

        write_text_test_results(ResultType.JUNIT, self.create_result_name('.xml'), report)


class TestSuccess(TestResult):
    """Test success."""
    def write_junit(self, args: TestConfig) -> None:
        """Write results to a junit XML file."""
        test_case = junit_xml.TestCase(classname=self.command, name=self.name)

        self.save_junit(args, test_case)


class TestSkipped(TestResult):
    """Test skipped."""
    def __init__(self, command: str, test: str, python_version: t.Optional[str] = None) -> None:
        super().__init__(command, test, python_version)

        self.reason: t.Optional[str] = None

    def write_console(self) -> None:
        """Write results to console."""
        if self.reason:
            display.warning(self.reason)
        else:
            display.info('No tests applicable.', verbosity=1)

    def write_junit(self, args: TestConfig) -> None:
        """Write results to a junit XML file."""
        test_case = junit_xml.TestCase(
            classname=self.command,
            name=self.name,
            skipped=self.reason or 'No tests applicable.',
        )

        self.save_junit(args, test_case)


class TestFailure(TestResult):
    """Test failure."""
    def __init__(
            self,
            command: str,
            test: str,
            python_version: t.Optional[str] = None,
            messages: t.Optional[c.Sequence[TestMessage]] = None,
            summary: t.Optional[str] = None,
    ):
        super().__init__(command, test, python_version)

        if messages:
            messages = sorted(messages)
        else:
            messages = []

        self.messages = messages
        self.summary = summary

    def write(self, args: TestConfig) -> None:
        """Write the test results to various locations."""
        if args.metadata.changes:
            self.populate_confidence(args.metadata)

        super().write(args)

    def write_console(self) -> None:
        """Write results to console."""
        if self.summary:
            display.error(self.summary)
        else:
            if self.python_version:
                specifier = ' on python %s' % self.python_version
            else:
                specifier = ''

            display.error('Found %d %s issue(s)%s which need to be resolved:' % (len(self.messages), self.test or self.command, specifier))

            for message in self.messages:
                display.error(message.format(show_confidence=True))

            doc_url = self.find_docs()
            if doc_url:
                display.info('See documentation for help: %s' % doc_url)

    def write_lint(self) -> None:
        """Write lint results to stdout."""
        if self.summary:
            command = self.format_command()
            message = 'The test `%s` failed. See stderr output for details.' % command
            path = ''
            message = TestMessage(message, path)
            print(message)  # display goes to stderr, this should be on stdout
        else:
            for message in self.messages:
                print(message)  # display goes to stderr, this should be on stdout

    def write_junit(self, args: TestConfig) -> None:
        """Write results to a junit XML file."""
        title = self.format_title()
        output = self.format_block()

        test_case = junit_xml.TestCase(
            classname=self.command,
            name=self.name,
            failures=[
                junit_xml.TestFailure(
                    message=title,
                    output=output,
                ),
            ],
        )

        self.save_junit(args, test_case)

    def write_bot(self, args: TestConfig) -> None:
        """Write results to a file for ansibullbot to consume."""
        docs = self.find_docs()
        message = self.format_title(help_link=docs)
        output = self.format_block()

        if self.messages:
            verified = all((m.confidence or 0) >= 50 for m in self.messages)
        else:
            verified = False

        bot_data = dict(
            verified=verified,
            docs=docs,
            results=[
                dict(
                    message=message,
                    output=output,
                ),
            ],
        )

        if args.explain:
            return

        write_json_test_results(ResultType.BOT, self.create_result_name('.json'), bot_data)

    def populate_confidence(self, metadata: Metadata) -> None:
        """Populate test result confidence using the provided metadata."""
        for message in self.messages:
            if message.confidence is None:
                message.confidence = calculate_confidence(message.path, message.line, metadata)

    def format_command(self) -> str:
        """Return a string representing the CLI command associated with the test failure."""
        command = 'ansible-test %s' % self.command

        if self.test:
            command += ' --test %s' % self.test

        if self.python_version:
            command += ' --python %s' % self.python_version

        return command

    def find_docs(self):
        """
        :rtype: str
        """
        if self.command != 'sanity':
            return None  # only sanity tests have docs links

        # Use the major.minor version for the URL only if this a release that
        # matches the pattern 2.4.0, otherwise, use 'devel'
        ansible_version = get_ansible_version()
        url_version = 'devel'
        if re.search(r'^[0-9.]+$', ansible_version):
            url_version = '.'.join(ansible_version.split('.')[:2])

        testing_docs_url = 'https://docs.ansible.com/ansible-core/%s/dev_guide/testing' % url_version

        url = '%s/%s/' % (testing_docs_url, self.command)

        if self.test:
            url += '%s.html' % self.test

        return url

    def format_title(self, help_link: t.Optional[str] = None) -> str:
        """Return a string containing a title/heading for this test failure, including an optional help link to explain the test."""
        command = self.format_command()

        if self.summary:
            reason = 'the error'
        else:
            reason = '1 error' if len(self.messages) == 1 else '%d errors' % len(self.messages)

        if help_link:
            help_link_markup = ' [[explain](%s)]' % help_link
        else:
            help_link_markup = ''

        title = 'The test `%s`%s failed with %s:' % (command, help_link_markup, reason)

        return title

    def format_block(self) -> str:
        """Format the test summary or messages as a block of text and return the result."""
        if self.summary:
            block = self.summary
        else:
            block = '\n'.join(m.format() for m in self.messages)

        message = block.strip()

        # Hack to remove ANSI color reset code from SubprocessError messages.
        message = message.replace(display.clear, '')

        return message


class TestMessage:
    """Single test message for one file."""
    def __init__(
            self,
            message: str,
            path: str,
            line: int = 0,
            column: int = 0,
            level: str = 'error',
            code: t.Optional[str] = None,
            confidence: t.Optional[int] = None,
    ):
        self.__path = path
        self.__line = line
        self.__column = column
        self.__level = level
        self.__code = code
        self.__message = message

        self.confidence = confidence

    @property
    def path(self) -> str:
        """Return the path."""
        return self.__path

    @property
    def line(self) -> int:
        """Return the line number, or 0 if none is available."""
        return self.__line

    @property
    def column(self) -> int:
        """Return the column number, or 0 if none is available."""
        return self.__column

    @property
    def level(self) -> str:
        """Return the level."""
        return self.__level

    @property
    def code(self) -> t.Optional[str]:
        """Return the code, if any."""
        return self.__code

    @property
    def message(self) -> str:
        """Return the message."""
        return self.__message

    @property
    def tuple(self) -> tuple[str, int, int, str, t.Optional[str], str]:
        """Return a tuple with all the immutable values of this test message."""
        return self.__path, self.__line, self.__column, self.__level, self.__code, self.__message

    def __lt__(self, other):
        return self.tuple < other.tuple

    def __le__(self, other):
        return self.tuple <= other.tuple

    def __eq__(self, other):
        return self.tuple == other.tuple

    def __ne__(self, other):
        return self.tuple != other.tuple

    def __gt__(self, other):
        return self.tuple > other.tuple

    def __ge__(self, other):
        return self.tuple >= other.tuple

    def __hash__(self):
        return hash(self.tuple)

    def __str__(self):
        return self.format()

    def format(self, show_confidence: bool = False) -> str:
        """Return a string representation of this message, optionally including the confidence level."""
        if self.__code:
            msg = '%s: %s' % (self.__code, self.__message)
        else:
            msg = self.__message

        if show_confidence and self.confidence is not None:
            msg += ' (%d%%)' % self.confidence

        return '%s:%s:%s: %s' % (self.__path, self.__line, self.__column, msg)
