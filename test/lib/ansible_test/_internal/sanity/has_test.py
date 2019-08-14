"""Sanity test to check that an integration test exists"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import textwrap
import re
import os

from .. import types as t

from ..sanity import (
    SanityVersionNeutral,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
)

from ..config import (
    SanityConfig,
)

from ..target import (
    filter_targets,
    walk_posix_integration_targets,
    walk_windows_integration_targets,
    walk_integration_targets,
    walk_module_targets,
)

from ..cloud import (
    get_cloud_platforms,
)

from ..util import (
    display,
)


class TestTestExists(SanityVersionNeutral):
    @property
    def can_ignore(self):  # type: () -> bool
        """True if the test supports ignore entries."""
        return True

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        all_targets = [target for target in targets]
        return all_targets

    @property
    def test(self, args, targets):
        """
        :type args:
        :type targets:
        :type python_version: str
        :rtype: TestResult
        """
        missing_tests = set()

        # Diff missing_tests and all_tests

        if missing_tests:
            return SanityFailure(self.name, messages=missing_tests)

        return SanitySuccess(self.name)
