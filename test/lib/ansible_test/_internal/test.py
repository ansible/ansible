"""Classes for storing and processing test results."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import re

from . import types as t

from .util import (
    display,
    get_ansible_version,
)

from .util_common import (
    write_text_test_results,
    write_json_test_results,
    ResultType,
)

from .config import (
    TestConfig,
)


def calculate_best_confidence(choices, metadata):
    """
    :type choices: tuple[tuple[str, int]]
    :type metadata: Metadata
    :rtype: int
    """
    best_confidence = 0

    for path, line in choices:
        confidence = calculate_confidence(path, line, metadata)
        best_confidence = max(confidence, best_confidence)

    return best_confidence


def calculate_confidence(path, line, metadata):
    """
    :type path: str
    :type line: int
    :type metadata: Metadata
    :rtype: int
    """
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
    def __init__(self, command, test, python_version=None):
        """
        :type command: str
        :type test: str
        :type python_version: str
        """
        self.command = command
        self.test = test
        self.python_version = python_version
        self.name = self.test or self.command

        if self.python_version:
            self.name += '-python-%s' % self.python_version

        try:
            import junit_xml
        except ImportError:
            junit_xml = None

        self.junit = junit_xml

    def write(self, args):
        """
        :type args: TestConfig
        """
        self.write_console()
        self.write_bot(args)

        if args.lint:
            self.write_lint()

        if args.junit:
            if self.junit:
                self.write_junit(args)
            else:
                display.warning('Skipping junit xml output because the `junit-xml` python package was not found.', unique=True)

    def write_console(self):
        """Write results to console."""

    def write_lint(self):
        """Write lint results to stdout."""

    def write_bot(self, args):
        """
        :type args: TestConfig
        """

    def write_junit(self, args):
        """
        :type args: TestConfig
        """

    def create_result_name(self, extension):
        """
        :type extension: str
        :rtype: str
        """
        name = 'ansible-test-%s' % self.command

        if self.test:
            name += '-%s' % self.test

        if self.python_version:
            name += '-python-%s' % self.python_version

        name += extension

        return name

    def save_junit(self, args, test_case, properties=None):
        """
        :type args: TestConfig
        :type test_case: junit_xml.TestCase
        :type properties: dict[str, str] | None
        :rtype: str | None
        """
        test_suites = [
            self.junit.TestSuite(
                name='ansible-test',
                test_cases=[test_case],
                timestamp=datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
                properties=properties,
            ),
        ]

        # the junit_xml API is changing in version 2.0.0
        # TestSuite.to_xml_string is being replaced with to_xml_report_string
        # see: https://github.com/kyrus/python-junit-xml/blob/63db26da353790500642fd02cae1543eb41aab8b/junit_xml/__init__.py#L249-L261
        try:
            to_xml_string = self.junit.to_xml_report_string
        except AttributeError:
            to_xml_string = self.junit.TestSuite.to_xml_string

        report = to_xml_string(test_suites=test_suites, prettyprint=True, encoding='utf-8')

        if args.explain:
            return

        write_text_test_results(ResultType.JUNIT, self.create_result_name('.xml'), report)


class TestTimeout(TestResult):
    """Test timeout."""
    def __init__(self, timeout_duration):
        """
        :type timeout_duration: int
        """
        super(TestTimeout, self).__init__(command='timeout', test='')

        self.timeout_duration = timeout_duration

    def write(self, args):
        """
        :type args: TestConfig
        """
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

        timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

        # hack to avoid requiring junit-xml, which may not be pre-installed outside our test containers
        xml = '''
<?xml version="1.0" encoding="utf-8"?>
<testsuites disabled="0" errors="1" failures="0" tests="1" time="0.0">
\t<testsuite disabled="0" errors="1" failures="0" file="None" log="None" name="ansible-test" skipped="0" tests="1" time="0" timestamp="%s" url="None">
\t\t<testcase classname="timeout" name="timeout">
\t\t\t<error message="%s" type="error">%s</error>
\t\t</testcase>
\t</testsuite>
</testsuites>
''' % (timestamp, message, output)

        write_text_test_results(ResultType.JUNIT, self.create_result_name('.xml'), xml.lstrip())


class TestSuccess(TestResult):
    """Test success."""
    def write_junit(self, args):
        """
        :type args: TestConfig
        """
        test_case = self.junit.TestCase(classname=self.command, name=self.name)

        self.save_junit(args, test_case)


class TestSkipped(TestResult):
    """Test skipped."""
    def write_console(self):
        """Write results to console."""
        display.info('No tests applicable.', verbosity=1)

    def write_junit(self, args):
        """
        :type args: TestConfig
        """
        test_case = self.junit.TestCase(classname=self.command, name=self.name)
        test_case.add_skipped_info('No tests applicable.')

        self.save_junit(args, test_case)


class TestFailure(TestResult):
    """Test failure."""
    def __init__(self, command, test, python_version=None, messages=None, summary=None):
        """
        :type command: str
        :type test: str
        :type python_version: str | None
        :type messages: list[TestMessage] | None
        :type summary: unicode | None
        """
        super(TestFailure, self).__init__(command, test, python_version)

        if messages:
            messages = sorted(messages)
        else:
            messages = []

        self.messages = messages
        self.summary = summary

    def write(self, args):
        """
        :type args: TestConfig
        """
        if args.metadata.changes:
            self.populate_confidence(args.metadata)

        super(TestFailure, self).write(args)

    def write_console(self):
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

    def write_lint(self):
        """Write lint results to stdout."""
        if self.summary:
            command = self.format_command()
            message = 'The test `%s` failed. See stderr output for details.' % command
            path = ''
            message = TestMessage(message, path)
            print(message)
        else:
            for message in self.messages:
                print(message)

    def write_junit(self, args):
        """
        :type args: TestConfig
        """
        title = self.format_title()
        output = self.format_block()

        test_case = self.junit.TestCase(classname=self.command, name=self.name)

        # Include a leading newline to improve readability on Shippable "Tests" tab.
        # Without this, the first line becomes indented.
        test_case.add_failure_info(message=title, output='\n%s' % output)

        self.save_junit(args, test_case)

    def write_bot(self, args):
        """
        :type args: TestConfig
        """
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

    def populate_confidence(self, metadata):
        """
        :type metadata: Metadata
        """
        for message in self.messages:
            if message.confidence is None:
                message.confidence = calculate_confidence(message.path, message.line, metadata)

    def format_command(self):
        """
        :rtype: str
        """
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

        testing_docs_url = 'https://docs.ansible.com/ansible/%s/dev_guide/testing' % url_version

        url = '%s/%s/' % (testing_docs_url, self.command)

        if self.test:
            url += '%s.html' % self.test

        return url

    def format_title(self, help_link=None):
        """
        :type help_link: str | None
        :rtype: str
        """
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

    def format_block(self):
        """
        :rtype: str
        """
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
    def __init__(self, message, path, line=0, column=0, level='error', code=None, confidence=None):
        """
        :type message: str
        :type path: str
        :type line: int
        :type column: int
        :type level: str
        :type code: str | None
        :type confidence: int | None
        """
        self.__path = path
        self.__line = line
        self.__column = column
        self.__level = level
        self.__code = code
        self.__message = message

        self.confidence = confidence

    @property
    def path(self):  # type: () -> str
        """Return the path."""
        return self.__path

    @property
    def line(self):  # type: () -> int
        """Return the line number, or 0 if none is available."""
        return self.__line

    @property
    def column(self):  # type: () -> int
        """Return the column number, or 0 if none is available."""
        return self.__column

    @property
    def level(self):  # type: () -> str
        """Return the level."""
        return self.__level

    @property
    def code(self):  # type: () -> t.Optional[str]
        """Return the code, if any."""
        return self.__code

    @property
    def message(self):  # type: () -> str
        """Return the message."""
        return self.__message

    @property
    def tuple(self):  # type: () -> t.Tuple[str, int, int, str, t.Optional[str], str]
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

    def format(self, show_confidence=False):
        """
        :type show_confidence: bool
        :rtype: str
        """
        if self.__code:
            msg = '%s: %s' % (self.__code, self.__message)
        else:
            msg = self.__message

        if show_confidence and self.confidence is not None:
            msg += ' (%d%%)' % self.confidence

        return '%s:%s:%s: %s' % (self.__path, self.__line, self.__column, msg)
