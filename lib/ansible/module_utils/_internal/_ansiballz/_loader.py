# Copyright (c) 2024 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Support code for exclusive use by the AnsiballZ wrapper."""

from __future__ import annotations

import importlib
import json
import sys
import typing as t

from ansible.module_utils import basic
from ansible.module_utils._internal import _ansiballz, _errors, _traceback, _messages
from ansible.module_utils.common.json import get_module_encoder, Direction


def setup_module_environment(
    *,
    json_params: bytes,
    profile: str,
    extensions: dict[str, dict[str, object]],
) -> None:
    """Set up the module execution environment.

    This is called by __main__.py in the ansiballz zip to initialize the
    environment before module execution. It handles extension initialization
    and sets up module argument access.
    """
    for extension, args in extensions.items():
        extension_module = importlib.import_module(f'{_ansiballz.__name__}._extensions.{extension}')
        extension_module.run(args)

    basic._ANSIBLE_ARGS = json_params
    basic._ANSIBLE_PROFILE = profile


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
