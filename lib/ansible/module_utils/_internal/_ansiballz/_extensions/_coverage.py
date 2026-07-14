from __future__ import annotations

import atexit
import dataclasses
import importlib.util
import os
import sys

import typing as t


@dataclasses.dataclass(frozen=True)
class Options:
    """Code coverage options."""

    config: str
    output: str | None


def run(args: dict[str, t.Any]) -> None:  # pragma: nocover
    """Bootstrap `coverage` for the current Ansible module invocation."""
    options = Options(**args)

    if options.output:
        # Enable code coverage analysis of the module.
        # This feature is for internal testing and may change without notice.
        python_version_string = '.'.join(str(v) for v in sys.version_info[:2])
        os.environ['COVERAGE_FILE'] = f'{options.output}=python-{python_version_string}=coverage'

        import coverage

        cov = coverage.Coverage(config_file=options.config)

        def atexit_coverage() -> None:
            cov.stop()
            cov.save()

        atexit.register(atexit_coverage)

        cov.start()
    else:
        # Verify coverage is available without importing it.
        # This will detect when a module would fail with coverage enabled with minimal overhead.
        if importlib.util.find_spec('coverage') is None:
            raise RuntimeError('Could not find the `coverage` Python module.')
