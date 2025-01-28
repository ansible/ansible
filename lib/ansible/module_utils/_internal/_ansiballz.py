# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Support code for exclusive use by the AnsiballZ wrapper."""

from __future__ import annotations

import atexit
import importlib.util
import json
import os
import runpy
import sys
import typing as t

from . import _errors
from .. import basic
from ..common.json import AnsibleJSONEncoder


def run_module(*, coverage_config: str | None = None, coverage_output: str | None = None, **kwargs) -> None:  # pragma: nocover
    """Used internally by the AnsiballZ wrapper to run an Ansible module."""
    try:
        _enable_coverage(coverage_config, coverage_output)
        _run_module(**kwargs)
    except Exception as ex:  # not BaseException, since modules are expected to raise SystemExit
        _handle_exception(ex)


def _enable_coverage(coverage_config: str | None, coverage_output: str | None) -> None:  # pragma: nocover
    """Bootstrap `coverage` for the current Ansible module invocation."""
    if not coverage_config:
        return

    if coverage_output:
        # Enable code coverage analysis of the module.
        # This feature is for internal testing and may change without notice.
        python_version_string = '.'.join(str(v) for v in sys.version_info[:2])
        os.environ['COVERAGE_FILE'] = f'{coverage_output}=python-{python_version_string}=coverage'

        import coverage

        cov = coverage.Coverage(config_file=coverage_config)

        def atexit_coverage():
            cov.stop()
            cov.save()

        atexit.register(atexit_coverage)

        cov.start()
    else:
        # Verify coverage is available without importing it.
        # This will detect when a module would fail with coverage enabled with minimal overhead.
        if importlib.util.find_spec('coverage') is None:
            raise RuntimeError('Could not find the `coverage` Python module.')


def _run_module(*, json_params: bytes, profile: str, module_fqn: str, modlib_path: str, init_globals: dict[str, t.Any] | None = None) -> None:
    """Used internally by `_run_module` to run an Ansible module after coverage has been enabled (if applicable)."""
    basic._ANSIBLE_ARGS = json_params
    basic._ANSIBLE_PROFILE = profile

    init_globals = init_globals or {}
    init_globals.update(_module_fqn=module_fqn, _modlib_path=modlib_path)

    # Run the module. By importing it as '__main__', it executes as a script.
    runpy.run_module(mod_name=module_fqn, init_globals=init_globals, run_name='__main__', alter_sys=True)

    # An Ansible module must print its own results and exit. If execution reaches this point, that did not happen.
    raise RuntimeError('New-style module did not handle its own exit.')


def _handle_exception(exception: BaseException) -> t.NoReturn:
    """Handle the given exception."""
    result = dict(
        failed=True,
        exception=_errors.create_error_summary(exception),
    )

    print(json.dumps(result, cls=AnsibleJSONEncoder, preserve_datatags=True))  # pylint: disable=ansible-bad-function

    sys.exit(1)  # pylint: disable=ansible-bad-function
