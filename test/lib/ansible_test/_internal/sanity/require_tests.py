"""Sanity test to check that an integration test exists"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import textwrap
import re
import os

from .. import types as t

from ..sanity import (
    SanitySingleVersion,
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
    walk_units_targets,
    walk_module_targets,
)

from ..cloud import (
    get_cloud_platforms,
)

from ..util import (
    display,
)


class RequireTestsTest(SanitySingleVersion):
    @property
    def can_ignore(self):  # type: () -> bool
        """True if the test supports ignore entries."""
        return True

    @property
    def all_targets(self):  # type: () -> bool
        """True if test targets will not be filtered using includes, excludes, requires or changes. Mutually exclusive with no_targets."""
        return True

    def filter_targets(self, targets):  # type: (t.List[TestTarget]) -> t.List[TestTarget]
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        return [target for target in targets if target.module]

    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        integration_targets = walk_integration_targets()
        unit_targets = walk_units_targets()
        module_targets = walk_module_targets()

        # Get the list of all modules covered by unit and integration tests
        all_unit_modules = set(u.module for u in unit_targets if u.module)
        all_integration_modules = set(i.modules for i in integration_targets if i.modules)

        all_tests = set()
        for m in all_integration_modules:
            all_tests.update(m)
        all_tests.update(all_unit_modules)


        # Get the list of all modules
        all_modules = set()
        for mt in module_targets:
            all_modules.update(mt.modules)

        # Diff missing_tests and all_tests
        missing_tests = all_modules.difference(all_tests)

        errors = []
        for missing in missing_tests:
            errors.append(SanityMessage(
                path=missing,
                message='missing unit or integration test',
            ))

        if missing_tests:
            return SanityFailure(self.name, messages=errors)

        return SanitySuccess(self.name)
