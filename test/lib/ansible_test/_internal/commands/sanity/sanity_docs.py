"""Sanity test for documentation of sanity tests."""
from __future__ import annotations

import os

from . import (
    SanityVersionNeutral,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanityTargets,
    sanity_get_tests,
)

from ...test import (
    TestResult,
)

from ...config import (
    SanityConfig,
)

from ...data import (
    data_context,
)


class SanityDocsTest(SanityVersionNeutral):
    """Sanity test for documentation of sanity tests."""
    ansible_only = True

    @property
    def can_ignore(self) -> bool:
        """True if the test supports ignore entries."""
        return False

    @property
    def no_targets(self) -> bool:
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return True

    def test(self, args: SanityConfig, targets: SanityTargets) -> TestResult:
        sanity_dir = 'docs/docsite/rst/dev_guide/testing/sanity'
        sanity_docs = set(part[0] for part in (os.path.splitext(os.path.basename(path)) for path in data_context().content.get_files(sanity_dir))
                          if part[1] == '.rst')
        sanity_tests = set(sanity_test.name for sanity_test in sanity_get_tests())

        missing = sanity_tests - sanity_docs

        results = []

        results += [SanityMessage(
            message='missing docs for ansible-test sanity --test %s' % r,
            path=os.path.join(sanity_dir, '%s.rst' % r),
        ) for r in sorted(missing)]

        if results:
            return SanityFailure(self.name, messages=results)

        return SanitySuccess(self.name)
