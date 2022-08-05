"""Sanity test for the sanity ignore file."""
from __future__ import annotations

import os

from . import (
    SanityFailure,
    SanityIgnoreParser,
    SanityVersionNeutral,
    SanitySuccess,
    SanityMessage,
    SanityTargets,
)

from ...test import (
    calculate_confidence,
    calculate_best_confidence,
    TestResult,
)

from ...config import (
    SanityConfig,
)


class IgnoresTest(SanityVersionNeutral):
    """Sanity test for sanity test ignore entries."""
    @property
    def can_ignore(self) -> bool:
        """True if the test supports ignore entries."""
        return False

    @property
    def no_targets(self) -> bool:
        """True if the test does not use test targets. Mutually exclusive with all_targets."""
        return True

    def test(self, args: SanityConfig, targets: SanityTargets) -> TestResult:
        sanity_ignore = SanityIgnoreParser.load(args)

        messages: list[SanityMessage] = []

        # parse errors

        messages.extend(SanityMessage(
            message=message,
            path=sanity_ignore.relative_path,
            line=line,
            column=column,
            confidence=calculate_confidence(sanity_ignore.path, line, args.metadata) if args.metadata.changes else None,
        ) for line, column, message in sanity_ignore.parse_errors)

        # file not found errors

        messages.extend(SanityMessage(
            message="%s '%s' does not exist" % ("Directory" if path.endswith(os.path.sep) else "File", path),
            path=sanity_ignore.relative_path,
            line=line,
            column=1,
            confidence=calculate_best_confidence(((sanity_ignore.path, line), (path, 0)), args.metadata) if args.metadata.changes else None,
        ) for line, path in sanity_ignore.file_not_found_errors)

        # conflicting ignores and skips

        for test_name, ignores in sanity_ignore.ignores.items():
            for ignore_path, ignore_entry in ignores.items():
                skip_line_no = sanity_ignore.skips.get(test_name, {}).get(ignore_path)

                if not skip_line_no:
                    continue

                for ignore_line_no in ignore_entry.values():
                    messages.append(SanityMessage(
                        message="Ignoring '%s' is unnecessary due to skip entry on line %d" % (ignore_path, skip_line_no),
                        path=sanity_ignore.relative_path,
                        line=ignore_line_no,
                        column=1,
                        confidence=calculate_confidence(sanity_ignore.path, ignore_line_no, args.metadata) if args.metadata.changes else None,
                    ))

        if messages:
            return SanityFailure(self.name, messages=messages)

        return SanitySuccess(self.name)
