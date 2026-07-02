# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Support code for exclusive use by the AnsiballZ wrapper."""

from __future__ import annotations

import importlib
import json
import runpy
import sys
import typing as t

from ansible.module_utils import basic
from ansible.module_utils._internal import _errors, _traceback, _messages, _ansiballz
from ansible.module_utils.common.json import get_module_encoder, Direction


def run_module(
    *,
    json_params: bytes,
    profile: str,
    module_fqn: str,
    modlib_path: str,
    extensions: dict[str, dict[str, object]],
    init_globals: dict[str, t.Any] | None = None,
) -> None:  # pragma: nocover
    """Used internally by the AnsiballZ wrapper to run an Ansible module."""
    try:
        for extension, args in extensions.items():
            # importing _ansiballz instead of _extensions avoids an unnecessary import when extensions are not in use
            extension_module = importlib.import_module(f'{_ansiballz.__name__}._extensions.{extension}')
            extension_module.run(args)

        _run_module(
            json_params=json_params,
            profile=profile,
            module_fqn=module_fqn,
            modlib_path=modlib_path,
            init_globals=init_globals,
        )
    except Exception as ex:  # not BaseException, since modules are expected to raise SystemExit
        _handle_exception(ex, profile)


def _run_module(
    *,
    json_params: bytes,
    profile: str,
    module_fqn: str,
    modlib_path: str,
    init_globals: dict[str, t.Any] | None = None,
) -> None:
    """Used internally by `_run_module` to run an Ansible module after coverage has been enabled (if applicable)."""
    basic._ANSIBLE_ARGS = json_params
    basic._ANSIBLE_PROFILE = profile

    init_globals = init_globals or {}
    init_globals.update(_module_fqn=module_fqn, _modlib_path=modlib_path)

    # Run the module. By importing it as '__main__', it executes as a script.
    runpy.run_module(mod_name=module_fqn, init_globals=init_globals, run_name='__main__', alter_sys=True)

    # An Ansible module must print its own results and exit. If execution reaches this point, that did not happen.
    raise RuntimeError('New-style module did not handle its own exit.')


def _handle_exception(exception: BaseException, profile: str) -> t.NoReturn:
    """Handle the given exception."""
    result = dict(
        failed=True,
        exception=_messages.ErrorSummary(
            event=_errors.EventFactory.from_exception(exception, _traceback.is_traceback_enabled(_traceback.TracebackEvent.ERROR)),
        ),
    )

    encoder = get_module_encoder(profile, Direction.MODULE_TO_CONTROLLER)

    print(json.dumps(result, cls=encoder))  # pylint: disable=ansible-bad-function

    sys.exit(1)  # pylint: disable=ansible-bad-function
