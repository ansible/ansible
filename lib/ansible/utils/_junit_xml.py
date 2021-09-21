"""
Dataclasses for creating JUnit XML files.
See: https://github.com/junit-team/junit5/blob/main/platform-tests/src/test/resources/jenkins-junit.xsd
"""
from __future__ import annotations

import abc
import dataclasses
import datetime
import decimal
import typing as t

from xml.dom import minidom
# noinspection PyPep8Naming
from xml.etree import ElementTree as ET


@dataclasses.dataclass
class TestResult(metaclass=abc.ABCMeta):
    """Base class for the result of a test case."""
    output: t.Optional[str] = None
    message: t.Optional[str] = None
    type: t.Optional[str] = None

    def __post_init__(self):
        if self.type is None:
            self.type = self.tag

    @property
    @abc.abstractmethod
    def tag(self) -> str:
        """Tag name for the XML element created by this result type."""

    def get_attributes(self) -> t.Dict[str, str]:
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            message=self.message,
            type=self.type,
        )

    def get_xml_element(self) -> ET.Element:
        """Return an XML element representing this instance."""
        element = ET.Element(self.tag, self.get_attributes())
        element.text = self.output

        return element


@dataclasses.dataclass
class TestFailure(TestResult):
    """Failure info for a test case."""
    @property
    def tag(self) -> str:
        """Tag name for the XML element created by this result type."""
        return 'failure'


@dataclasses.dataclass
class TestError(TestResult):
    """Error info for a test case."""
    @property
    def tag(self) -> str:
        """Tag name for the XML element created by this result type."""
        return 'error'


@dataclasses.dataclass
class TestCase:
    """An individual test case."""
    name: str
    assertions: t.Optional[int] = None
    classname: t.Optional[str] = None
    status: t.Optional[str] = None
    time: t.Optional[decimal.Decimal] = None

    errors: t.List[TestError] = dataclasses.field(default_factory=list)
    failures: t.List[TestFailure] = dataclasses.field(default_factory=list)
    skipped: t.Optional[str] = None
    system_out: t.Optional[str] = None
    system_err: t.Optional[str] = None

    is_disabled: bool = False

    @property
    def is_failure(self) -> bool:
        """True if the test case contains failure info."""
        return bool(self.failures)

    @property
    def is_error(self) -> bool:
        """True if the test case contains error info."""
        return bool(self.errors)

    @property
    def is_skipped(self) -> bool:
        """True if the test case was skipped."""
        return bool(self.skipped)

    def get_attributes(self) -> t.Dict[str, str]:
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            assertions=self.assertions,
            classname=self.classname,
            name=self.name,
            status=self.status,
            time=self.time,
        )

    def get_xml_element(self) -> ET.Element:
        """Return an XML element representing this instance."""
        element = ET.Element('testcase', self.get_attributes())

        if self.skipped:
            ET.SubElement(element, 'skipped').text = self.skipped

        element.extend([error.get_xml_element() for error in self.errors])
        element.extend([failure.get_xml_element() for failure in self.failures])

        if self.system_out:
            ET.SubElement(element, 'system-out').text = self.system_out

        if self.system_err:
            ET.SubElement(element, 'system-err').text = self.system_err

        return element


@dataclasses.dataclass
class TestSuite:
    """A collection of test cases."""
    name: str
    hostname: t.Optional[str] = None
    id: t.Optional[str] = None
    package: t.Optional[str] = None
    timestamp: t.Optional[datetime.datetime] = None

    properties: t.Dict[str, str] = dataclasses.field(default_factory=dict)
    cases: t.List[TestCase] = dataclasses.field(default_factory=list)
    system_out: t.Optional[str] = None
    system_err: t.Optional[str] = None

    @property
    def disabled(self) -> int:
        """The number of disabled test cases."""
        return sum(case.is_disabled for case in self.cases)

    @property
    def errors(self) -> int:
        """The number of test cases containing error info."""
        return sum(case.is_error for case in self.cases)

    @property
    def failures(self) -> int:
        """The number of test cases containing failure info."""
        return sum(case.is_failure for case in self.cases)

    @property
    def skipped(self) -> int:
        """The number of test cases containing skipped info."""
        return sum(case.is_skipped for case in self.cases)

    @property
    def tests(self) -> int:
        """The number of test cases."""
        return len(self.cases)

    @property
    def time(self) -> decimal.Decimal:
        """The total time from all test cases."""
        return sum(case.time for case in self.cases if case.time)

    def get_attributes(self) -> t.Dict[str, str]:
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            disabled=self.disabled,
            errors=self.errors,
            failures=self.failures,
            hostname=self.hostname,
            id=self.id,
            name=self.name,
            package=self.package,
            skipped=self.skipped,
            tests=self.tests,
            time=self.time,
            timestamp=self.timestamp.isoformat(timespec='seconds') if self.timestamp else None,
        )

    def get_xml_element(self) -> ET.Element:
        """Return an XML element representing this instance."""
        element = ET.Element('testsuite', self.get_attributes())

        if self.properties:
            ET.SubElement(element, 'properties').extend([ET.Element('property', dict(name=name, value=value)) for name, value in self.properties.items()])

        element.extend([test_case.get_xml_element() for test_case in self.cases])

        if self.system_out:
            ET.SubElement(element, 'system-out').text = self.system_out

        if self.system_err:
            ET.SubElement(element, 'system-err').text = self.system_err

        return element


@dataclasses.dataclass
class TestSuites:
    """A collection of test suites."""
    name: t.Optional[str] = None

    suites: t.List[TestSuite] = dataclasses.field(default_factory=list)

    @property
    def disabled(self) -> int:
        """The number of disabled test cases."""
        return sum(suite.disabled for suite in self.suites)

    @property
    def errors(self) -> int:
        """The number of test cases containing error info."""
        return sum(suite.errors for suite in self.suites)

    @property
    def failures(self) -> int:
        """The number of test cases containing failure info."""
        return sum(suite.failures for suite in self.suites)

    @property
    def tests(self) -> int:
        """The number of test cases."""
        return sum(suite.tests for suite in self.suites)

    @property
    def time(self) -> decimal.Decimal:
        """The total time from all test cases."""
        return sum(suite.time for suite in self.suites)

    def get_attributes(self) -> t.Dict[str, str]:
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            disabled=self.disabled,
            errors=self.errors,
            failures=self.failures,
            name=self.name,
            tests=self.tests,
            time=self.time,
        )

    def get_xml_element(self) -> ET.Element:
        """Return an XML element representing this instance."""
        element = ET.Element('testsuites', self.get_attributes())
        element.extend([suite.get_xml_element() for suite in self.suites])

        return element

    def to_pretty_xml(self) -> str:
        """Return a pretty formatted XML string representing this instance."""
        return _pretty_xml(self.get_xml_element())


def _attributes(**kwargs) -> t.Dict[str, str]:
    """Return the given kwargs as a dictionary with values converted to strings. Items with a value of None will be omitted."""
    return {key: str(value) for key, value in kwargs.items() if value is not None}


def _pretty_xml(element: ET.Element) -> str:
    """Return a pretty formatted XML string representing the given element."""
    return minidom.parseString(ET.tostring(element, encoding='unicode')).toprettyxml()
