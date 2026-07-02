"""Erase code coverage files."""

from __future__ import annotations

import os

from ...util_common import (
    ResultType,
)

from ...executor import (
    Delegate,
)

from ...provisioning import (
    prepare_profiles,
)

from . import (
    CoverageConfig,
)


def command_coverage_erase(args: CoverageEraseConfig) -> None:
    """Erase code coverage data files collected during test runs."""
    host_state = prepare_profiles(args)  # coverage erase

    if args.delegate:
        raise Delegate(host_state=host_state)

    coverage_dir = ResultType.COVERAGE.path

    for name in os.listdir(coverage_dir):
        if not name.startswith('coverage') and '=coverage.' not in name:
            continue

        path = os.path.join(coverage_dir, name)

        if not args.explain:
            os.remove(path)


class CoverageEraseConfig(CoverageConfig):
    """Configuration for the coverage erase command."""
