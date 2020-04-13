"""Erase code coverage files."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ..util_common import (
    ResultType,
)

from . import (
    CoverageConfig,
)


def command_coverage_erase(args):  # type: (CoverageConfig) -> None
    """Erase code coverage data files collected during test runs."""
    coverage_dir = ResultType.COVERAGE.path

    for name in os.listdir(coverage_dir):
        if not name.startswith('coverage') and '=coverage.' not in name:
            continue

        path = os.path.join(coverage_dir, name)

        if not args.explain:
            os.remove(path)
